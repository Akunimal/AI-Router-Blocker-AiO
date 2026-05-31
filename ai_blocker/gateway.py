# -*- coding: utf-8 -*-
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class GatewayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_OPTIONS(self):
        self._proxy_request("OPTIONS")

    def _proxy_request(self, method):
        target = self.server.target_url.rstrip("/") + self.path
        headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ['host', 'accept-encoding']:
                headers[k] = v

        data = None
        if method in ['POST', 'PUT', 'PATCH']:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                data = self.rfile.read(content_length)

        req = urllib.request.Request(target, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.send_response(response.status)
                for k, v in response.headers.items():
                    if k.lower() not in ['transfer-encoding']:
                        self.send_header(k, v)
                self.end_headers()

                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ['transfer-encoding']:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Gateway Error: {e}".encode())
