"""Automated tests for FastAPI endpoints."""

import io
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Morphix"


def test_api_capabilities():
    res = client.get("/api/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert "formats" in data
    assert "engines" in data
    assert "routes" in data


def test_api_diagnostics():
    res = client.get("/api/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "system" in data
    assert "capabilities" in data


def test_api_upload_and_convert():
    # 1. Create in-memory PNG
    buf = io.BytesIO()
    img = Image.new("RGB", (32, 32), (0, 255, 128))
    img.save(buf, "PNG")
    buf.seek(0)

    # 2. Upload
    upload_res = client.post(
        "/api/upload",
        files={"file": ("test_upload.png", buf, "image/png")}
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["uploaded"] is True
    uploaded_path = upload_data["path"]

    # 3. Convert
    convert_res = client.post(
        "/api/convert",
        json={
            "source_path": uploaded_path,
            "target_format": "webp",
            "settings": {"quality": 80}
        }
    )
    assert convert_res.status_code == 200
    convert_data = convert_res.json()
    assert "id" in convert_data
    assert convert_data["target_format"] == "webp"


def test_serve_index_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "Morphix" in res.text
    assert "<!DOCTYPE html>" in res.text
