# -*- coding: utf-8 -*-
"""
Local API Gateway with HTTPS MITM proxy, configurable DPI rules, DLP
sanitization, and structured audit logging.
"""
import json
import select
import socket
import ssl
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

try:
    from ai_blocker.tls_manager import get_or_generate_leaf_cert
except ImportError:
    get_or_generate_leaf_cert = None  # type: ignore[assignment]

from ai_blocker.dpi_rules import DPIAction, DPIRuleEngine

try:
    from ai_blocker.dlp_engine import DLPAction, DLPEngine, DLPPolicy, DLPPolicyManager
except ImportError:
    DLPEngine = None  # type: ignore[assignment,misc]
    DLPPolicy = None  # type: ignore[assignment,misc]
    DLPPolicyManager = None  # type: ignore[assignment,misc]

try:
    from ai_blocker.audit_log import AuditEntry, AuditLog
except ImportError:
    AuditLog = None  # type: ignore[assignment,misc]
    AuditEntry = None  # type: ignore[assignment,misc]

try:
    from ai_blocker.token_monitor import TokenMonitor
except ImportError:
    TokenMonitor = None  # type: ignore[assignment,misc]

try:
    from ai_blocker.guardrails import PromptGuardrail, ThreatCategory
except ImportError:
    PromptGuardrail = None  # type: ignore[assignment,misc]
    ThreatCategory = None  # type: ignore[assignment,misc]


