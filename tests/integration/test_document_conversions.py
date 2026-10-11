"""Integration tests for document, spreadsheet, and data conversions."""

import tempfile
import json
from pathlib import Path
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
