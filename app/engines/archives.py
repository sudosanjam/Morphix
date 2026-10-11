"""Archive extraction and packaging: ZIP, TAR, GZ."""

import zipfile
import tarfile
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.engines.base import EngineCapability
from app.core.errors import ConversionFailedError


class ArchiveEngine(EngineCapability):
    name = "archives"
    display_name = "Archive Engine (ZIP/TAR/GZ)"

    SUPPORTED_INPUTS = ["zip", "tar", "gz"]
    SUPPORTED_OUTPUTS = ["zip", "tar"]

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def get_version(cls) -> Optional[str]:
        return "python-standard (zipfile & tarfile)"

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        return "bundled-python"

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert archive format (e.g. TAR to ZIP or ZIP to TAR)."""
        src_ext = source_path.suffix.lower().lstrip(".")
        tgt_fmt = target_format.lower()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_cb:
            progress_cb(10, f"Reading archive {source_path.name}...")

        try:
            # Create a temporary extraction directory inside cache
            from app.config import config
            temp_extract = config.temp_dir / f"arch_{source_path.stem}"
            temp_extract.mkdir(parents=True, exist_ok=True)

            if src_ext == "zip":
                with zipfile.ZipFile(source_path, "r") as zf:
                    zf.extractall(temp_extract)
            elif src_ext in ("tar", "gz"):
                mode = "r:gz" if src_ext == "gz" or source_path.name.endswith(".tar.gz") else "r"
                with tarfile.open(source_path, mode) as tf:
                    tf.extractall(temp_extract)

            if progress_cb:
                progress_cb(60, f"Compressing into {tgt_fmt.upper()}...")

            if tgt_fmt == "zip":
                with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for item in temp_extract.rglob("*"):
                        if item.is_file():
                            zf.write(item, item.relative_to(temp_extract))
            elif tgt_fmt == "tar":
                with tarfile.open(target_path, "w") as tf:
                    for item in temp_extract.rglob("*"):
                        if item.is_file():
                            tf.add(item, arcname=str(item.relative_to(temp_extract)))

            # Cleanup temp
            import shutil
            shutil.rmtree(temp_extract, ignore_errors=True)

            if progress_cb:
                progress_cb(100, "Archive conversion complete.")
            return target_path

        except Exception as e:
            raise ConversionFailedError(f"Archive operation failed: {str(e)}")
