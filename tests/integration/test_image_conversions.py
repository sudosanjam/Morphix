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


def test_png_to_pdf_conversion():
    import pypdf
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "document_page.png"
        img = Image.new("RGBA", (200, 300), (40, 120, 220, 255))
        img.save(src, "PNG")

        planned = plan_conversion(
            source_path=src,
            target_format="pdf",
            raw_settings={"dpi": 150}
        )
        res = execute_conversion(planned)

        assert res.output_path.exists()
        assert res.output_path.suffix.lower() == ".pdf"
        assert validate_output_file(res.output_path, "pdf") is True

        reader = pypdf.PdfReader(str(res.output_path))
        assert len(reader.pages) == 1


def test_webp_and_jpg_to_pdf_conversion():
    import pypdf
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_jpg = tmp / "photo.jpg"
        img_jpg = Image.new("RGB", (150, 150), (200, 50, 80))
        img_jpg.save(src_jpg, "JPEG")

        planned_jpg = plan_conversion(source_path=src_jpg, target_format="pdf")
        res_jpg = execute_conversion(planned_jpg)
        assert res_jpg.output_path.exists()
        assert validate_output_file(res_jpg.output_path, "pdf") is True

        src_webp = tmp / "photo.webp"
        img_webp = Image.new("RGB", (100, 100), (50, 150, 80))
        img_webp.save(src_webp, "WEBP")

        planned_webp = plan_conversion(source_path=src_webp, target_format="pdf")
        res_webp = execute_conversion(planned_webp)
        assert res_webp.output_path.exists()
        assert validate_output_file(res_webp.output_path, "pdf") is True


def test_combine_multiple_images_into_pdf():
    import pypdf
    from app.engines.pdf import PDFEngine

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        p1 = tmp / "page1.png"
        p2 = tmp / "page2.jpg"
        p3 = tmp / "page3.webp"

        Image.new("RGB", (100, 150), (255, 0, 0)).save(p1, "PNG")
        Image.new("RGB", (100, 150), (0, 255, 0)).save(p2, "JPEG")
        Image.new("RGB", (100, 150), (0, 0, 255)).save(p3, "WEBP")

        out_pdf = tmp / "merged_booklet.pdf"
        res = PDFEngine.convert_images_to_pdf(
            image_paths=[p1, p2, p3],
            output_path=out_pdf,
            settings={"dpi": 150}
        )

        assert res.exists()
        assert validate_output_file(res, "pdf") is True
        reader = pypdf.PdfReader(str(res))
        assert len(reader.pages) == 3

