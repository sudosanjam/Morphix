"""Robust file format detection based on magic bytes, content signatures, and extensions."""

import os
import zipfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


class FormatDetectionResult:
    def __init__(
        self,
        format_id: str,
        family: str,
        confidence: float,
        detected_by: str,
        mismatch_warning: Optional[str] = None
    ):
        self.format_id = format_id.lower()
        self.family = family.lower()
        self.confidence = confidence
        self.detected_by = detected_by
        self.mismatch_warning = mismatch_warning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format_id,
            "family": self.family,
            "confidence": self.confidence,
            "detected_by": self.detected_by,
            "mismatch_warning": self.mismatch_warning
        }


# Mapping of formats to general family
FORMAT_FAMILIES = {
    # Images
    "png": "image", "jpg": "image", "jpeg": "image", "webp": "image",
    "gif": "image", "bmp": "image", "tiff": "image", "tif": "image",
    "ico": "image", "svg": "image", "avif": "image", "tga": "image",
    # Audio
    "mp3": "audio", "wav": "audio", "flac": "audio", "aac": "audio",
    "m4a": "audio", "ogg": "audio", "opus": "audio", "wma": "audio",
    "aiff": "audio", "aif": "audio", "alac": "audio", "ac3": "audio",
    # Documents
    "pdf": "document", "docx": "document", "doc": "document", "odt": "document",
    "rtf": "document", "txt": "document", "md": "document", "html": "document",
    "htm": "document", "epub": "ebook",
    # Spreadsheets
    "xlsx": "spreadsheet", "xls": "spreadsheet", "ods": "spreadsheet",
    "csv": "spreadsheet", "tsv": "spreadsheet",
    # Presentations
    "pptx": "presentation", "ppt": "presentation", "odp": "presentation",
    # Structured Data
    "json": "data", "yaml": "data", "yml": "data", "xml": "data",
    # Archives
    "zip": "archive", "tar": "archive", "gz": "archive"
}

EXTENSION_CANONICAL = {
    "jpeg": "jpg",
    "tif": "tiff",
    "htm": "html",
    "yml": "yaml",
    "aif": "aiff",
}


def canonical_format(fmt: str) -> str:
    """Normalize format name to standard canonical lowercase name."""
    fmt = fmt.lower().strip().lstrip(".")
    return EXTENSION_CANONICAL.get(fmt, fmt)


def detect_file_format(file_path: Path | str) -> FormatDetectionResult:
    """Detect format using magic signatures first, falling back to extension."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower().lstrip(".")
    claimed_fmt = canonical_format(ext) if ext else ""

    # Read first 8KB of file for signature analysis
    header = b""
    try:
        with open(path, "rb") as f:
            header = f.read(8192)
    except Exception:
        pass

    sig_fmt: Optional[str] = None
    confidence = 0.5
    method = "extension"

    if header:
        # 1. Images
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            sig_fmt = "png"
            confidence = 1.0
        elif header.startswith(b"\xff\xd8\xff"):
            sig_fmt = "jpg"
            confidence = 1.0
        elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
            sig_fmt = "gif"
            confidence = 1.0
        elif len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            sig_fmt = "webp"
            confidence = 1.0
        elif header.startswith(b"BM"):
            sig_fmt = "bmp"
            confidence = 0.95
        elif header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
            sig_fmt = "tiff"
            confidence = 1.0
        elif header.startswith(b"\x00\x00\x01\x00"):
            sig_fmt = "ico"
            confidence = 0.9

        # 2. Audio
        elif header.startswith(b"fLaC"):
            sig_fmt = "flac"
            confidence = 1.0
        elif len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WAVE":
            sig_fmt = "wav"
            confidence = 1.0
        elif header.startswith(b"OggS"):
            # Could be ogg vorbis or opus
            if b"OpusHead" in header[:64]:
                sig_fmt = "opus"
            else:
                sig_fmt = "ogg"
            confidence = 1.0
        elif header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            sig_fmt = "mp3"
            confidence = 0.95
        elif len(header) >= 12 and header.startswith(b"FORM") and header[8:12] in (b"AIFF", b"AIFC"):
            sig_fmt = "aiff"
            confidence = 1.0
        elif len(header) >= 8 and (header[4:8] == b"ftyp" and any(b in header[8:16] for b in [b"M4A", b"isom", b"mp42"])):
            sig_fmt = "m4a"
            confidence = 0.95

        # 3. Documents
        elif header.startswith(b"%PDF-"):
            sig_fmt = "pdf"
            confidence = 1.0
        elif header.startswith(b"{\\rtf"):
            sig_fmt = "rtf"
            confidence = 1.0

        # 4. ZIP-based containers (Office Open XML, OpenDocument, EPUB, ZIP)
        elif header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06"):
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    namelist = zf.namelist()
                    if "word/document.xml" in namelist:
                        sig_fmt = "docx"
                    elif "xl/workbook.xml" in namelist:
                        sig_fmt = "xlsx"
                    elif "ppt/presentation.xml" in namelist:
                        sig_fmt = "pptx"
                    elif "mimetype" in namelist:
                        mimetype = zf.read("mimetype").decode("ascii", errors="ignore").strip()
                        if "epub" in mimetype:
                            sig_fmt = "epub"
                        elif "opendocument.text" in mimetype:
                            sig_fmt = "odt"
                        elif "opendocument.spreadsheet" in mimetype:
                            sig_fmt = "ods"
                        elif "opendocument.presentation" in mimetype:
                            sig_fmt = "odp"
                        else:
                            sig_fmt = "zip"
                    else:
                        sig_fmt = "zip"
                    confidence = 1.0
            except Exception:
                sig_fmt = "zip"
                confidence = 0.8

        # 5. Text / Markup heuristics
        if not sig_fmt:
            try:
                text_sample = header[:2048].decode("utf-8", errors="ignore").strip()
                if text_sample.startswith("<?xml") or (text_sample.startswith("<") and "</" in text_sample):
                    if "<svg" in text_sample.lower():
                        sig_fmt = "svg"
                    elif "<html" in text_sample.lower() or "<!doctype html" in text_sample.lower():
                        sig_fmt = "html"
                    else:
                        sig_fmt = "xml"
                    confidence = 0.9
                elif (text_sample.startswith("{") and text_sample.endswith("}")) or (text_sample.startswith("[") and text_sample.endswith("]")):
                    sig_fmt = "json"
                    confidence = 0.85
            except Exception:
                pass

    detected_fmt = sig_fmt or claimed_fmt or "bin"
    detected_by = "magic_signature" if sig_fmt else "file_extension"

    # Check for extension mismatch
    mismatch_warning = None
    if sig_fmt and claimed_fmt and sig_fmt != claimed_fmt:
        mismatch_warning = (
            f"File extension '.{ext}' does not match detected format '{sig_fmt}'. "
            f"Processing as '{sig_fmt}'."
        )

    family = FORMAT_FAMILIES.get(detected_fmt, "other")
    return FormatDetectionResult(
        format_id=detected_fmt,
        family=family,
        confidence=confidence,
        detected_by=detected_by,
        mismatch_warning=mismatch_warning
    )
