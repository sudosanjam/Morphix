"""Conversion Planner: plans routes, validates options, computes warnings, and resolves paths."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.core.detector import detect_file_format, canonical_format
from app.core.registry import registry, ConversionRoute, ENGINE_MAP
from app.core.errors import FormatNotSupportedError, EngineNotFoundError, SecurityError
from app.config import config


class PlannedJob:
    """Represents a planned, validated conversion job ready for execution."""

    def __init__(
        self,
        source_path: Path,
        source_format: str,
        target_format: str,
        target_path: Path,
        route: ConversionRoute,
        settings: Dict[str, Any],
        potential_info_loss: str,
        warnings: List[str]
    ):
        self.source_path = source_path
        self.source_format = source_format
        self.target_format = target_format
        self.target_path = target_path
        self.route = route
        self.settings = settings
        self.potential_info_loss = potential_info_loss
        self.warnings = warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "source_format": self.source_format,
            "target_format": self.target_format,
            "target_path": str(self.target_path),
            "engine": self.route.engine_name,
            "lossiness": self.route.lossiness,
            "potential_loss": self.potential_info_loss,
            "warnings": self.warnings,
            "settings": self.settings
        }


def resolve_output_path(
    source_path: Path,
    target_format: str,
    output_destination: Optional[Path | str] = None,
    overwrite_policy: str = "rename"
) -> Path:
    """Determine final output file path respecting overwrite policies and output folder settings."""
    tgt_fmt = canonical_format(target_format)
    stem = source_path.stem

    if output_destination:
        dest_p = Path(output_destination).resolve()
        if dest_p.is_dir() or str(output_destination).endswith(("\\", "/")):
            target_file = dest_p / f"{stem}.{tgt_fmt}"
        else:
            target_file = dest_p
    elif config.settings.default_output_dir:
        dest_p = Path(config.settings.default_output_dir).resolve()
        dest_p.mkdir(parents=True, exist_ok=True)
        target_file = dest_p / f"{stem}.{tgt_fmt}"
    else:
        # Default: alongside source file
        target_file = source_path.parent / f"{stem}.{tgt_fmt}"

    # Prevent accidental overwriting of input file!
    if target_file.resolve() == source_path.resolve():
        target_file = target_file.parent / f"{stem}_converted.{tgt_fmt}"

    # Handle overwrite policy
    if target_file.exists() and overwrite_policy == "rename":
        counter = 1
        new_name = f"{stem}_{counter}.{tgt_fmt}"
        candidate = target_file.parent / new_name
        while candidate.exists():
            counter += 1
            candidate = target_file.parent / f"{stem}_{counter}.{tgt_fmt}"
        target_file = candidate

    return target_file


def plan_conversion(
    source_path: Path | str,
    target_format: str,
    output_destination: Optional[Path | str] = None,
    raw_settings: Optional[Dict[str, Any]] = None,
    overwrite_policy: Optional[str] = None
) -> PlannedJob:
    """Plan, inspect, and validate a conversion before execution."""
    src_p = Path(source_path).resolve()
    if not src_p.exists():
        raise FileNotFoundError(f"Input file not found: {src_p}")

    # 1. Detect actual format
    detection = detect_file_format(src_p)
    src_fmt = detection.format_id
    tgt_fmt = canonical_format(target_format)

    # 2. Prevent dummy same-format extension rename
    if src_fmt == tgt_fmt and not raw_settings:
        pass  # Optimization / reprocessing is permitted if settings provided

    # 3. Find matching capability route
    route = registry.find_route(src_fmt, tgt_fmt)
    if not route:
        # Check if engine exists but format unsupported
        any_route = any(src_fmt in r.source_formats and tgt_fmt in r.target_formats for r in registry.routes)
        if any_route:
            # Route exists in definitions, but engine is not available!
            for r in registry.routes:
                if src_fmt in r.source_formats and tgt_fmt in r.target_formats:
                    raise EngineNotFoundError(r.engine_name)
        raise FormatNotSupportedError(src_fmt, tgt_fmt)

    # 4. Validate and apply format settings against schema
    validated_settings: Dict[str, Any] = {}
    user_settings = raw_settings or {}

    for s_name, s_def in route.settings_schema.items():
        if s_name in user_settings and user_settings[s_name] is not None:
            val = user_settings[s_name]
            # Type casting and bounds checking
            if s_def.type == "int":
                val = int(val)
                if s_def.min_val is not None:
                    val = max(int(s_def.min_val), val)
                if s_def.max_val is not None:
                    val = min(int(s_def.max_val), val)
            elif s_def.type == "float":
                val = float(val)
                if s_def.min_val is not None:
                    val = max(float(s_def.min_val), val)
                if s_def.max_val is not None:
                    val = min(float(s_def.max_val), val)
            elif s_def.type == "bool":
                val = bool(val)
            elif s_def.type == "select" and s_def.options:
                if val not in s_def.options and str(val) not in [str(o) for o in s_def.options]:
                    val = s_def.default
            validated_settings[s_name] = val
        else:
            validated_settings[s_name] = s_def.default

    # 5. Resolve output path
    policy = overwrite_policy or config.settings.overwrite_policy
    target_path = resolve_output_path(src_p, tgt_fmt, output_destination, policy)

    # 6. Gather warnings
    warnings = list(route.warnings)
    if detection.mismatch_warning:
        warnings.append(detection.mismatch_warning)

    return PlannedJob(
        source_path=src_p,
        source_format=src_fmt,
        target_format=tgt_fmt,
        target_path=target_path,
        route=route,
        settings=validated_settings,
        potential_info_loss=route.potential_info_loss,
        warnings=warnings
    )
