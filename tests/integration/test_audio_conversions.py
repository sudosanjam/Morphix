"""Integration tests for real audio conversions via FFmpeg."""

import wave
import math
import struct
import tempfile
from pathlib import Path
import pytest

from app.engines.ffmpeg import FFmpegEngine
from app.core.planner import plan_conversion
from app.core.converter import execute_conversion
from app.core.validation import validate_output_file


def generate_test_wav(file_path: Path, duration_seconds: float = 1.0, sample_rate: int = 44100):
    """Generate a clean 440Hz sine wave WAV file for testing."""
    n_samples = int(duration_seconds * sample_rate)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            # 440 Hz standard tone
            sample = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            frames.extend(struct.pack("<h", sample))
        wf.writeframes(frames)


@pytest.mark.skipif(not FFmpegEngine.is_available(), reason="FFmpeg not available")
def test_wav_to_mp3_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_wav = tmp / "tone.wav"
        generate_test_wav(src_wav, duration_seconds=1.0)

        planned = plan_conversion(
            source_path=src_wav,
            target_format="mp3",
            raw_settings={"bitrate": "192k"}
        )
        res = execute_conversion(planned)

        assert res.output_path.exists()
        assert res.output_path.suffix == ".mp3"
        assert validate_output_file(res.output_path, "mp3") is True

        probe = FFmpegEngine.probe_media(res.output_path)
        assert probe.get("duration_seconds") is not None
        assert probe["duration_seconds"] >= 0.8


@pytest.mark.skipif(not FFmpegEngine.is_available(), reason="FFmpeg not available")
def test_wav_to_flac_and_ogg_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_wav = tmp / "tone.wav"
        generate_test_wav(src_wav, duration_seconds=0.5)

        # 1. FLAC
        planned_flac = plan_conversion(source_path=src_wav, target_format="flac")
        res_flac = execute_conversion(planned_flac)
        assert res_flac.output_path.exists()
        assert validate_output_file(res_flac.output_path, "flac") is True

        # 2. OGG
        planned_ogg = plan_conversion(source_path=src_wav, target_format="ogg", raw_settings={"bitrate": "128k"})
        res_ogg = execute_conversion(planned_ogg)
        assert res_ogg.output_path.exists()
        assert validate_output_file(res_ogg.output_path, "ogg") is True


@pytest.mark.skipif(not FFmpegEngine.is_available(), reason="FFmpeg not available")
def test_audio_loudness_normalization():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_wav = tmp / "tone.wav"
        generate_test_wav(src_wav, duration_seconds=1.5)

        planned = plan_conversion(
            source_path=src_wav,
            target_format="mp3",
            raw_settings={"loudness_norm": True, "target_lufs": -16.0, "true_peak": -1.0}
        )
        res = execute_conversion(planned)
        assert res.output_path.exists()
        assert validate_output_file(res.output_path, "mp3") is True
