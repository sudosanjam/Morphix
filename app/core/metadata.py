"""File inspection and metadata extraction for all supported media and document formats."""

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

from app.core.detector import detect_file_format, canonical_format
from app.engines.ffmpeg import FFmpegEngine
from app.engines.pdf import PDFEngine
from app.engines.spreadsheets import SpreadsheetEngine


def format_bytes(size_bytes: int) -> str:
    """Format bytes into readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def compute_file_hash(file_path: Path, max_bytes: int = 1024 * 1024 * 10) -> str:
    """Compute quick SHA-256 hash of file."""
    sha = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(max_bytes)
            sha.update(chunk)
        return sha.hexdigest()[:16]
    except Exception:
        return ""


def inspect_file(file_path: Path | str) -> Dict[str, Any]:
    """Inspect any file and extract deep format-specific metadata."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    size_bytes = path.stat().st_size
    detection = detect_file_format(path)
    fmt = detection.format_id
    family = detection.family

    result: Dict[str, Any] = {
        "path": str(path),
        "name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": size_bytes,
        "size_formatted": format_bytes(size_bytes),
        "format": fmt,
        "family": family,
        "confidence": detection.confidence,
        "detected_by": detection.detected_by,
        "mismatch_warning": detection.mismatch_warning,
        "hash": compute_file_hash(path),
        "properties": {}
    }

    # 1. Images
    if family == "image":
        try:
            with Image.open(path) as img:
                w, h = img.size
                result["properties"] = {
                    "width": w,
                    "height": h,
                    "aspect_ratio": f"{w}:{h}" if h > 0 else "N/A",
                    "mode": img.mode,
                    "has_alpha": "A" in img.mode or "transparency" in img.info,
                    "format": img.format or fmt.upper(),
                    "animated": getattr(img, "is_animated", False),
                    "n_frames": getattr(img, "n_frames", 1)
                }
        except Exception as e:
            result["properties"]["error"] = f"Could not inspect image: {e}"

    # 2. Audio
    elif family == "audio":
        if FFmpegEngine.is_available():
            try:
                audio_info = FFmpegEngine.probe_media(path)
                result["properties"] = audio_info
            except Exception as e:
                result["properties"]["error"] = f"Could not inspect audio: {e}"
        else:
            result["properties"]["warning"] = "FFmpeg not available for audio stream probing."

    # 3. Documents & PDF
    elif family == "document":
        if fmt == "pdf":
            try:
                result["properties"] = PDFEngine.inspect_pdf(path)
            except Exception as e:
                result["properties"]["error"] = f"Could not inspect PDF: {e}"
        elif fmt in ("txt", "md", "html"):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
                result["properties"] = {
                    "line_count": len(lines),
                    "char_count": len(content),
                    "word_count": len(content.split())
                }
            except Exception:
                pass

    # 4. Spreadsheets
    elif family == "spreadsheet":
        try:
            result["properties"] = SpreadsheetEngine.inspect_spreadsheet(path)
        except Exception as e:
            result["properties"]["error"] = f"Could not inspect spreadsheet: {e}"

    # 5. Structured Data
    elif family == "data":
        try:
            if fmt == "json":
                import json
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    result["properties"] = {
                        "type": type(data).__name__,
                        "item_count": len(data) if isinstance(data, (list, dict)) else 1
                    }
        except Exception:
            pass

    return result
