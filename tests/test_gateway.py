# -*- coding: utf-8 -*-
"""Tests for the gateway HTTP proxy handler."""
import json
import socket
import ssl
import urllib.error
import urllib.request
from io import BytesIO
from unittest.mock import MagicMock, call, patch

import pytest

from ai_blocker.gateway import GatewayHandler
from ai_blocker.audit_log import AuditEntry, AuditLog
from ai_blocker.token_monitor import TokenMonitor
from ai_blocker.dpi_rules import DPIAction, DPIRule, DPIRuleEngine
from ai_blocker.guardrails import PromptGuardrail, ThreatCategory, GuardrailResult


def _handler():
    h = GatewayHandler.__new__(GatewayHandler)
    h.command = "GET"
    h.path = "/api/test"
    h.requestline = "GET /api/test HTTP/1.1"
    h.request_version = "HTTP/1.1"
    h.headers = {"Host": "example.com", "Accept": "application/json"}
    h.rfile = MagicMock()
    h.wfile = MagicMock()
    h.client_address = ("127.0.0.1", 54321)
    h.server = MagicMock()
    h.server.dpi_engine = MagicMock()
    h.server.token_monitor = None
    h.server.audit_log = None
    h.server.dlp_engine = None
    h.server.guardrail = None
    h.server.dlp_enabled = True
    h.server.guardrails_enabled = True
    h.server.target_url = "http://localhost:8080"
    return h


def _http_mock(status=200, headers=None, body=b"ok"):
    """Create a mock HTTP response that works as a context manager."""
    m = MagicMock()
    m.__enter__.return_value = m
    m.status = status
    m.headers = headers or {}
    m.read.side_effect = [body, b""]
    return m


# ---------------------------------------------------------------------------
# HTTP method dispatch
# ---------------------------------------------------------------------------

class TestGatewayHTTPMethods:
    """Each do_* delegates to _proxy_request with the correct method name."""

    def test_do_get(self, mocker):
        h = _handler()
        m = mocker.patch.object(h, "_proxy_request")
        h.do_GET()
        m.assert_called_once_with("GET")

    def test_do_post(self, mocker):
        h = _handler()
        h.command = "POST"
        m = mocker.patch.object(h, "_proxy_request")
        h.do_POST()
        m.assert_called_once_with("POST")

    def test_do_put(self, mocker):
        h = _handler()
        h.command = "PUT"
        m = mocker.patch.object(h, "_proxy_request")
        h.do_PUT()
        m.assert_called_once_with("PUT")

    def test_do_delete(self, mocker):
        h = _handler()
        h.command = "DELETE"
        m = mocker.patch.object(h, "_proxy_request")
        h.do_DELETE()
        m.assert_called_once_with("DELETE")

    def test_do_patch(self, mocker):
        h = _handler()
        h.command = "PATCH"
        m = mocker.patch.object(h, "_proxy_request")
        h.do_PATCH()
        m.assert_called_once_with("PATCH")

    def test_do_options(self, mocker):
        h = _handler()
        h.command = "OPTIONS"
        m = mocker.patch.object(h, "_proxy_request")
        h.do_OPTIONS()
        m.assert_called_once_with("OPTIONS")


# ---------------------------------------------------------------------------
# _proxy_request - HTTP forwarding logic
# ---------------------------------------------------------------------------

