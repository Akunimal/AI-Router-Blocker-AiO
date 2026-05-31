"""Tests for the transparent API Gateway proxy handler."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch

import ai_blocker


def test_gateway_handler_proxy_get():
    """GatewayHandler should forward GET requests to the configured target URL."""
    handler = MagicMock(spec=ai_blocker.GatewayHandler)
    handler.path = "/v1/models"
    handler.headers = {"Content-Type": "application/json"}
    handler.server = MagicMock()
    handler.server.target_url = "http://localhost:11434"

    with patch("ai_blocker.gateway.urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.read.return_value = b""
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        ai_blocker.GatewayHandler._proxy_request(handler, "GET")

        # Should have sent a 200 response
        handler.send_response.assert_called_with(200)


def test_gateway_handler_proxy_post_with_body():
    """GatewayHandler should read POST body from content-length header."""
    handler = MagicMock(spec=ai_blocker.GatewayHandler)
    handler.path = "/v1/chat/completions"
    handler.headers = {"Content-Type": "application/json", "Content-Length": "42"}
    handler.server = MagicMock()
    handler.server.target_url = "http://localhost:11434"
    handler.rfile = MagicMock()
    handler.rfile.read.return_value = b'{"model": "llama3", "messages": []}'

    with patch("ai_blocker.gateway.urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.read.return_value = b""
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        ai_blocker.GatewayHandler._proxy_request(handler, "POST")

        handler.rfile.read.assert_called_once_with(42)


def test_gateway_handler_proxies_mutating_methods():
    """GatewayHandler should register mutating HTTP methods used by REST APIs."""
    expected_methods = {
        "do_PUT": "PUT",
        "do_PATCH": "PATCH",
        "do_DELETE": "DELETE",
    }

    for handler_method, proxied_method in expected_methods.items():
        handler = MagicMock(spec=ai_blocker.GatewayHandler)

        getattr(ai_blocker.GatewayHandler, handler_method)(handler)

        handler._proxy_request.assert_called_once_with(proxied_method)


def test_gateway_handler_proxy_delete_with_body():
    """GatewayHandler should preserve DELETE bodies when clients send one."""
    handler = MagicMock(spec=ai_blocker.GatewayHandler)
    handler.path = "/v1/resources/123"
    handler.headers = {"Content-Type": "application/json", "Content-Length": "15"}
    handler.server = MagicMock()
    handler.server.target_url = "http://localhost:11434"
    handler.rfile = MagicMock()
    handler.rfile.read.return_value = b'{"force": true}'

    with patch("ai_blocker.gateway.urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.headers = {}
        mock_response.read.return_value = b""
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        ai_blocker.GatewayHandler._proxy_request(handler, "DELETE")

        handler.rfile.read.assert_called_once_with(15)
