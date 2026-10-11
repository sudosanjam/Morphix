"""Test proving 100% offline operation without external network calls or remote endpoints."""

import socket
import tempfile
from pathlib import Path
from PIL import Image

from app.core.planner import plan_conversion
from app.core.converter import execute_conversion
from app.services.diagnostics import run_diagnostics
from app.main import app
from fastapi.testclient import TestClient


def test_conversion_with_network_disabled(monkeypatch):
    """Ensure that conversions run completely offline and fail if any external network attempt is made."""
    original_connect = socket.socket.connect

    def block_external_network(self, address):
        host, port = address[0], address[1]
        # Allow internal localhost / loopback pipes needed by Python's asyncio on Windows
        if host in ("127.0.0.1", "localhost", "::1"):
            return original_connect(self, address)
        raise RuntimeError(f"External network access attempted to {host}:{port}! Morphix must operate strictly offline.")

    def block_dns(host, port, *args, **kwargs):
        if host in ("127.0.0.1", "localhost", "::1"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
        raise RuntimeError(f"DNS resolution attempted for {host}! Morphix must operate strictly offline.")

    monkeypatch.setattr(socket, "getaddrinfo", block_dns)
    monkeypatch.setattr(socket.socket, "connect", block_external_network)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "offline_test.png"
        img = Image.new("RGBA", (50, 50), (100, 200, 50, 255))
        img.save(src, "PNG")

        # Conversion must succeed entirely without network
        planned = plan_conversion(src, "webp")
        res = execute_conversion(planned)
        assert res.output_path.exists()
        assert res.output_path.stat().st_size > 0

        # Diagnostics must run without network
        diag = run_diagnostics()
        assert diag["app"]["offline_mode"] is True

        # API client must serve index without external requests
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Morphix" in resp.text
