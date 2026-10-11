"""Output file validation and integrity verification."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import pypdf
import yaml
import defusedxml.ElementTree as DefusedET

from app.core.errors import ValidationError
from app.engines.ffmpeg import FFmpegEngine


def validate_output_file(
    output_path: Path,
    expected_format: str,
    validation_type: str = "basic"
) -> bool:
    """Validate that converted output exists, is non-empty, and can be parsed correctly."""
    if not output_path.exists():
        raise ValidationError(
            f"Output file was not created: {output_path.name}",
            details="The conversion engine completed without generating the target file."
        )

    size = output_path.stat().st_size
    if size == 0:
        raise ValidationError(
            f"Output file is empty (0 bytes): {output_path.name}",
            details="The conversion produced a 0-byte file."
        )

    fmt = expected_format.lower().lstrip(".")

    # Deep validation by type
    if validation_type == "image" or fmt in ("png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico"):
        try:
            with Image.open(output_path) as img:
                img.verify()
            # Re-open to check dimensions can be read
            with Image.open(output_path) as img:
                w, h = img.size
                if w <= 0 or h <= 0:
                    raise ValidationError(f"Invalid image dimensions: {w}x{h}")
        except Exception as e:
            raise ValidationError(f"Generated image failed validation: {str(e)}")

    elif validation_type == "audio" or fmt in ("mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "aiff"):
        if FFmpegEngine.is_available():
            info = FFmpegEngine.probe_media(output_path)
            # Duration should be detected and > 0
            dur = info.get("duration_seconds")
            if dur is not None and dur <= 0:
                raise ValidationError("Generated audio file has 0 duration.")

    elif validation_type == "pdf" or fmt == "pdf":
        try:
            reader = pypdf.PdfReader(str(output_path))
            if len(reader.pages) == 0:
                raise ValidationError("Generated PDF contains 0 pages.")
        except Exception as e:
            raise ValidationError(f"Generated PDF failed validation: {str(e)}")

    elif validation_type == "data" or fmt in ("json", "yaml", "yml", "xml"):
        try:
            if fmt == "json":
                with open(output_path, "r", encoding="utf-8") as f:
                    json.load(f)
            elif fmt in ("yaml", "yml"):
                with open(output_path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
            elif fmt == "xml":
                DefusedET.parse(str(output_path))
        except Exception as e:
            raise ValidationError(f"Generated data file failed validation: {str(e)}")

    return True
