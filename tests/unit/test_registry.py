"""Unit tests for capability registry and route planner."""

import tempfile
from pathlib import Path
from PIL import Image
import pytest

from app.core.registry import registry
from app.core.planner import plan_conversion
from app.core.errors import FormatNotSupportedError


def test_registry_has_routes():
    assert len(registry.routes) > 0
    statuses = registry.get_engine_statuses()
    engine_names = [e["name"] for e in statuses]
    assert "pillow" in engine_names
    assert "ffmpeg" in engine_names
    assert "pdf" in engine_names
    assert "openpyxl" in engine_names


def test_registry_targets_for_png():
    targets = registry.get_available_targets("png")
    target_fmts = [t["format"] for t in targets]
    assert "jpg" in target_fmts
    assert "webp" in target_fmts
    assert "pdf" in target_fmts


def test_registry_targets_for_pdf():
    targets = registry.get_available_targets("pdf")
    target_fmts = [t["format"] for t in targets]
    # Retain txt option
    assert "txt" in target_fmts
    # Support image formats
    assert "png" in target_fmts
    assert "jpg" in target_fmts
    assert "webp" in target_fmts


def test_plan_image_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_png = tmp_path / "photo.png"
        img = Image.new("RGBA", (100, 100), (255, 128, 0, 255))
        img.save(src_png, "PNG")

        planned = plan_conversion(
            source_path=src_png,
            target_format="webp",
            raw_settings={"quality": 90, "width": 50}
        )

        assert planned.target_format == "webp"
        assert planned.route.engine_name == "pillow"
        assert planned.settings["quality"] == 90
        assert planned.settings["width"] == 50
        assert planned.target_path.suffix == ".webp"


def test_plan_unsupported_format_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "file.xyz123"
        src.write_text("dummy")
        with pytest.raises(FormatNotSupportedError):
            plan_conversion(source_path=src, target_format="mp3")
