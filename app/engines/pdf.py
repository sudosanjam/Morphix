import io
import zipfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
import pypdf
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

from app.engines.base import EngineCapability
from app.core.errors import ConversionFailedError, ValidationError


class PDFEngine(EngineCapability):
    name = "pdf"
    display_name = "Morphix PDF Engine"

    SUPPORTED_INPUTS = ["pdf", "txt", "md", "png", "jpg", "jpeg"]
    SUPPORTED_OUTPUTS = ["pdf", "txt", "png", "jpg", "jpeg", "webp", "bmp", "tiff"]

    _tls = threading.local()

    @classmethod
    def get_last_output_files(cls) -> List[Path]:
        return getattr(cls._tls, "output_files", [])

    @classmethod
    def _set_last_output_files(cls, files: List[Path]):
        cls._tls.output_files = files

    @classmethod
    def is_available(cls) -> bool:
        try:
            import pypdf
            import reportlab
            return True
        except ImportError:
            return False

    @classmethod
    def get_version(cls) -> Optional[str]:
        versions = []
        try:
            import pypdf
            versions.append(f"pypdf {pypdf.__version__}")
        except Exception:
            pass
        if pdfium is not None:
            try:
                versions.append(f"pypdfium2 {pdfium.__version__}")
            except Exception:
                pass
        return " | ".join(versions) if versions else None

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        return "bundled-python (pypdf, reportlab, pypdfium2)"

    @classmethod
    def inspect_pdf(cls, file_path: Path) -> Dict[str, Any]:
        """Inspect PDF page count, metadata, encryption, etc."""
        try:
            reader = pypdf.PdfReader(str(file_path))
            meta = reader.metadata or {}
            page_count = len(reader.pages)
            info = {
                "page_count": page_count,
                "is_encrypted": reader.is_encrypted,
                "title": str(meta.title) if meta.title else None,
                "author": str(meta.author) if meta.author else None,
                "subject": str(meta.subject) if meta.subject else None,
                "creator": str(meta.creator) if meta.creator else None,
            }
            if page_count > 0:
                first_page = reader.pages[0]
                box = first_page.mediabox
                info["page_width"] = float(box.width)
                info["page_height"] = float(box.height)
            return info
        except Exception:
            return {}

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Execute PDF conversion, page processing, or text rendering."""
        src_ext = source_path.suffix.lower().lstrip(".")
        tgt_fmt = target_format.lower()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_cb:
            progress_cb(10, f"Preparing PDF task from {src_ext} to {tgt_fmt}...")

        try:
            # 1. PDF -> TXT (Text extraction)
            if src_ext == "pdf" and tgt_fmt == "txt":
                cls._set_last_output_files([target_path])
                reader = pypdf.PdfReader(str(source_path))
                total = len(reader.pages)
                extracted_text = []
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    extracted_text.append(f"--- Page {idx + 1} ---\n{text}\n")
                    if progress_cb:
                        progress_cb(int(10 + (idx / total) * 80), f"Extracting page {idx + 1}...")

                with open(target_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(extracted_text))

                if progress_cb:
                    progress_cb(100, "Text extraction complete.")
                return target_path

            # 2. PDF -> PDF (Page operations, metadata editing, rotation, page range)
            elif src_ext == "pdf" and tgt_fmt == "pdf":
                cls._set_last_output_files([target_path])
                reader = pypdf.PdfReader(str(source_path))
                writer = pypdf.PdfWriter()

                # Parse page range
                page_range_str = settings.get("page_range")
                target_pages: List[int] = []
                total_pages = len(reader.pages)

                if page_range_str:
                    # e.g. "1-3, 5"
                    for part in str(page_range_str).split(","):
                        part = part.strip()
                        if "-" in part:
                            s, e = part.split("-", 1)
                            start = max(1, int(s.strip()))
                            end = min(total_pages, int(e.strip()))
                            target_pages.extend(range(start - 1, end))
                        elif part.isdigit():
                            p = int(part)
                            if 1 <= p <= total_pages:
                                target_pages.append(p - 1)
                else:
                    target_pages = list(range(total_pages))

                rotate = int(settings.get("rotate_pages", 0))

                for idx, p_num in enumerate(target_pages):
                    page = reader.pages[p_num]
                    if rotate in (90, 180, 270):
                        page.rotate(rotate)
                    writer.add_page(page)
                    if progress_cb:
                        progress_cb(int(15 + (idx / len(target_pages)) * 70), f"Processing page {p_num + 1}...")

                # Metadata editing
                meta_dict = {}
                if settings.get("title"):
                    meta_dict["/Title"] = settings["title"]
                if settings.get("author"):
                    meta_dict["/Author"] = settings["author"]
                if settings.get("subject"):
                    meta_dict["/Subject"] = settings["subject"]
                if meta_dict:
                    writer.add_metadata(meta_dict)

                with open(target_path, "wb") as f:
                    writer.write(f)

                if progress_cb:
                    progress_cb(100, "PDF processing complete.")
                return target_path

            # 3. PDF -> Images (PNG, JPG, JPEG, WEBP, BMP, TIFF)
            elif src_ext == "pdf" and tgt_fmt in ("png", "jpg", "jpeg", "webp", "bmp", "tiff"):
                norm_fmt = "jpg" if tgt_fmt == "jpeg" else tgt_fmt
                if pdfium is None:
                    raise ConversionFailedError(
                        "pypdfium2 library is required to render PDF pages to images. "
                        "Install it via: pip install pypdfium2"
                    )

                pdf_doc = pdfium.PdfDocument(str(source_path))
                total_pages = len(pdf_doc)
                if total_pages == 0:
                    raise ConversionFailedError("PDF document contains no pages.")

                # Parse page range
                page_range_str = settings.get("page_range")
                target_pages: List[int] = []
                if page_range_str:
                    for part in str(page_range_str).split(","):
                        part = part.strip()
                        if "-" in part:
                            s, e = part.split("-", 1)
                            start = max(1, int(s.strip()))
                            end = min(total_pages, int(e.strip()))
                            target_pages.extend(range(start - 1, end))
                        elif part.isdigit():
                            p = int(part)
                            if 1 <= p <= total_pages:
                                target_pages.append(p - 1)
                else:
                    target_pages = list(range(total_pages))

                if not target_pages:
                    target_pages = list(range(total_pages))

                # Deduplicate and sort pages
                target_pages = sorted(list(dict.fromkeys(target_pages)))

                dpi = int(settings.get("dpi", 150))
                # 72 pt per inch base scale
                scale = max(0.5, min(dpi / 72.0, 6.0))
                rotate = int(settings.get("rotate_pages", 0))
                quality = int(settings.get("quality", 90))

                num_target_pages = len(target_pages)
                parent_dir = target_path.parent
                parent_dir.mkdir(parents=True, exist_ok=True)
                stem = source_path.stem

                generated_files: List[Path] = []

                for idx, page_num in enumerate(target_pages):
                    if progress_cb:
                        pct = int(10 + (idx / num_target_pages) * 75)
                        progress_cb(pct, f"Rendering page {page_num + 1} of {total_pages}...")

                    page = pdf_doc[page_num]
                    pil_img = page.render(scale=scale, rotation=rotate).to_pil()

                    # Handle color format compatibility
                    if norm_fmt in ("jpg", "bmp"):
                        if pil_img.mode in ("RGBA", "LA", "P"):
                            bg = Image.new("RGB", pil_img.size, (255, 255, 255))
                            if pil_img.mode == "RGBA":
                                bg.paste(pil_img, mask=pil_img.split()[-1])
                            else:
                                bg.paste(pil_img.convert("RGB"))
                            pil_img = bg
                        elif pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                    elif norm_fmt == "png":
                        if pil_img.mode not in ("RGB", "RGBA", "L"):
                            pil_img = pil_img.convert("RGBA")

                    if settings.get("grayscale"):
                        pil_img = pil_img.convert("L")

                    # Page output filename
                    if num_target_pages == 1:
                        if target_path.suffix.lower() == f".{norm_fmt}":
                            page_path = target_path
                        else:
                            page_path = parent_dir / f"{stem}.{norm_fmt}"
                    else:
                        page_path = parent_dir / f"{stem}_page_{page_num + 1}.{norm_fmt}"

                    save_kwargs: Dict[str, Any] = {}
                    if norm_fmt in ("jpg", "jpeg"):
                        save_kwargs["quality"] = quality
                        save_kwargs["optimize"] = True
                    elif norm_fmt == "webp":
                        save_kwargs["quality"] = quality
                        if settings.get("lossless"):
                            save_kwargs["lossless"] = True

                    pil_img.save(page_path, **save_kwargs)
                    generated_files.append(page_path)

                cls._set_last_output_files(generated_files)

                # Single page: return that page file
                if num_target_pages == 1:
                    if progress_cb:
                        progress_cb(100, f"Page rendered successfully to {norm_fmt.upper()}.")
                    return generated_files[0]

                # Multiple pages: generate a zip archive containing all pages
                zip_path = parent_dir / f"{stem}_{norm_fmt}_pages.zip"
                with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for f in generated_files:
                        zf.write(f, arcname=f.name)

                if progress_cb:
                    progress_cb(100, f"Successfully converted {num_target_pages} pages to {norm_fmt.upper()}.")

                return zip_path

            # 4. TXT / MD -> PDF (Document rendering)
            elif src_ext in ("txt", "md") and tgt_fmt == "pdf":
                cls._set_last_output_files([target_path])
                content = source_path.read_text(encoding="utf-8", errors="replace")
                doc = SimpleDocTemplate(
                    str(target_path),
                    pagesize=A4,
                    rightMargin=54, leftMargin=54,
                    topMargin=54, bottomMargin=54
                )
                styles = getSampleStyleSheet()
                body_style = styles["Normal"]
                body_style.fontSize = 10
                body_style.leading = 14

                h1_style = ParagraphStyle(
                    "Heading1",
                    parent=styles["Heading1"],
                    fontSize=18,
                    leading=22,
                    spaceAfter=12,
                    textColor=colors.HexColor("#1e293b")
                )

                story = []
                lines = content.splitlines()
                for line in lines:
                    line = line.strip()
                    if not line:
                        story.append(Spacer(1, 8))
                    elif line.startswith("# "):
                        story.append(Paragraph(line[2:], h1_style))
                    elif line.startswith("## "):
                        story.append(Paragraph(line[3:], styles["Heading2"]))
                    else:
                        # Escape special XML chars for ReportLab
                        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(escaped, body_style))

                doc.build(story)
                if progress_cb:
                    progress_cb(100, "PDF rendering complete.")
                return target_path

            # 5. Images -> PDF
            elif src_ext in ("png", "jpg", "jpeg", "webp", "bmp") and tgt_fmt == "pdf":
                cls._set_last_output_files([target_path])
                with Image.open(source_path) as im:
                    if im.mode != "RGB":
                        im = im.convert("RGB")
                    im.save(target_path, "PDF", resolution=100.0)
                if progress_cb:
                    progress_cb(100, "Image converted to PDF.")
                return target_path

            else:
                raise ConversionFailedError(f"PDFEngine does not handle {src_ext} to {tgt_fmt}")

        except Exception as e:
            if isinstance(e, ConversionFailedError):
                raise
            raise ConversionFailedError(f"PDF operation failed: {str(e)}")

    @classmethod
    def merge_pdfs(cls, input_paths: List[Path], output_path: Path, progress_cb=None) -> Path:
        """Merge multiple PDF files into one output PDF."""
        writer = pypdf.PdfWriter()
        total = len(input_paths)
        for idx, p in enumerate(input_paths):
            reader = pypdf.PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)
            if progress_cb:
                progress_cb(int((idx / total) * 90), f"Merged {p.name}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            writer.write(f)

        if progress_cb:
            progress_cb(100, "PDF merge complete.")
        return output_path
