"""Unit tests for file format detector and magic bytes."""

import tempfile
from pathlib import Path
from PIL import Image
import pytest

from app.core.detector import detect_file_format, canonical_format


def test_canonical_format():
    assert canonical_format("JPEG") == "jpg"
    assert canonical_format(".png") == "png"
    assert canonical_format("TIF") == "tiff"
    assert canonical_format("htm") == "html"
    assert canonical_format("yml") == "yaml"


def test_detect_image_signatures():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Real PNG
        png_file = tmp_path / "test.png"
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.save(png_file, "PNG")
        res = detect_file_format(png_file)
        assert res.format_id == "png"
        assert res.family == "image"
        assert res.confidence == 1.0
        assert res.mismatch_warning is None

        # 2. Real JPEG
        jpg_file = tmp_path / "test.jpg"
        img_rgb = Image.new("RGB", (10, 10), (0, 255, 0))
        img_rgb.save(jpg_file, "JPEG")
        res_jpg = detect_file_format(jpg_file)
        assert res_jpg.format_id == "jpg"
        assert res_jpg.family == "image"

        # 3. Extension Mismatch: JPEG saved with .png extension
        mismatch_file = tmp_path / "fake.png"
        img_rgb.save(mismatch_file, "JPEG")
        res_mismatch = detect_file_format(mismatch_file)
        assert res_mismatch.format_id == "jpg"
        assert res_mismatch.mismatch_warning is not None
        assert "does not match detected format 'jpg'" in res_mismatch.mismatch_warning


def test_detect_pdf_signature():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_file = Path(tmpdir) / "sample.pdf"
        pdf_file.write_bytes(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
        res = detect_file_format(pdf_file)
        assert res.format_id == "pdf"
        assert res.family == "document"
        assert res.confidence == 1.0


def test_detect_audio_signatures():
    with tempfile.TemporaryDirectory() as tmpdir:
        wav_file = Path(tmpdir) / "sound.wav"
        # Standard RIFF WAVE header
        wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00"
        wav_file.write_bytes(wav_header)
        res = detect_file_format(wav_file)
        assert res.format_id == "wav"
        assert res.family == "audio"
