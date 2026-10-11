"""Document transformations: Markdown, HTML, TXT, plus Pandoc and LibreOffice adapters."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import markdown
from html.parser import HTMLParser

from app.engines.base import EngineCapability
from app.core.errors import ConversionFailedError, EngineNotFoundError
from app.config import config


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        self.text_parts.append(data)

    def get_text(self) -> str:
        return "".join(self.text_parts)


class DocumentEngine(EngineCapability):
    name = "documents"
    display_name = "Document Engine (Markdown/HTML/TXT)"

    SUPPORTED_INPUTS = ["md", "markdown", "html", "htm", "txt"]
    SUPPORTED_OUTPUTS = ["html", "txt", "md"]

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def get_version(cls) -> Optional[str]:
        return f"markdown {markdown.__version__}"

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        return "bundled-python (markdown)"

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert between Markdown, HTML, and Plain Text."""
        src_ext = source_path.suffix.lower().lstrip(".")
        if src_ext == "markdown":
            src_ext = "md"
        elif src_ext == "htm":
            src_ext = "html"

        tgt_fmt = target_format.lower()
        if tgt_fmt == "htm":
            tgt_fmt = "html"

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_cb:
            progress_cb(10, f"Reading document content ({src_ext})...")

        try:
            content = source_path.read_text(encoding="utf-8", errors="replace")

            if progress_cb:
                progress_cb(50, f"Transforming to {tgt_fmt.upper()}...")

            # 1. MD -> HTML
            if src_ext == "md" and tgt_fmt == "html":
                extensions = ["extra", "codehilite", "tables", "toc"]
                html_body = markdown.markdown(content, extensions=extensions)
                title = settings.get("title") or source_path.stem

                full_html = (
                    f"<!DOCTYPE html>\n"
                    f"<html lang=\"en\">\n"
                    f"<head>\n"
                    f"  <meta charset=\"UTF-8\">\n"
                    f"  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                    f"  <title>{title}</title>\n"
                    f"  <style>\n"
                    f"    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 2rem; color: #333; }}\n"
                    f"    pre {{ background: #f4f4f5; padding: 1rem; border-radius: 6px; overflow-x: auto; }}\n"
                    f"    code {{ font-family: monospace; background: #f4f4f5; padding: 2px 4px; border-radius: 4px; }}\n"
                    f"    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}\n"
                    f"    th, td {{ border: 1px solid #e4e4e7; padding: 8px 12px; text-align: left; }}\n"
                    f"    th {{ background: #f4f4f5; }}\n"
                    f"  </style>\n"
                    f"</head>\n"
                    f"<body>\n{html_body}\n</body>\n</html>"
                )
                target_path.write_text(full_html, encoding="utf-8")

            # 2. HTML -> TXT
            elif src_ext == "html" and tgt_fmt == "txt":
                parser = HTMLTextExtractor()
                parser.feed(content)
                target_path.write_text(parser.get_text(), encoding="utf-8")

            # 3. MD -> TXT (Strip markdown syntax)
            elif src_ext == "md" and tgt_fmt == "txt":
                # Strip basic headers, bold, italics, links
                txt = re.sub(r"#+\s*", "", content)
                txt = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", txt)
                txt = re.sub(r"[\*_]{1,3}([^\*_]+)[\*_]{1,3}", r"\1", txt)
                target_path.write_text(txt, encoding="utf-8")

            # 4. TXT -> MD or TXT -> HTML
            elif src_ext == "txt" and tgt_fmt == "md":
                target_path.write_text(content, encoding="utf-8")

            elif src_ext == "txt" and tgt_fmt == "html":
                escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html = f"<!DOCTYPE html><html><body><pre>{escaped}</pre></body></html>"
                target_path.write_text(html, encoding="utf-8")

            else:
                raise ConversionFailedError(f"Unsupported document transformation: {src_ext} to {tgt_fmt}")

            if progress_cb:
                progress_cb(100, "Document conversion complete.")
            return target_path

        except Exception as e:
            if isinstance(e, ConversionFailedError):
                raise
            raise ConversionFailedError(f"Document conversion failed: {str(e)}")


class PandocEngine(EngineCapability):
    """Pandoc document conversion adapter (optional engine)."""
    name = "pandoc"
    display_name = "Pandoc Document Converter"

    _cached_exe: Optional[str] = None
    _cached_version: Optional[str] = None

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        if cls._cached_exe and os.path.exists(cls._cached_exe):
            return cls._cached_exe
        custom = config.settings.custom_pandoc_path
        if custom and os.path.exists(custom):
            cls._cached_exe = custom
            return custom
        sys_path = shutil.which("pandoc")
        if sys_path:
            cls._cached_exe = sys_path
            return sys_path
        return None

    @classmethod
    def is_available(cls) -> bool:
        return cls.get_binary_path() is not None

    @classmethod
    def get_version(cls) -> Optional[str]:
        if cls._cached_version:
            return cls._cached_version
        exe = cls.get_binary_path()
        if not exe:
            return None
        try:
            res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.splitlines()[0]
            cls._cached_version = first_line
            return first_line
        except Exception:
            return None

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        exe = cls.get_binary_path()
        if not exe:
            raise EngineNotFoundError("Pandoc", "Install Pandoc on your system for advanced office/document conversions.")

        target_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [exe, str(source_path), "-o", str(target_path)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            raise ConversionFailedError(f"Pandoc failed with code {res.returncode}", stderr=res.stderr)
        return target_path


class LibreOfficeEngine(EngineCapability):
    """LibreOffice headless office document converter (optional engine)."""
    name = "libreoffice"
    display_name = "LibreOffice Office Suite"

    _cached_exe: Optional[str] = None
    _cached_version: Optional[str] = None

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        if cls._cached_exe and os.path.exists(cls._cached_exe):
            return cls._cached_exe
        custom = config.settings.custom_libreoffice_path
        if custom and os.path.exists(custom):
            cls._cached_exe = custom
            return custom
        for candidate in ["soffice", "libreoffice"]:
            sys_path = shutil.which(candidate)
            if sys_path:
                cls._cached_exe = sys_path
                return sys_path
        # Check standard Windows installation directory
        if os.name == "nt":
            win_lo = Path("C:/Program Files/LibreOffice/program/soffice.exe")
            if win_lo.exists():
                cls._cached_exe = str(win_lo)
                return str(win_lo)
        return None

    @classmethod
    def is_available(cls) -> bool:
        return cls.get_binary_path() is not None

    @classmethod
    def get_version(cls) -> Optional[str]:
        if cls._cached_version:
            return cls._cached_version
        exe = cls.get_binary_path()
        if not exe:
            return None
        try:
            res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.splitlines()[0]
            cls._cached_version = first_line
            return first_line
        except Exception:
            return None

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        exe = cls.get_binary_path()
        if not exe:
            raise EngineNotFoundError("LibreOffice", "Install LibreOffice for DOCX, PPTX, and ODT conversions.")

        out_dir = target_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            exe, "--headless", "--convert-to", target_format.lower(),
            "--outdir", str(out_dir), str(source_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode != 0:
            raise ConversionFailedError(f"LibreOffice conversion failed: {res.returncode}", stderr=res.stderr)
        return target_path
