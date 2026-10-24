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


def test_api_pdf_targets_include_images_and_text():
    res = client.get("/api/capabilities/targets?source_format=pdf")
    assert res.status_code == 200
    data = res.json()
    targets = [t["format"] for t in data["targets"]]
    # Text extraction retained
    assert "txt" in targets
    # Image conversion supported
    assert "png" in targets
    assert "jpg" in targets
    assert "webp" in targets


def test_api_job_files_endpoint():
    # 1. Create in-memory PNG
    buf = io.BytesIO()
    img = Image.new("RGB", (32, 32), (255, 0, 0))
    img.save(buf, "PNG")
    buf.seek(0)

    # 2. Upload
    upload_res = client.post(
        "/api/upload",
        files={"file": ("test_file_listing.png", buf, "image/png")}
    )
    uploaded_path = upload_res.json()["path"]

    # 3. Convert
    convert_res = client.post(
        "/api/convert",
        json={
            "source_path": uploaded_path,
            "target_format": "jpg",
            "settings": {"quality": 90}
        }
    )
    job_id = convert_res.json()["id"]

    # Wait for completion
    import time
    for _ in range(20):
        time.sleep(0.1)
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] == "completed":
            break

    # 4. Check files endpoint
    files_res = client.get(f"/api/jobs/{job_id}/files")
    assert files_res.status_code == 200
    files_data = files_res.json()
    assert files_data["total_files"] >= 1
    assert "files" in files_data
    first_file = files_data["files"][0]
    assert "download_url" in first_file
    assert "preview_url" in first_file

    # 5. Check specific download and preview
    dl_res = client.get(f"/api/jobs/{job_id}/download/1")
    assert dl_res.status_code == 200
    prev_res = client.get(f"/api/jobs/{job_id}/preview/1")
    assert prev_res.status_code == 200


def test_serve_index_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "Morphix" in res.text
    assert "<!DOCTYPE html>" in res.text
    assert "morphix_retro_logo.png" in res.text


def test_api_image_to_pdf_and_assets():
    # 1. Test retro logo assets are served
    res_logo = client.get("/assets/morphix_retro_logo.png")
    assert res_logo.status_code == 200
    assert len(res_logo.content) > 0

    res_fav = client.get("/assets/favicon.png")
    assert res_fav.status_code == 200

    # 2. Upload image and convert to PDF
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), (100, 200, 50))
    img.save(buf, "PNG")
    buf.seek(0)

    upload_res = client.post(
        "/api/upload",
        files={"file": ("page.png", buf, "image/png")}
    )
    assert upload_res.status_code == 200
    uploaded_path = upload_res.json()["path"]

    convert_res = client.post(
        "/api/convert",
        json={
            "source_path": uploaded_path,
            "target_format": "pdf",
            "settings": {"dpi": 150}
        }
    )
    assert convert_res.status_code == 200
    job_id = convert_res.json()["id"]

    import time
    for _ in range(30):
        time.sleep(0.1)
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] == "completed":
            break

    assert j["status"] == "completed"
    assert j["target_path"].endswith(".pdf")


def test_api_multi_image_to_pdf():
    # Create two in-memory images
    buf1 = io.BytesIO()
    Image.new("RGB", (50, 50), (255, 0, 0)).save(buf1, "PNG")
    buf1.seek(0)

    buf2 = io.BytesIO()
    Image.new("RGB", (50, 50), (0, 0, 255)).save(buf2, "JPEG")
    buf2.seek(0)

    up1 = client.post("/api/upload", files={"file": ("im1.png", buf1, "image/png")}).json()
    up2 = client.post("/api/upload", files={"file": ("im2.jpg", buf2, "image/jpeg")}).json()

    # Call /api/pdf/from-images
    merge_res = client.post(
        "/api/pdf/from-images",
        json={
            "image_paths": [up1["path"], up2["path"]],
            "title": "api_test_combined",
            "settings": {"dpi": 100}
        }
    )
    assert merge_res.status_code == 200
    job_id = merge_res.json()["id"]

    import time
    for _ in range(30):
        time.sleep(0.1)
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] == "completed":
            break

    assert j["status"] == "completed"
    assert j["target_path"].endswith(".pdf")

