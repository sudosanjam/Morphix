"""Conversion Execution: runs conversion tasks, monitors progress, validates outputs, and handles cleanup."""

import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from app.core.planner import PlannedJob
from app.core.registry import ENGINE_MAP
from app.core.validation import validate_output_file
from app.core.errors import ConversionFailedError, ValidationError, JobCancelledError
from app.core.metadata import inspect_file


class ConversionResult:
    """Detailed summary of a completed conversion."""

    def __init__(
        self,
        source_path: Path,
        output_path: Path,
        source_format: str,
        target_format: str,
        duration_seconds: float,
        source_size_bytes: int,
        output_size_bytes: int,
        engine_used: str,
        warnings: list
    ):
        self.source_path = source_path
        self.output_path = output_path
        self.source_format = source_format
        self.target_format = target_format
        self.duration_seconds = duration_seconds
        self.source_size_bytes = source_size_bytes
        self.output_size_bytes = output_size_bytes
        self.engine_used = engine_used
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "output_path": str(self.output_path),
            "source_format": self.source_format,
            "target_format": self.target_format,
            "duration_seconds": round(self.duration_seconds, 3),
            "source_size_bytes": self.source_size_bytes,
            "output_size_bytes": self.output_size_bytes,
            "engine": self.engine_used,
            "warnings": self.warnings
        }


def execute_conversion(
    planned_job: PlannedJob,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    is_cancelled_callback: Optional[Callable[[], bool]] = None
) -> ConversionResult:
    """Execute planned conversion, validate output, and clean up on failure."""
    start_time = time.time()
    source_p = planned_job.source_path
    target_p = planned_job.target_path
    engine_name = planned_job.route.engine_name
    engine_cls = ENGINE_MAP.get(engine_name)

    if not engine_cls:
        raise ConversionFailedError(f"Engine class not found for: {engine_name}")

    src_size = source_p.stat().st_size

    def check_cancel():
        if is_cancelled_callback and is_cancelled_callback():
            # Clean up target if created
            if target_p.exists():
                try:
                    target_p.unlink()
                except Exception:
                    pass
            raise JobCancelledError(str(target_p))

    check_cancel()

    def wrapped_progress(pct: int, msg: str):
        check_cancel()
        if progress_callback:
            progress_callback(pct, msg)

    try:
        # Run conversion in engine
        result_path = engine_cls.convert(
            source_path=source_p,
            target_path=target_p,
            target_format=planned_job.target_format,
            settings=planned_job.settings,
            progress_cb=wrapped_progress
        )

        check_cancel()

        # Validate output
        if progress_callback:
            progress_callback(95, "Validating output file...")

        validate_output_file(
            result_path,
            expected_format=planned_job.target_format,
            validation_type=planned_job.route.validation_type
        )

        duration = time.time() - start_time
        out_size = result_path.stat().st_size

        if progress_callback:
            progress_callback(100, "Done")

        return ConversionResult(
            source_path=source_p,
            output_path=result_path,
            source_format=planned_job.source_format,
            target_format=planned_job.target_format,
            duration_seconds=duration,
            source_size_bytes=src_size,
            output_size_bytes=out_size,
            engine_used=engine_name,
            warnings=planned_job.warnings
        )

    except Exception as e:
        # Clean up partial target file on failure to prevent corrupted outputs
        if target_p.exists():
            try:
                target_p.unlink()
            except Exception:
                pass
        raise