class GatewayHandler(BaseHTTPRequestHandler):
    """HTTP/HTTPS proxy handler with DPI, DLP, guardrails, and audit logging."""

    # ?=??=? HTTPS CONNECT (MITM DPI) ?=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=?

    def do_CONNECT(self):
        """Intercepts HTTPS CONNECT requests for MITM Deep Packet Inspection."""
        if not get_or_generate_leaf_cert:  # type: ignore[truthy-function]
            self.send_error(501, "TLS Decryption (DPI) not supported. Missing cryptography package.")
            return

        domain, port_str = self.path.split(':')
        port = int(port_str)

        # 1. Generate on-the-fly leaf cert for the domain
        try:
            cert_path = get_or_generate_leaf_cert(domain)
        except Exception as e:
            self.send_error(500, f"Failed to generate certificate: {e}")
            return

        # 2. Accept the CONNECT request
        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self.wfile.flush()

        # 3. Upgrade connection to TLS
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert_path, keyfile=cert_path)

        try:
            client_conn = context.wrap_socket(self.connection, server_side=True)
        except ssl.SSLError:
            return

        # 4. Read the full HTTP request line and headers
        try:
            req_line, headers_raw = self._read_http_request(client_conn)
            if not req_line:
                return

            decoded_line = req_line.decode('utf-8', errors='ignore').strip()
            parts = decoded_line.split(" ")
            if len(parts) < 2:
                return

            method = parts[0]
            path = parts[1]

            # 5. DPI rule evaluation
            dpi_engine = getattr(self.server, 'dpi_engine', None) or DPIRuleEngine()
            action, matched_rule = dpi_engine.evaluate(path, method)

            if action == DPIAction.BLOCK:
                rule_name = matched_rule.name if matched_rule else "unknown"
                err_body = json.dumps({
                    "error": f"Blocked by AI DevSec Gateway DPI ? rule: {rule_name}",
                    "rule": rule_name,
                    "path": path,
                })
                err_body_bytes = err_body.encode('utf-8')
                err_response = (
                    "HTTP/1.1 403 Forbidden\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(err_body_bytes)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode('utf-8') + err_body_bytes
                client_conn.sendall(err_response)
                self._log_audit(domain, path, method, "blocked")
                client_conn.close()
                return

            if action == DPIAction.LOG:
                self._log_audit(domain, path, method, "logged")

            # 6. Read request body if present (for DLP inspection)
            content_length = self._parse_content_length(headers_raw)
            body = b""
            if content_length > 0:
                body = self._recv_exact(client_conn, content_length)

                # DLP scan on outbound body
                body = self._apply_dlp(body, domain, path, method)

                # Guardrails check
                if not self._check_guardrails(body, client_conn, domain, path, method):
                    return

            # 7. Forward to real destination
            remote_conn = socket.create_connection((domain, port), timeout=10)
            remote_context = ssl.create_default_context()
            remote_ssl_conn = remote_context.wrap_socket(remote_conn, server_hostname=domain)

            # Rebuild and forward the request
            if body and content_length > 0:
                # Update Content-Length in case DLP changed the body size
                headers_raw = self._update_content_length(headers_raw, len(body))

            remote_ssl_conn.sendall(req_line + headers_raw + b"\r\n" + body)

            # 8. Bidirectional forward for the response
            self._tunnel(client_conn, remote_ssl_conn)
            self._log_audit(domain, path, method, "allowed")

        except Exception as e:
            print(f"DPI Proxy Error: {e}")
        finally:
            try:
                client_conn.close()
            except Exception:
                pass

    # ?=??=? HTTP proxy methods ??????????????????????????????????????????????????????????????????????????????????????????????????

    def do_GET(self):
        if self.path == "/stats":
            self._handle_stats()
            return
        self._proxy_request("GET")
    def do_POST(self): self._proxy_request("POST")
    def do_PUT(self): self._proxy_request("PUT")
    def do_PATCH(self): self._proxy_request("PATCH")
    def do_DELETE(self): self._proxy_request("DELETE")
    def do_OPTIONS(self): self._proxy_request("OPTIONS")

    def _handle_stats(self):
        """Return token monitor stats as JSON."""
        monitor = self._get_token_monitor()
        if monitor is None:
            body = json.dumps({"error": "TokenMonitor not available"}).encode()
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        stats = monitor.get_hourly_summary()
        breakdown = monitor.get_per_domain_breakdown()
        dlp_metrics = {}
        dlp = self._get_dlp_engine()
        if dlp is not None and hasattr(dlp, 'metrics'):
            dlp_metrics = dlp.metrics.to_dict()
        body = json.dumps({
            "summary": stats,
            "domains": breakdown,
            "dlp_metrics": dlp_metrics,
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy_request(self, method):
        target = getattr(self.server, 'target_url', "http://localhost")
        target = target.rstrip("/") + self.path
        headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ['host', 'accept-encoding']:
                headers[k] = v

        data = None
        if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                data = self.rfile.read(content_length)

                # DLP sanitization on outbound data
                data = self._apply_dlp(data, "", self.path, method)

        # Token monitoring
        tokens_in = 0
        monitor = self._get_token_monitor()
        if monitor:
            if data:
                tokens_in = monitor.estimate_tokens(data)
            if monitor.is_over_limit():
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Token rate limit exceeded (AI DevSec Gateway)",
                }).encode())
                self._log_audit("", self.path, method, "blocked")
                return

        req = urllib.request.Request(target, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.send_response(response.status)
                for k, v in response.headers.items():
                    if k.lower() not in ['transfer-encoding']:
                        self.send_header(k, v)
                self.end_headers()

                response_data = b""
                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break
                    response_data += chunk
                    self.wfile.write(chunk)
                    self.wfile.flush()

                # Record token usage
                monitor = self._get_token_monitor()
                if monitor:
                    tokens_out = monitor.estimate_tokens(response_data)
                    monitor.record(tokens_in, tokens_out, domain="", path=self.path)

                self._log_audit("", self.path, method, "allowed")

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ['transfer-encoding']:
                    self.send_header(k, v)
            self.end_headers()
            error_data = e.read()
            self.wfile.write(error_data)

            # Record token usage for errors too
            monitor = self._get_token_monitor()
            if monitor:
                tokens_out = monitor.estimate_tokens(error_data)
                monitor.record(tokens_in, tokens_out, domain="", path=self.path)

            self._log_audit("", self.path, method, "allowed")
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Gateway Error: {e}".encode())

    # ?=??=? Bidirectional tunnel ?=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=??=?

    def _tunnel(self, client, remote):
        """Creates a bidirectional tunnel between the client and remote server."""
        sockets = [client, remote]
        while True:
            r, w, x = select.select(sockets, [], [], 300)
            if not r:
                break
            for sock in r:
                other = remote if sock is client else client
                try:
                    data = sock.recv(8192)
                    if not data:
                        return
                    other.sendall(data)
                except Exception:
                    return

    # ?=??=? Helper methods ??????????????????????????????????????????????????????????????????????????????????????????????????????????

    def _read_http_request(self, conn):
        """Read the request line and headers from a TLS-wrapped connection."""
        data = b""
        while True:
            char = conn.recv(1)
            if not char:
                return b"", b""
            data += char
            if data.endswith(b"\r\n\r\n"):
                break

        parts = data.split(b"\r\n", 1)
        req_line = parts[0] + b"\r\n"
        headers_raw = parts[1] if len(parts) > 1 else b""
        return req_line, headers_raw

    @staticmethod
    def _parse_content_length(headers_raw: bytes) -> int:
        """Extract Content-Length from raw header bytes."""
        for line in headers_raw.split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                try:
                    return int(line.split(b":", 1)[1].strip())
                except ValueError:
                    pass
        return 0

    @staticmethod
    def _update_content_length(headers_raw: bytes, new_length: int) -> bytes:
        """Replace Content-Length value in raw headers."""
        lines = headers_raw.split(b"\r\n")
        updated = []
        for line in lines:
            if line.lower().startswith(b"content-length:"):
                updated.append(f"Content-Length: {new_length}".encode())
            else:
                updated.append(line)
        return b"\r\n".join(updated)

    @staticmethod
    def _recv_exact(conn, length: int) -> bytes:
        """Receive exactly *length* bytes from *conn*."""
        data = b""
        while len(data) < length:
            chunk = conn.recv(min(8192, length - len(data)))
            if not chunk:
                break
            data += chunk
        return data

    def _apply_dlp(self, data: bytes, domain: str, path: str, method: str) -> bytes:
        """Apply DLP sanitization to request body data."""
        if not getattr(self.server, 'dlp_enabled', True):
            return data
        dlp = self._get_dlp_engine()
        if dlp is None:
            return data
        try:
            policy = self._get_dlp_policy(domain, path)
            if policy.action == DLPAction.PASS_THROUGH:
                if isinstance(dlp, DLPEngine):
                    dlp.metrics.passed_through_count += 1
                return data
            # Circuit breaker: skip scan if circuit is open
            if isinstance(dlp, DLPEngine) and dlp.metrics.should_skip():
                return data
            text = data.decode("utf-8", errors="ignore")
            findings = dlp.scan(text, policy=policy)
            if findings:
                if policy.action == DLPAction.BLOCK:
                    if isinstance(dlp, DLPEngine):
                        dlp.metrics.blocked_count += 1
                    self._log_audit(
                        domain, path, method, "blocked",
                        metadata={"dlp_findings": len(findings), "policy": "block"},
                    )
                    return b""
                redacted = dlp.redact(text, findings)
                self._log_audit(
                    domain, path, method,
                    "log_only" if policy.action == DLPAction.LOG_ONLY else "redacted",
                    metadata={"dlp_findings": len(findings)},
                )
                if policy.action == DLPAction.LOG_ONLY:
                    return data
                if isinstance(dlp, DLPEngine):
                    dlp.metrics.redacted_count += 1
                return redacted.encode("utf-8")
        except Exception:
            pass
        return data

    def _check_guardrails(self, body: bytes, client_conn, domain: str, path: str, method: str) -> bool:
        """Check prompt guardrails. Returns False if the request was blocked."""
        if not getattr(self.server, 'guardrails_enabled', True):
            return True
        guardrail = self._get_guardrail()
        if guardrail is None:
            return True
        try:
            text = body.decode("utf-8", errors="ignore")
            result = guardrail.evaluate(text)
            if result.category != ThreatCategory.SAFE:
                err_body = json.dumps({
                    "error": f"Blocked by AI DevSec Gateway guardrail: {result.category.value}",
                    "risk_score": result.risk_score,
                    "explanation": result.explanation,
                })
                err_body_bytes = err_body.encode('utf-8')
                err_response = (
                    "HTTP/1.1 403 Forbidden\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(err_body_bytes)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode('utf-8') + err_body_bytes
                client_conn.sendall(err_response)
                self._log_audit(domain, path, method, "blocked",
                                metadata={"guardrail": result.category.value})
                client_conn.close()
                return False
        except Exception:
            pass
        return True

    def _log_audit(self, domain: str, path: str, method: str, action: str,
                   metadata: dict | None = None) -> None:
        """Log a request to the audit log if available."""
        audit = self._get_audit_log()
        if audit is None or AuditEntry is None:
            return
        try:
            entry = AuditEntry(
                direction="outbound",
                action=action,
                domain=domain,
                path=path,
                method=method,
                metadata=metadata or {},
            )
            audit.log_entry(entry)
        except Exception:
            pass

    def _get_dlp_engine(self):
        return getattr(self.server, 'dlp_engine', None)

    def _get_dlp_policy(self, domain: str, path: str):
        """Return DLP policy for given domain/path."""
        mgr = getattr(self.server, 'dlp_policy_manager', None)
        if mgr is None:
            return DLPPolicy()
        return mgr.resolve(domain, path)

    def _get_audit_log(self):
        return getattr(self.server, 'audit_log', None)

    def _get_token_monitor(self):
        return getattr(self.server, 'token_monitor', None)

    def _get_guardrail(self):
        return getattr(self.server, 'guardrail', None)

    def _get_dlp_enabled(self):
        return getattr(self.server, 'dlp_enabled', True)

    def _get_guardrails_enabled(self):
        return getattr(self.server, 'guardrails_enabled', True)

