"""Unit tests for presets service and history service."""

import tempfile
from pathlib import Path
from app.services.presets import PresetService
from app.services.history import HistoryService
from app.core.jobs import JobItem, JobState


def test_presets_builtin_and_custom():
    with tempfile.TemporaryDirectory() as tmpdir:
        p_file = Path(tmpdir) / "presets.json"
        service = PresetService(file_path=p_file)

        builtins = service.list_presets()
        assert len(builtins) >= 8

        # Create custom preset
        new_p = service.create_preset(
            name="Test Custom WebP",
            description="Unit test preset",
            category="image",
            target_format="webp",
            settings={"quality": 75}
        )
        assert new_p.id.startswith("custom_")

        # Reload service from disk
        service2 = PresetService(file_path=p_file)
        retrieved = service2.get_preset(new_p.id)
        assert retrieved is not None
        assert retrieved.name == "Test Custom WebP"

        # Delete preset
        assert service2.delete_preset(new_p.id) is True
        assert service2.get_preset(new_p.id) is None


def test_history_logging_and_clearing():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_history.db"
        hist = HistoryService(db_path=db_file)

        job = JobItem(
            id="test_job_1",
            source_path="c:/test/input.png",
            target_format="webp",
            target_path="c:/test/input.webp",
            status=JobState.COMPLETED,
            source_size_bytes=1000,
            output_size_bytes=500,
            duration_seconds=0.12,
            engine="pillow"
        )
        hist.record_job(job)

        records = hist.list_history()
        assert len(records) == 1
        assert records[0]["id"] == "test_job_1"
        assert records[0]["target_format"] == "webp"

        # Clear
        hist.clear_history()
        assert len(hist.list_history()) == 0
