"""Integration tests for real image conversions."""

import tempfile
from pathlib import Path
from PIL import Image

from app.core.planner import plan_conversion
from app.core.converter import execute_conversion
from app.core.validation import validate_output_file


def test_png_to_jpeg_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "sample.png"
        img = Image.new("RGBA", (120, 80), (255, 0, 128, 200))
        img.save(src, "PNG")

        planned = plan_conversion(
            source_path=src,
            target_format="jpg",
            raw_settings={"quality": 85, "flatten_transparency": True}
        )
        res = execute_conversion(planned)

        assert res.output_path.exists()
        assert res.output_path.suffix.lower() in (".jpg", ".jpeg")
        assert validate_output_file(res.output_path, "jpg") is True

        with Image.open(res.output_path) as out_img:
            assert out_img.size == (120, 80)
            assert out_img.mode == "RGB"


def test_png_to_webp_resizing():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "sample.png"
        img = Image.new("RGB", (200, 100), (0, 128, 255))
        img.save(src, "PNG")

        planned = plan_conversion(
            source_path=src,
            target_format="webp",
            raw_settings={"width": 100, "preserve_aspect": True, "quality": 80}
        )
        res = execute_conversion(planned)

        assert res.output_path.exists()
        assert validate_output_file(res.output_path, "webp") is True

        with Image.open(res.output_path) as out_img:
            assert out_img.size == (100, 50)  # aspect ratio maintained (2:1)


def test_image_rotation_and_grayscale():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "rotate_test.png"
        img = Image.new("RGB", (80, 40), (200, 100, 50))
        img.save(src, "PNG")

        planned = plan_conversion(
            source_path=src,
            target_format="png",
            raw_settings={"rotate": 90, "grayscale": True}
        )
        res = execute_conversion(planned)

        with Image.open(res.output_path) as out_img:
            assert out_img.size == (40, 80)  # Rotated 90 degrees
            assert out_img.mode in ("L", "RGB")
