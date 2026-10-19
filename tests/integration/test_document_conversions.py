"""Integration tests for document, spreadsheet, and data conversions."""

import tempfile
import json
from pathlib import Path
from PIL import Image
import openpyxl
import pypdf

from app.core.planner import plan_conversion
from app.core.converter import execute_conversion
from app.core.validation import validate_output_file


def test_markdown_to_html_and_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_md = tmp / "document.md"
        src_md.write_text("# Morphix Overview\n\nThis is a sample document for conversion.\n\n- Feature 1\n- Feature 2\n")

        # 1. MD -> HTML
        planned_html = plan_conversion(source_path=src_md, target_format="html")
        res_html = execute_conversion(planned_html)
        assert res_html.output_path.exists()
        content = res_html.output_path.read_text(encoding="utf-8")
        assert "Morphix Overview" in content
        assert "Feature 1" in content

        # 2. MD -> PDF
        planned_pdf = plan_conversion(source_path=src_md, target_format="pdf")
        res_pdf = execute_conversion(planned_pdf)
        assert res_pdf.output_path.exists()
        assert validate_output_file(res_pdf.output_path, "pdf") is True


def test_pdf_page_rotation_and_extraction():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Create a sample 2-page PDF
        sample_txt = tmp / "sample.txt"
        sample_txt.write_text("Page 1 content\n\nPage 2 content\n")
        pdf_res = execute_conversion(plan_conversion(sample_txt, "pdf"))
        orig_pdf = pdf_res.output_path

        # Rotate PDF
        planned_rotate = plan_conversion(
            source_path=orig_pdf,
            target_format="pdf",
            raw_settings={"rotate_pages": 90}
        )
        res_rotate = execute_conversion(planned_rotate)
        assert res_rotate.output_path.exists()
        assert validate_output_file(res_rotate.output_path, "pdf") is True


def test_pdf_to_images_multi_page_extraction():
    """Verify that multi-page PDF renders into individual images and ZIP package."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Create a sample 2-page PDF
        orig_pdf = tmp / "document.pdf"
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(orig_pdf))
        c.drawString(100, 750, "Morphix Page 1")
        c.showPage()
        c.drawString(100, 750, "Morphix Page 2")
        c.showPage()
        c.save()

        # 1. Convert PDF -> PNG (All pages)
        planned_png = plan_conversion(
            source_path=orig_pdf,
            target_format="png",
            raw_settings={"dpi": 150}
        )
        res_png = execute_conversion(planned_png)

        # ZIP archive exists for multi-page output
        assert res_png.output_path.exists()
        assert res_png.output_path.suffix == ".zip"

        # Output files list contains each individual page
        assert len(res_png.output_files) == 2
        for idx, page_file in enumerate(res_png.output_files):
            assert page_file.exists()
            assert page_file.suffix == ".png"
            assert f"page_{idx + 1}" in page_file.name
            with Image.open(page_file) as img:
                assert img.width > 0
                assert img.height > 0

        # Validate output passes
        assert validate_output_file(res_png.output_path, "png") is True


def test_pdf_to_jpg_with_page_range():
    """Verify converting a single selected page of PDF to JPG."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        orig_pdf = tmp / "document2.pdf"
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(orig_pdf))
        c.drawString(100, 750, "Page One")
        c.showPage()
        c.drawString(100, 750, "Page Two")
        c.showPage()
        c.save()

        # Convert only page 2
        planned_jpg = plan_conversion(
            source_path=orig_pdf,
            target_format="jpg",
            raw_settings={"page_range": "2", "quality": 92}
        )
        res_jpg = execute_conversion(planned_jpg)

        assert res_jpg.output_path.exists()
        assert res_jpg.output_path.suffix == ".jpg"
        assert len(res_jpg.output_files) == 1
        with Image.open(res_jpg.output_path) as img:
            assert img.format in ("JPEG", "MPO")
            assert img.width > 0
        with Image.open(res_jpg.output_path) as img:
            assert img.format in ("JPEG", "MPO")
            assert img.width > 0


def test_pdf_to_txt_text_extraction():
    """Verify that PDF -> TXT text extraction remains fully functional."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        sample_txt = tmp / "document3.txt"
        sample_txt.write_text("Hello World from Morphix PDF Engine\n")
        pdf_res = execute_conversion(plan_conversion(sample_txt, "pdf"))
        orig_pdf = pdf_res.output_path

        planned_txt = plan_conversion(
            source_path=orig_pdf,
            target_format="txt"
        )
        res_txt = execute_conversion(planned_txt)
        assert res_txt.output_path.exists()
        assert res_txt.output_path.suffix == ".txt"
        content = res_txt.output_path.read_text(encoding="utf-8")
        assert "Hello World" in content


def test_spreadsheet_conversions():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # 1. Create test CSV
        csv_file = tmp / "data.csv"
        csv_file.write_text("name,category,price\nWidget,Tools,19.99\nGadget,Electronics,49.50\n")

        # 2. CSV -> XLSX
        planned_xlsx = plan_conversion(source_path=csv_file, target_format="xlsx")
        res_xlsx = execute_conversion(planned_xlsx)
        assert res_xlsx.output_path.exists()
        wb = openpyxl.load_workbook(res_xlsx.output_path)
        assert "Data" in wb.sheetnames
        wb.close()

        # 3. XLSX -> CSV
        planned_csv = plan_conversion(
            source_path=res_xlsx.output_path,
            target_format="csv",
            raw_settings={"delimiter": "comma"}
        )
        res_csv = execute_conversion(planned_csv)
        assert res_csv.output_path.exists()
        csv_content = res_csv.output_path.read_text()
        assert "Widget" in csv_content


def test_structured_data_conversions():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        json_file = tmp / "data.json"
        sample_dict = {"project": "Morphix", "version": "1.0.0", "offline": True}
        json_file.write_text(json.dumps(sample_dict))

        # JSON -> YAML
        planned_yaml = plan_conversion(source_path=json_file, target_format="yaml")
        res_yaml = execute_conversion(planned_yaml)
        assert res_yaml.output_path.exists()
        assert "Morphix" in res_yaml.output_path.read_text()

        # YAML -> JSON
        planned_back = plan_conversion(source_path=res_yaml.output_path, target_format="json")
        res_back = execute_conversion(planned_back)
        assert res_back.output_path.exists()
        parsed = json.loads(res_back.output_path.read_text())
        assert parsed["project"] == "Morphix"
