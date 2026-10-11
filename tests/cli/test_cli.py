"""Automated tests for the Morphix CLI commands."""

import json
import tempfile
from pathlib import Path
from typer.testing import CliRunner
from PIL import Image

from app.cli.main import app

runner = CliRunner()


def test_cli_version():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "Morphix" in res.stdout
    assert "1.0.0" in res.stdout


def test_cli_doctor_json():
    res = runner.invoke(app, ["doctor", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["app"]["name"] == "Morphix"
    assert "system" in data
    assert "storage" in data
    assert "capabilities" in data


def test_cli_formats():
    res = runner.invoke(app, ["formats", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert "png" in data
    assert "mp3" in data
    assert "pdf" in data


def test_cli_inspect():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        img_p = tmp / "sample.png"
        img = Image.new("RGB", (64, 32), (10, 20, 30))
        img.save(img_p, "PNG")

        res = runner.invoke(app, ["inspect", str(img_p), "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["format"] == "png"
        assert data["properties"]["width"] == 64
        assert data["properties"]["height"] == 32


def test_cli_convert_image():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "icon.png"
        img = Image.new("RGBA", (48, 48), (255, 0, 0, 255))
        img.save(src, "PNG")

        res = runner.invoke(app, ["convert", str(src), "--to", "webp", "--quality", "90", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["status"] == "success"
        assert Path(data["output_path"]).exists()


def test_cli_batch():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_dir = tmp / "src"
        src_dir.mkdir()
        for i in range(3):
            im = Image.new("RGB", (20, 20), (i * 50, 0, 0))
            im.save(src_dir / f"img_{i}.png", "PNG")

        res = runner.invoke(app, ["batch", str(src_dir), "--to", "webp", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["status"] == "completed"
        assert data["total"] == 3
        assert data["success"] == 3


def test_cli_presets():
    res = runner.invoke(app, ["preset", "list", "--json"])
    assert res.exit_code == 0
    p_list = json.loads(res.stdout)
    assert len(p_list) >= 8
