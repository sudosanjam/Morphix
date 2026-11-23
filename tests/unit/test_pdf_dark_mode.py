"""Unit tests for PDF Dark Mode, Reader Mode Palettes, and Conversions."""

import tempfile
from pathlib import Path
from PIL import Image
import pytest

from app.engines.pdf import PDFEngine
from app.core.detector import FORMAT_FAMILIES
from app.core.planner import resolve_output_path


def test_dark_mode_palettes_exist():
    expected = ["dark", "oled", "midnight", "sepia_dark", "sepia_light", "sepia", "amber", "invert"]
    for key in expected:
        assert key in PDFEngine.DARK_MODE_PALETTES, f"Palette '{key}' must be defined"


def test_apply_dark_mode_image_transform():
    # Create a 20x20 image: left half white (background 255), right half black (text 0)
    img = Image.new("RGB", (20, 20), (255, 255, 255))
    for y in range(20):
        for x in range(10, 20):
            img.putpixel((x, y), (0, 0, 0))

    # 1. Dark mode: Charcoal background, dull white text
    dark_img = PDFEngine.apply_dark_mode_to_image(img, "dark")
    bg_pixel = dark_img.getpixel((2, 2))
    fg_pixel = dark_img.getpixel((15, 15))

    # Background should now be very dark (close to 0-30)
    assert max(bg_pixel) < 40, f"Dark mode background should be dark, got {bg_pixel}"
    # Foreground text should now be light/dull white (close to 210-245)
    assert min(fg_pixel) > 200, f"Dark mode text should be bright dull-white, got {fg_pixel}"

    # 2. OLED mode: Pure black background (0, 0, 0)
    oled_img = PDFEngine.apply_dark_mode_to_image(img, "oled")
    oled_bg = oled_img.getpixel((2, 2))
    assert oled_bg == (0, 0, 0), f"OLED background must be pure black (0,0,0), got {oled_bg}"

    # 3. Sepia reader mode: warm background
    sepia_img = PDFEngine.apply_dark_mode_to_image(img, "sepia_light")
    sepia_bg = sepia_img.getpixel((2, 2))
    # Cream paper background has R > G > B
    assert sepia_bg[0] > sepia_bg[2], f"Sepia light should have warm paper tone, got {sepia_bg}"


def test_pdf_dark_mode_format_metadata_and_planning():
    # Verify detector families
    for fmt in ["pdf_dark", "pdf_oled", "pdf_sepia", "pdf_midnight"]:
        assert FORMAT_FAMILIES.get(fmt) == "document"

    # Verify planner resolves dark format aliases to .pdf output with suffix
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "document.pdf"
        src.write_bytes(b"%PDF-1.4 dummy")

        out = resolve_output_path(src, "pdf_dark", overwrite_policy="rename")
        assert out.suffix == ".pdf"
        assert "dark" in out.stem
        assert out != src


def test_full_pdf_to_dark_pdf_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a valid test PDF by saving PIL images as PDF
        page1 = Image.new("RGB", (300, 300), (255, 255, 255))
        # Add black square in center (simulating text)
        for y in range(100, 200):
            for x in range(100, 200):
                page1.putpixel((x, y), (0, 0, 0))

        page2 = Image.new("RGB", (300, 300), (255, 255, 255))
        for y in range(50, 150):
            for x in range(50, 150):
                page2.putpixel((x, y), (20, 20, 20))

        pdf_src = tmp_path / "white_doc.pdf"
        page1.save(pdf_src, save_all=True, append_images=[page2])

        engine = PDFEngine()

        # 1. Convert to PDF with dark_mode setting
        pdf_out_dark = tmp_path / "doc_dark.pdf"
        res = engine.convert(pdf_src, pdf_out_dark, "pdf", {"dark_mode": "dark", "dpi": 100})
        assert res.exists()
        assert pdf_out_dark.exists()
        assert pdf_out_dark.stat().st_size > 500

        # 2. Convert to PDF with OLED alias
        pdf_out_oled = tmp_path / "doc_oled.pdf"
        res_oled = engine.convert(pdf_src, pdf_out_oled, "pdf_oled", {"dpi": 100})
        assert res_oled.exists()
        assert pdf_out_oled.exists()

        # 3. Convert PDF page 1 to Dark Mode PNG image
        png_out = tmp_path / "page_dark.png"
        res_png = engine.convert(pdf_src, png_out, "png", {"dark_mode": "dark", "dpi": 100, "page_range": "1"})
        assert res_png.exists()
        # Check generated dark PNG
        rendered_png = Image.open(res_png)
        corner_pixel = rendered_png.getpixel((5, 5))
        # Background must be dark (< 40)
        assert max(corner_pixel[:3]) < 40, f"Rendered page background should be dark, got {corner_pixel}"
