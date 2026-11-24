"""Integration tests for live preview endpoints and bookmark favicons."""

import tempfile
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_favicon_endpoints_for_browser_bookmarks():
    # 1. Root favicon.ico requested by browsers when bookmarking
    res_ico = client.get("/favicon.ico")
    assert res_ico.status_code == 200
    assert "image" in res_ico.headers.get("content-type", "")

    # 2. Apple touch icon for iOS / Safari bookmarks
    res_apple = client.get("/apple-touch-icon.png")
    assert res_apple.status_code == 200
    assert "image/png" in res_apple.headers.get("content-type", "")


def test_preview_render_and_info_for_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pdf_file = tmp_path / "test_doc.pdf"

        # Create a 2-page test PDF
        page1 = Image.new("RGB", (300, 300), (255, 255, 255))
        page2 = Image.new("RGB", (300, 300), (240, 240, 240))
        page1.save(pdf_file, save_all=True, append_images=[page2])

        # 1. Preview info
        info_res = client.get(f"/api/preview/info?path={pdf_file}")
        assert info_res.status_code == 200
        data = info_res.json()
        assert data["format"] == "pdf"
        assert data["total_pages"] == 2
        assert data["supports_dark_mode"] is True

        # 2. Render page 1 (Original)
        render_res = client.get(f"/api/preview/render?path={pdf_file}&page=1")
        assert render_res.status_code == 200
        assert render_res.headers.get("content-type") == "image/jpeg"
        assert render_res.headers.get("x-total-pages") == "2"
        assert render_res.headers.get("x-current-page") == "1"

        # 3. Render page 1 with Dark Mode (Charcoal)
        dark_res = client.get(f"/api/preview/render?path={pdf_file}&page=1&dark_mode=dark")
        assert dark_res.status_code == 200
        assert dark_res.headers.get("content-type") == "image/jpeg"
        # Verify rendered dark image has dark pixels
        import io
        img = Image.open(io.BytesIO(dark_res.content))
        pixel = img.getpixel((10, 10))
        assert max(pixel[:3]) < 50, f"Expected dark pixel, got {pixel}"