class TestProxyRequest:
    """_proxy_request: forwarding, error handling, token/audit/DLP plumbing."""

    def test_get_success(self):
        h = _handler()
        h.command = "GET"
        resp = _http_mock(200, {"Content-Type": "application/json"}, b'{"status":"ok"}')

        with patch("urllib.request.urlopen", return_value=resp) as m:
            h.do_GET()
            req = m.call_args[0][0]
            assert req.full_url == "http://localhost:8080/api/test"
            assert req.method == "GET"
            assert req.data is None

    def test_post_with_body(self):
        h = _handler()
        h.command = "POST"
        h.headers["Content-Length"] = "11"
        h.rfile.read.return_value = b"hello world"
        resp = _http_mock(200, {}, b"{}")

        with patch("urllib.request.urlopen", return_value=resp):
            h.do_POST()

        h.rfile.read.assert_called_once_with(11)

    def test_post_no_body_when_zero_length(self):
        h = _handler()
        h.command = "POST"
        resp = _http_mock(200, {}, b"{}")

        with patch("urllib.request.urlopen", return_value=resp):
            h.do_POST()

        h.rfile.read.assert_not_called()

    def test_http_error_404(self):
        h = _handler()
        h.command = "GET"
        fp = BytesIO(b'{"error":"not found"}')
        http_error = urllib.error.HTTPError(
            "http://test", 404, "Not Found",
            {"Content-Type": "application/json"}, fp,
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            h.do_GET()

    def test_connection_error_502(self):
        h = _handler()
        h.command = "GET"
        with patch("urllib.request.urlopen", side_effect=Exception("refused")):
            h.do_GET()

    def test_token_limit_exceeded_returns_429(self):
        h = _handler()
        h.command = "GET"
        monitor = MagicMock(spec=TokenMonitor)
        monitor.is_over_limit.return_value = True
        h.server.token_monitor = monitor

        with patch("urllib.request.urlopen") as m:
            h.do_GET()
            m.assert_not_called()

    def test_dlp_applied_to_body(self):
        h = _handler()
        h.command = "POST"
        h.headers["Content-Length"] = "14"
        h.rfile.read.return_value = b"sensitive data"
        dlp = MagicMock()
        dlp.scan.return_value = [MagicMock()]
        dlp.redact.return_value = "REDACTED"
        h.server.dlp_engine = dlp
        resp = _http_mock(200, {}, b"ok")

        with patch("urllib.request.urlopen", return_value=resp):
            h.do_POST()

        dlp.scan.assert_called_once()
        dlp.redact.assert_called_once()

    def test_dlp_disabled_on_proxy_request(self):
        h = _handler()
        h.command = "POST"
        h.headers["Content-Length"] = "14"
        h.rfile.read.return_value = b"sensitive data"
        h.server.dlp_enabled = False
        dlp = MagicMock()
        dlp.scan.return_value = [MagicMock()]
        h.server.dlp_engine = dlp
        resp = _http_mock(200, {}, b"ok")

        with patch("urllib.request.urlopen", return_value=resp):
            h.do_POST()

        dlp.scan.assert_not_called()

    def test_audit_log_created_on_success(self):
        h = _handler()
        h.command = "GET"
        audit = MagicMock(spec=AuditLog)
        h.server.audit_log = audit
        resp = _http_mock(200, {}, b"ok")

        with patch("urllib.request.urlopen", return_value=resp):
            h.do_GET()

        assert audit.log_entry.call_count >= 1

    def test_token_monitor_records_after_response(self):
        h = _handler()
        h.command = "GET"
        monitor = MagicMock(spec=TokenMonitor)
        monitor.is_over_limit.return_value = False
        monitor.estimate_tokens.return_value = 10
        h.server.token_monitor = monitor
        resp = _http_mock(200, {}, b"hello world")

        with patch("urllib.request.urlopen", return_value=resp):
            h.do_GET()

        monitor.record.assert_called_once()
        args = monitor.record.call_args[0]
        assert args[0] == 0

    def test_token_monitor_records_on_http_error(self):
        h = _handler()
        h.command = "GET"
        monitor = MagicMock(spec=TokenMonitor)
        monitor.is_over_limit.return_value = False
        monitor.estimate_tokens.return_value = 10
        h.server.token_monitor = monitor

        fp = BytesIO(b"error body")
        http_error = urllib.error.HTTPError(
            "http://test", 500, "Error",
            {"Content-Type": "text/plain"}, fp,
        )

        with patch("urllib.request.urlopen", side_effect=http_error):
            h.do_GET()

        assert monitor.record.call_count >= 1

    def test_target_url_custom(self):
        h = _handler()
        h.command = "GET"
        h.server.target_url = "https://api.backend"
        resp = _http_mock(200, {}, b"ok")

        with patch("urllib.request.urlopen") as m:
            m.return_value = resp
            h.do_GET()
            assert m.call_args[0][0].full_url.startswith("https://api.backend")

    def test_skips_accept_encoding_header(self):
        h = _handler()
        h.command = "GET"
        h.headers["Accept-Encoding"] = "gzip"
        resp = _http_mock(200, {}, b"ok")

        with patch("urllib.request.urlopen") as m:
            m.return_value = resp
            h.do_GET()
            req = m.call_args[0][0]
            for k in req.headers:
                assert k.lower() != "accept-encoding"


# ---------------------------------------------------------------------------
# Helper / static methods
# ---------------------------------------------------------------------------

class TestHelpers:
    """Gateway static helpers: parse, update, recv, DLP, guardrails, audit."""

    def test_parse_content_length_found(self):
        r = GatewayHandler._parse_content_length(
            b"Content-Length: 42\r\nAccept: */*"
        )
        assert r == 42

    def test_parse_content_length_not_found(self):
        assert GatewayHandler._parse_content_length(b"Host: ex.com") == 0

    def test_parse_content_length_invalid(self):
        assert GatewayHandler._parse_content_length(
            b"Content-Length: xyz\r\n"
        ) == 0

    def test_update_content_length_replaced(self):
        r = GatewayHandler._update_content_length(
            b"Content-Length: 5\r\nHost: ex.com", 99
        )
        assert b"Content-Length: 99" in r
        assert b"Content-Length: 5" not in r

    def test_update_content_length_no_header(self):
        r = GatewayHandler._update_content_length(b"Host: ex.com", 99)
        assert r == b"Host: ex.com"

    def test_recv_exact_normal(self):
        conn = MagicMock()
        conn.recv.side_effect = [b"hel", b"lo"]
        r = GatewayHandler._recv_exact(conn, 5)
        assert r == b"hello"

    def test_recv_exact_early_close(self):
        conn = MagicMock()
        conn.recv.side_effect = [b"hi", b""]
        r = GatewayHandler._recv_exact(conn, 100)
        assert r == b"hi"

    def test_apply_dlp_with_findings(self):
        h = _handler()
        dlp = MagicMock()
        dlp.scan.return_value = [MagicMock()]
        dlp.redact.return_value = "cenzurado"
        h.server.dlp_engine = dlp
        r = h._apply_dlp(b"original", "ex.com", "/", "POST")
        assert r == b"cenzurado"
        dlp.scan.assert_called_once()

    def test_apply_dlp_no_findings(self):
        h = _handler()
        dlp = MagicMock()
        dlp.scan.return_value = []
        h.server.dlp_engine = dlp
        r = h._apply_dlp(b"safe", "ex.com", "/", "GET")
        assert r == b"safe"
        dlp.redact.assert_not_called()

    def test_apply_dlp_no_engine(self):
        h = _handler()
        assert h._apply_dlp(b"data", "", "/", "GET") == b"data"

    def test_check_guardrails_safe(self):
        h = _handler()
        g = MagicMock(spec=PromptGuardrail)
        g.evaluate.return_value = GuardrailResult(ThreatCategory.SAFE, 0.0, [], "")
        h.server.guardrail = g
        assert h._check_guardrails(b"ok", MagicMock(), "ex.com", "/", "POST") is True

    def test_check_guardrails_blocked(self):
        h = _handler()
        g = MagicMock(spec=PromptGuardrail)
        g.evaluate.return_value = GuardrailResult(
            ThreatCategory.JAILBREAK, 0.95, ["pattern"], "bad prompt",
        )
        h.server.guardrail = g
        h.server.audit_log = MagicMock(spec=AuditLog)
        conn = MagicMock()
        assert h._check_guardrails(b"bad", conn, "ex.com", "/", "POST") is False
        conn.sendall.assert_called_once()

    def test_check_guardrails_no_engine(self):
        h = _handler()
        assert h._check_guardrails(b"any", MagicMock(), "", "/", "GET") is True

    def test_log_audit(self):
        h = _handler()
        audit = MagicMock(spec=AuditLog)
        h.server.audit_log = audit
        h._log_audit("ex.com", "/path", "GET", "allowed")
        audit.log_entry.assert_called_once()

    def test_log_audit_with_metadata(self):
        h = _handler()
        audit = MagicMock(spec=AuditLog)
        h.server.audit_log = audit
        h._log_audit("ex.com", "/path", "POST", "redacted", metadata={"dlp_count": 3})
        entry = audit.log_entry.call_args[0][0]
        assert entry.metadata == {"dlp_count": 3}

    def test_log_audit_no_engine(self):
        h = _handler()
        h._log_audit("ex.com", "/path", "GET", "allowed")

    def test_accessors(self):
        h = _handler()
        assert h._get_dlp_engine() is None
        assert h._get_audit_log() is None
        assert h._get_token_monitor() is None
        assert h._get_guardrail() is None
        assert h._get_dlp_enabled() is True
        assert h._get_guardrails_enabled() is True
        dlp = MagicMock()
        h.server.dlp_engine = dlp
        assert h._get_dlp_engine() is dlp

    def test_dlp_disabled_by_flag(self):
        h = _handler()
        h.server.dlp_enabled = False
        h.server.dlp_engine = MagicMock()
        r = h._apply_dlp(b"data", "ex.com", "/", "POST")
        assert r == b"data"
        h.server.dlp_engine.scan.assert_not_called()

    def test_guardrails_disabled_by_flag(self):
        h = _handler()
        h.server.guardrails_enabled = False
        g = MagicMock(spec=PromptGuardrail)
        h.server.guardrail = g
        assert h._check_guardrails(b"bad", MagicMock(), "ex.com", "/", "POST") is True
        g.evaluate.assert_not_called()


# ---------------------------------------------------------------------------
# DO_CONNECT (HTTPS MITM tunnel)
# ---------------------------------------------------------------------------

class TestDO_CONNECT:
    """HTTPS CONNECT with cert generation, DPI, DLP, guardrails."""

    def test_connect_no_tls_module(self):
        """501 when get_or_generate_leaf_cert is None."""
        import ai_blocker.gateway as gw
        orig = gw.get_or_generate_leaf_cert
        gw.get_or_generate_leaf_cert = None
        try:
            h = _handler()
            h.path = "example.com:443"
            h.do_CONNECT()
        finally:
            gw.get_or_generate_leaf_cert = orig

    def test_connect_cert_error(self):
        """500 when cert generation fails."""
        import ai_blocker.gateway as gw
        orig = gw.get_or_generate_leaf_cert
        gw.get_or_generate_leaf_cert = MagicMock(side_effect=Exception("cert fail"))
        try:
            h = _handler()
            h.path = "example.com:443"
            h.do_CONNECT()
        finally:
            gw.get_or_generate_leaf_cert = orig

    def test_connect_dpi_block(self):
        """DPI BLOCK returns 403 before forwarding."""
        import ai_blocker.gateway as gw
        gw.get_or_generate_leaf_cert = MagicMock(return_value="cert.pem")

        mock_ctx = MagicMock()
        mock_client_conn = MagicMock()
        mock_client_conn.recv.return_value = b"x"
        mock_ctx.wrap_socket.return_value = mock_client_conn

        h = _handler()
        h.path = "evil.com:443"
        h.connection = MagicMock()
        h._read_http_request = MagicMock(return_value=(b"GET / HTTP/1.1\r\n", b""))
        h._log_audit = MagicMock()

        dpi = MagicMock(spec=DPIRuleEngine)
        dpi.evaluate.return_value = (
            DPIAction.BLOCK,
            DPIRule("evil-block", DPIAction.BLOCK, ["*evil*"], "GET"),
        )
        h.server.dpi_engine = dpi

        with patch("ai_blocker.gateway.ssl.SSLContext", return_value=mock_ctx):
            h.do_CONNECT()

        dpi.evaluate.assert_called_once()
        mock_client_conn.sendall.assert_called_once()
        h._log_audit.assert_called_with("evil.com", "/", "GET", "blocked")

    def test_connect_log_action(self):
        """DPI LOG records audit but continues to forward."""
        import ai_blocker.gateway as gw
        gw.get_or_generate_leaf_cert = MagicMock(return_value="cert.pem")

        mock_ctx = MagicMock()
        mock_client_conn = MagicMock()
        mock_client_conn.recv.return_value = b"x"
        mock_ctx.wrap_socket.return_value = mock_client_conn

        h = _handler()
        h.path = "example.com:443"
        h.connection = MagicMock()
        h._read_http_request = MagicMock(return_value=(b"GET / HTTP/1.1\r\n", b""))
        h._tunnel = MagicMock()
        h._log_audit = MagicMock()

        dpi = MagicMock(spec=DPIRuleEngine)
        dpi.evaluate.return_value = (DPIAction.LOG, None)
        h.server.dpi_engine = dpi

        with (
            patch("ai_blocker.gateway.ssl.SSLContext", return_value=mock_ctx),
            patch("ai_blocker.gateway.socket.create_connection") as mock_sock,
            patch("ai_blocker.gateway.ssl.create_default_context") as mock_def_ctx,
        ):
            mock_remote = MagicMock()
            mock_sock.return_value = mock_remote
            mock_def_ctx.return_value.wrap_socket.return_value = MagicMock()
            h.do_CONNECT()

        logged_calls = [c for c in h._log_audit.call_args_list if "logged" in c[0]]
        assert len(logged_calls) >= 1

    def test_connect_guardrail_block(self):
        """Guardrail blocks request after body read."""
        import ai_blocker.gateway as gw
        gw.get_or_generate_leaf_cert = MagicMock(return_value="cert.pem")

        mock_ctx = MagicMock()
        mock_client_conn = MagicMock()
        mock_client_conn.recv.return_value = b"x"
        mock_ctx.wrap_socket.return_value = mock_client_conn

        h = _handler()
        h.path = "chat.example.com:443"
        h.connection = MagicMock()
        h._read_http_request = MagicMock(
            return_value=(b"POST /chat HTTP/1.1\r\n", b"Content-Length: 4\r\n"),
        )
        h._log_audit = MagicMock()
        h._tunnel = MagicMock()

        dpi = MagicMock(spec=DPIRuleEngine)
        dpi.evaluate.return_value = (DPIAction.LOG, None)
        h.server.dpi_engine = dpi

        g = MagicMock(spec=PromptGuardrail)
        g.evaluate.return_value = GuardrailResult(
            ThreatCategory.PROMPT_INJECTION, 0.92, ["ignore instructions"], "injection",
        )
        h.server.guardrail = g
        h.server.audit_log = MagicMock(spec=AuditLog)

        with (
            patch("ai_blocker.gateway.ssl.SSLContext", return_value=mock_ctx),
        ):
            h.do_CONNECT()

        g.evaluate.assert_called_once()

    def test_connect_ssl_error_returns_gracefully(self):
        """SSLError during wrap_socket exits without crash."""
        import ai_blocker.gateway as gw
        gw.get_or_generate_leaf_cert = MagicMock(return_value="cert.pem")

        mock_ctx = MagicMock()
        mock_ctx.wrap_socket.side_effect = ssl.SSLError("handshake failed")

        h = _handler()
        h.path = "example.com:443"
        h.connection = MagicMock()

        with patch("ai_blocker.gateway.ssl.SSLContext", return_value=mock_ctx):
            h.do_CONNECT()
