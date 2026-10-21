"""Microsoft Word document transformations (DOCX/DOC to PDF, Markdown, HTML, TXT, Images and reverse)."""

import os
import re
import io
import sys
import base64
import shutil
import zipfile
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table as RLTable, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.engines.base import EngineCapability
from app.engines.pdf import PDFEngine
from app.core.errors import ConversionFailedError

# Check for Word COM availability on Windows
_WORD_COM_AVAILABLE = False
if sys.platform == "win32":
    try:
        import win32com.client
        import pythoncom
        # Verify Word.Application can be queried
        _WORD_COM_AVAILABLE = True
    except ImportError:
        _WORD_COM_AVAILABLE = False


_WORD_COM_CACHED: Optional[bool] = None


class WordEngine(EngineCapability):
    """Engine for converting Microsoft Word documents and reverse transformations."""

    name = "word"
    display_name = "Microsoft Word Document Engine"

    SUPPORTED_INPUTS = ["docx", "doc", "md", "txt", "html", "pdf"]
    SUPPORTED_OUTPUTS = ["pdf", "txt", "md", "html", "docx", "png", "jpg", "jpeg", "webp", "bmp", "tiff"]

    _tls = threading.local()

    @classmethod
    def get_last_output_files(cls) -> List[Path]:
        return getattr(cls._tls, "output_files", [])

    @classmethod
    def _set_last_output_files(cls, files: List[Path]):
        cls._tls.output_files = files

    @classmethod
    def is_word_com_available(cls) -> bool:
        global _WORD_COM_CACHED
        if not _WORD_COM_AVAILABLE:
            return False
        if _WORD_COM_CACHED is not None:
            return _WORD_COM_CACHED

        # Check standard Windows paths first to avoid spinning up Word process repeatedly
        candidates = [
            Path("C:/Program Files/Microsoft Office/root/Office16/WINWORD.EXE"),
            Path("C:/Program Files (x86)/Microsoft Office/root/Office16/WINWORD.EXE"),
            Path("C:/Program Files/Microsoft Office/root/Office15/WINWORD.EXE"),
            Path("C:/Program Files (x86)/Microsoft Office/root/Office15/WINWORD.EXE"),
        ]
        if any(c.exists() for c in candidates) or shutil.which("winword"):
            _WORD_COM_CACHED = True
            return True

        # Fallback check via COM
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            try:
                word = win32com.client.Dispatch("Word.Application")
                ver = word.Version
                word.Quit()
                _WORD_COM_CACHED = bool(ver)
                return _WORD_COM_CACHED
            finally:
                pythoncom.CoUninitialize()
        except Exception:
            _WORD_COM_CACHED = False
            return False

    @classmethod
    def is_available(cls) -> bool:
        # python-docx is bundled/installed so docx processing is always available
        return True

    @classmethod
    def get_version(cls) -> Optional[str]:
        docx_ver = f"python-docx {docx.__version__}"
        if sys.platform == "win32" and cls.is_word_com_available():
            return f"{docx_ver} (Native Word COM Engine)"
        return f"{docx_ver} (Pure Python / ReportLab)"

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        if sys.platform == "win32" and cls.is_word_com_available():
            return "Microsoft Word (COM Automation)"
        return "bundled-python (docx)"

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert Word documents or convert other formats into Word documents."""
        src_ext = source_path.suffix.lower().lstrip(".")
        tgt_fmt = target_format.lower().lstrip(".")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        cls._set_last_output_files([target_path])

        if progress_cb:
            progress_cb(10, f"Reading document ({src_ext.upper()})...")

        # 1. DOCX/DOC -> PDF
        if src_ext in ("docx", "doc") and tgt_fmt == "pdf":
            return cls._convert_doc_to_pdf(source_path, target_path, settings, progress_cb)

        # 2. DOCX/DOC -> Plain Text
        elif src_ext in ("docx", "doc") and tgt_fmt == "txt":
            return cls._convert_doc_to_txt(source_path, target_path, settings, progress_cb)

        # 3. DOCX/DOC -> Markdown
        elif src_ext in ("docx", "doc") and tgt_fmt == "md":
            return cls._convert_doc_to_md(source_path, target_path, settings, progress_cb)

        # 4. DOCX/DOC -> HTML
        elif src_ext in ("docx", "doc") and tgt_fmt in ("html", "htm"):
            return cls._convert_doc_to_html(source_path, target_path, settings, progress_cb)

        # 5. DOCX/DOC -> Images (PNG, JPG, WebP, BMP, TIFF) via PDF
        elif src_ext in ("docx", "doc") and tgt_fmt in ("png", "jpg", "jpeg", "webp", "bmp", "tiff"):
            return cls._convert_doc_to_images(source_path, target_path, tgt_fmt, settings, progress_cb)

        # 6. DOC -> DOCX
        elif src_ext == "doc" and tgt_fmt == "docx":
            return cls._convert_legacy_doc_to_docx(source_path, target_path, settings, progress_cb)

        # 7. MD / TXT / HTML / PDF -> DOCX
        elif tgt_fmt == "docx":
            return cls._convert_to_docx(source_path, target_path, src_ext, settings, progress_cb)

        else:
            raise ConversionFailedError(f"Unsupported transformation: {src_ext} to {tgt_fmt}")

    # =========================================================================
    # DOCX -> PDF
    # =========================================================================
    @classmethod
    def _convert_doc_to_pdf(
        cls,
        source_path: Path,
        target_path: Path,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert DOCX/DOC to PDF using pure-Python engine or native Word COM."""
        engine_mode = settings.get("engine_mode", "auto")
        is_legacy_doc = source_path.suffix.lower() == ".doc"

        # Legacy .doc binary format or explicit native_word mode requires Word COM
        if is_legacy_doc or engine_mode == "native_word":
            if sys.platform == "win32" and _WORD_COM_AVAILABLE:
                try:
                    if progress_cb:
                        progress_cb(30, "Rendering document with Microsoft Word...")
                    cls._convert_with_word_com(source_path, target_path, format_code=17)  # 17 = wdFormatPDF
                    if progress_cb:
                        progress_cb(100, "PDF conversion complete.")
                    return target_path
                except Exception as e:
                    if is_legacy_doc:
                        raise ConversionFailedError(f"Failed to convert legacy .doc file via Word: {str(e)}")
                    # For DOCX, seamlessly fall back to pure-Python
            elif is_legacy_doc:
                raise ConversionFailedError("Converting legacy .doc binary files requires Microsoft Word on Windows.")

        # Modern DOCX: fast, deterministic, self-contained pure-Python generation
        if progress_cb:
            progress_cb(40, "Rendering PDF with document engine...")
        cls._convert_docx_to_pdf_pure_python(source_path, target_path, settings, progress_cb)

        if progress_cb:
            progress_cb(100, "PDF conversion complete.")
        return target_path

    @classmethod
    def _convert_with_word_com(cls, source_path: Path, target_path: Path, format_code: int):
        """Execute Word COM automation safely on Windows using an isolated instance."""
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        word = None
        doc = None
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0  # wdAlertsNone

            src_abs = str(source_path.resolve())
            tgt_abs = str(target_path.resolve())

            doc = word.Documents.Open(src_abs, ReadOnly=True, ConfirmConversions=False)
            doc.SaveAs2(tgt_abs, FileFormat=format_code)
        finally:
            if doc:
                try:
                    doc.Close(False)
                except Exception:
                    pass
            if word:
                try:
                    word.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()

    @classmethod
    def _convert_docx_to_pdf_pure_python(
        cls,
        source_path: Path,
        target_path: Path,
        settings: Dict[str, Any],
        progress_cb=None
    ):
        """Pure-Python DOCX -> PDF generation using python-docx and ReportLab."""
        doc_in = docx.Document(source_path)
        doc_out = SimpleDocTemplate(
            str(target_path),
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Define clean, modern typography styles
        body_style = ParagraphStyle(
            'ModernBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=6
        )

        title_style = ParagraphStyle(
            'ModernTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=28,
            textColor=colors.HexColor('#111827'),
            spaceAfter=14
        )

        h1_style = ParagraphStyle(
            'ModernH1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=22,
            textColor=colors.HexColor('#1f2937'),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            'ModernH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=18,
            textColor=colors.HexColor('#374151'),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True
        )

        h3_style = ParagraphStyle(
            'ModernH3',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#4b5563'),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )

        bullet_style = ParagraphStyle(
            'ModernBullet',
            parent=body_style,
            leftIndent=18,
            firstLineIndent=-10,
            spaceAfter=4
        )

        story = []
        total_p = len(doc_in.paragraphs)

        for idx, p in enumerate(doc_in.paragraphs):
            text = p.text.strip()
            if not text:
                continue

            style_name = (p.style.name if p.style else "").lower()

            # Heading styles
            if "title" in style_name:
                p_style = title_style
            elif "heading 1" in style_name:
                p_style = h1_style
            elif "heading 2" in style_name:
                p_style = h2_style
            elif "heading 3" in style_name or "heading 4" in style_name:
                p_style = h3_style
            elif "bullet" in style_name or "list" in style_name:
                p_style = bullet_style
            else:
                p_style = body_style

            # Build formatted text from runs (bold, italic, underline)
            run_parts = []
            for run in p.runs:
                chunk = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if run.bold:
                    chunk = f"<b>{chunk}</b>"
                if run.italic:
                    chunk = f"<i>{chunk}</i>"
                if run.underline:
                    chunk = f"<u>{chunk}</u>"
                run_parts.append(chunk)

            formatted_text = "".join(run_parts) or text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if "bullet" in style_name:
                formatted_text = f"• {formatted_text}"

            story.append(Paragraph(formatted_text, p_style))

            if progress_cb and total_p > 0:
                progress_cb(int(40 + (idx / total_p) * 40), f"Formatting paragraph {idx + 1}/{total_p}...")

        # Process tables
        for table in doc_in.tables:
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    row_data.append(Paragraph(cell_text, body_style))
                table_data.append(row_data)

            if table_data:
                t = RLTable(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(Spacer(1, 10))
                story.append(t)
                story.append(Spacer(1, 10))

        if not story:
            story.append(Paragraph("Empty Document", body_style))

        doc_out.build(story)

    # =========================================================================
    # DOCX -> TXT
    # =========================================================================
    @classmethod
    def _convert_doc_to_txt(
        cls,
        source_path: Path,
        target_path: Path,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Extract clean text from DOCX."""
        doc = docx.Document(source_path)
        lines = []

        for p in doc.paragraphs:
            text = p.text
            if text:
                style_name = (p.style.name if p.style else "").lower()
                if "bullet" in style_name:
                    lines.append(f"  * {text}")
                elif "heading 1" in style_name:
                    lines.append(f"\n# {text}\n")
                elif "heading 2" in style_name:
                    lines.append(f"\n## {text}\n")
                else:
                    lines.append(text)
            else:
                lines.append("")

        if doc.tables:
            lines.append("\n--- TABLES ---")
            for t_idx, table in enumerate(doc.tables):
                lines.append(f"\n[Table {t_idx + 1}]")
                for row in table.rows:
                    row_cells = [c.text.strip() for c in row.cells]
                    lines.append("\t|\t".join(row_cells))

        content = "\n".join(lines)
        target_path.write_text(content, encoding="utf-8")

        if progress_cb:
            progress_cb(100, "Text extracted successfully.")
        return target_path

    # =========================================================================
    # DOCX -> Markdown
    # =========================================================================
    @classmethod
    def _convert_doc_to_md(
        cls,
        source_path: Path,
        target_path: Path,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert DOCX structure, headings, formatted text, and tables to Markdown."""
        doc = docx.Document(source_path)
        md_lines = []

        total = len(doc.paragraphs)
        for idx, p in enumerate(doc.paragraphs):
            text = p.text.strip()
            if not text:
                md_lines.append("")
                continue

            style_name = (p.style.name if p.style else "").lower()

            # Determine prefix
            prefix = ""
            if "title" in style_name:
                prefix = "# "
            elif "heading 1" in style_name:
                prefix = "# "
            elif "heading 2" in style_name:
                prefix = "## "
            elif "heading 3" in style_name:
                prefix = "### "
            elif "heading 4" in style_name:
                prefix = "#### "
            elif "bullet" in style_name:
                prefix = "- "
            elif "list number" in style_name:
                prefix = "1. "

            # Build markdown runs
            runs_text = []
            for run in p.runs:
                chunk = run.text
                if not chunk:
                    continue
                if run.bold and run.italic:
                    chunk = f"***{chunk}***"
                elif run.bold:
                    chunk = f"**{chunk}**"
                elif run.italic:
                    chunk = f"*{chunk}*"
                elif run.font.name and "courier" in run.font.name.lower():
                    chunk = f"`{chunk}`"
                runs_text.append(chunk)

            line_body = "".join(runs_text) if runs_text else text
            md_lines.append(f"{prefix}{line_body}")

            if progress_cb and total > 0:
                progress_cb(int(20 + (idx / total) * 50), f"Converting to Markdown...")

        # Process tables to Markdown tables
        for table in doc.tables:
            if not table.rows:
                continue
            md_lines.append("\n")
            header_cells = [c.text.strip().replace("\n", " ") for c in table.rows[0].cells]
            md_lines.append("| " + " | ".join(header_cells) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")

            for row in table.rows[1:]:
                row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                md_lines.append("| " + " | ".join(row_cells) + " |")
            md_lines.append("\n")

        target_path.write_text("\n".join(md_lines), encoding="utf-8")

        if progress_cb:
            progress_cb(100, "Markdown conversion complete.")
        return target_path

    # =========================================================================
    # DOCX -> HTML
    # =========================================================================
    @classmethod
    def _convert_doc_to_html(
        cls,
        source_path: Path,
        target_path: Path,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert DOCX to clean, self-contained responsive HTML5 with embedded images."""
        doc = docx.Document(source_path)
        body_elements = []

        title = settings.get("title") or source_path.stem

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = (p.style.name if p.style else "").lower()

            # Build formatted inner HTML
            parts = []
            for run in p.runs:
                chunk = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if run.bold:
                    chunk = f"<strong>{chunk}</strong>"
                if run.italic:
                    chunk = f"<em>{chunk}</em>"
                if run.underline:
                    chunk = f"<u>{chunk}</u>"
                parts.append(chunk)

            inner = "".join(parts) or text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if "title" in style_name:
                body_elements.append(f'<h1 class="doc-title">{inner}</h1>')
            elif "heading 1" in style_name:
                body_elements.append(f"<h2>{inner}</h2>")
            elif "heading 2" in style_name:
                body_elements.append(f"<h3>{inner}</h3>")
            elif "heading 3" in style_name:
                body_elements.append(f"<h4>{inner}</h4>")
            elif "bullet" in style_name:
                body_elements.append(f"<ul><li>{inner}</li></ul>")
            else:
                body_elements.append(f"<p>{inner}</p>")

        # Process tables
        for table in doc.tables:
            table_html = ['<table class="doc-table">']
            for r_idx, row in enumerate(table.rows):
                table_html.append("  <tr>")
                tag = "th" if r_idx == 0 else "td"
                for cell in row.cells:
                    escaped = cell.text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    table_html.append(f"    <{tag}>{escaped}</{tag}>")
                table_html.append("  </tr>")
            table_html.append("</table>")
            body_elements.append("\n".join(table_html))

        # Extract embedded images from DOCX package
        try:
            with zipfile.ZipFile(source_path, "r") as zf:
                media_files = [n for n in zf.namelist() if n.startswith("word/media/")]
                if media_files:
                    body_elements.append('<div class="doc-images-section"><h3>Embedded Media</h3><div class="doc-images-grid">')
                    for m in media_files:
                        img_data = zf.read(m)
                        ext = m.split(".")[-1].lower()
                        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                        b64 = base64.b64encode(img_data).decode("ascii")
                        body_elements.append(f'<img src="data:{mime};base64,{b64}" class="doc-img" alt="{m}" />')
                    body_elements.append('</div></div>')
        except Exception:
            pass

        full_html = (
            f"<!DOCTYPE html>\n"
            f"<html lang=\"en\">\n"
            f"<head>\n"
            f"  <meta charset=\"UTF-8\">\n"
            f"  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            f"  <title>{title}</title>\n"
            f"  <style>\n"
            f"    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\n"
            f"           line-height: 1.65; max-width: 860px; margin: 0 auto; padding: 2.5rem 1.5rem; color: #1f2937; background: #fafafa; }}\n"
            f"    h1, h2, h3, h4 {{ color: #111827; font-weight: 700; margin-top: 1.5rem; margin-bottom: 0.5rem; }}\n"
            f"    .doc-title {{ font-size: 2rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.75rem; margin-bottom: 1.5rem; }}\n"
            f"    p {{ margin-bottom: 1rem; }}\n"
            f"    ul, ol {{ margin-bottom: 1rem; padding-left: 1.5rem; }}\n"
            f"    li {{ margin-bottom: 0.25rem; }}\n"
            f"    .doc-table {{ border-collapse: collapse; width: 100%; margin: 1.5rem 0; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-radius: 6px; overflow: hidden; }}\n"
            f"    th, td {{ border: 1px solid #e5e7eb; padding: 10px 14px; text-align: left; font-size: 0.9rem; }}\n"
            f"    th {{ background: #f3f4f6; font-weight: 600; color: #374151; }}\n"
            f"    tr:nth-child(even) {{ background: #f9fafb; }}\n"
            f"    .doc-img {{ max-width: 100%; height: auto; border-radius: 6px; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}\n"
            f"    .doc-images-grid {{ display: flex; flex-wrap: wrap; gap: 1rem; }}\n"
            f"  </style>\n"
            f"</head>\n"
            f"<body>\n"
            f"  <article>\n"
            f"    " + "\n    ".join(body_elements) + "\n"
            f"  </article>\n"
            f"</body>\n"
            f"</html>"
        )

        target_path.write_text(full_html, encoding="utf-8")

        if progress_cb:
            progress_cb(100, "HTML document generated successfully.")
        return target_path

    # =========================================================================
    # DOCX -> Images (PNG, JPG, WebP)
    # =========================================================================
    @classmethod
    def _convert_doc_to_images(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Render DOCX pages to images by converting to intermediate PDF."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_pdf = Path(tmp_dir) / f"{source_path.stem}_intermediate.pdf"
            if progress_cb:
                progress_cb(20, "Rendering document to intermediate vector layout...")
            cls._convert_doc_to_pdf(source_path, tmp_pdf, settings, progress_cb=None)

            if progress_cb:
                progress_cb(60, f"Rasterizing pages to {target_format.upper()} images...")

            # Render pages via PDFEngine
            out_path = PDFEngine.convert(
                source_path=tmp_pdf,
                target_path=target_path,
                target_format=target_format,
                settings=settings,
                progress_cb=progress_cb
            )

            # Pass along the output files (multi-page support)
            cls._set_last_output_files(PDFEngine.get_last_output_files())
            return out_path

    # =========================================================================
    # Legacy DOC -> DOCX
    # =========================================================================
    @classmethod
    def _convert_legacy_doc_to_docx(
        cls,
        source_path: Path,
        target_path: Path,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert legacy .doc to modern .docx via Word COM on Windows."""
        if not (sys.platform == "win32" and _WORD_COM_AVAILABLE):
            raise ConversionFailedError("Converting legacy .doc binary files requires Microsoft Word on Windows.")

        cls._convert_with_word_com(source_path, target_path, format_code=16)  # 16 = wdFormatXMLDocument (docx)
        if progress_cb:
            progress_cb(100, "Converted to DOCX successfully.")
        return target_path

    # =========================================================================
    # Reverse conversions: MD, TXT, HTML, PDF -> DOCX
    # =========================================================================
    @classmethod
    def _convert_to_docx(
        cls,
        source_path: Path,
        target_path: Path,
        source_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Build a formatted DOCX document from Markdown, TXT, HTML, or PDF."""
        doc = docx.Document()
        title = settings.get("title") or source_path.stem
        if settings.get("author"):
            doc.core_properties.author = settings["author"]
        if title:
            doc.core_properties.title = title

        if source_format == "txt":
            content = source_path.read_text(encoding="utf-8", errors="replace")
            for para in content.split("\n\n"):
                p_clean = para.strip()
                if p_clean:
                    doc.add_paragraph(p_clean)

        elif source_format in ("md", "markdown"):
            content = source_path.read_text(encoding="utf-8", errors="replace")
            in_table = False
            table_rows = []

            for line in content.splitlines():
                stripped = line.strip()
                if not stripped:
                    in_table = False
                    continue

                # Markdown table detection
                if stripped.startswith("|") and stripped.endswith("|"):
                    in_table = True
                    cells = [c.strip() for c in stripped.strip("|").split("|")]
                    # Check if separator row
                    if all(set(c).issubset({"-", ":", " "}) for c in cells):
                        continue
                    table_rows.append(cells)
                    continue
                elif in_table:
                    # Flush table
                    if table_rows:
                        num_cols = max(len(r) for r in table_rows)
                        t = doc.add_table(rows=len(table_rows), cols=num_cols)
                        for r_i, r in enumerate(table_rows):
                            for c_i, val in enumerate(r):
                                if c_i < num_cols:
                                    t.cell(r_i, c_i).text = val
                        table_rows = []
                    in_table = False

                # Headings
                if stripped.startswith("# "):
                    doc.add_heading(stripped[2:], level=1)
                elif stripped.startswith("## "):
                    doc.add_heading(stripped[3:], level=2)
                elif stripped.startswith("### "):
                    doc.add_heading(stripped[4:], level=3)
                elif stripped.startswith("#### "):
                    doc.add_heading(stripped[5:], level=4)
                elif stripped.startswith(("- ", "* ")):
                    doc.add_paragraph(stripped[2:], style='List Bullet')
                elif re.match(r"^\d+\.\s+", stripped):
                    item_text = re.sub(r"^\d+\.\s+", "", stripped)
                    doc.add_paragraph(item_text, style='List Number')
                else:
                    # Add paragraph with bold/italic runs
                    p = doc.add_paragraph()
                    # Simple regex matching for bold and italic
                    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', stripped)
                    for pt in parts:
                        if pt.startswith("**") and pt.endswith("**"):
                            p.add_run(pt[2:-2]).bold = True
                        elif pt.startswith("*") and pt.endswith("*"):
                            p.add_run(pt[1:-1]).italic = True
                        else:
                            p.add_run(pt)

            if table_rows:
                num_cols = max(len(r) for r in table_rows)
                t = doc.add_table(rows=len(table_rows), cols=num_cols)
                for r_i, r in enumerate(table_rows):
                    for c_i, val in enumerate(r):
                        if c_i < num_cols:
                            t.cell(r_i, c_i).text = val

        elif source_format in ("html", "htm"):
            from html.parser import HTMLParser

            class SimpleHTMLToDocx(HTMLParser):
                def __init__(self, doc):
                    super().__init__()
                    self.doc = doc
                    self.current_tag = None
                    self.current_para = None

                def handle_starttag(self, tag, attrs):
                    self.current_tag = tag
                    if tag in ("h1", "h2", "h3", "h4"):
                        level = int(tag[1])
                        self.current_para = self.doc.add_heading(level=level)
                    elif tag == "p":
                        self.current_para = self.doc.add_paragraph()
                    elif tag == "li":
                        self.current_para = self.doc.add_paragraph(style='List Bullet')

                def handle_data(self, data):
                    text = data.strip()
                    if text and self.current_para:
                        self.current_para.add_run(text)

            content = source_path.read_text(encoding="utf-8", errors="replace")
            parser = SimpleHTMLToDocx(doc)
            parser.feed(content)

        elif source_format == "pdf":
            import pypdf
            reader = pypdf.PdfReader(str(source_path))
            for i, page in enumerate(reader.pages):
                doc.add_heading(f"Page {i + 1}", level=2)
                txt = page.extract_text() or ""
                for line in txt.split("\n\n"):
                    if line.strip():
                        doc.add_paragraph(line.strip())

        doc.save(target_path)
        if progress_cb:
            progress_cb(100, "DOCX generated successfully.")
        return target_path
