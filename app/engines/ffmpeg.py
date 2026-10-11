"""FFmpeg audio conversion, resampling, loudness normalization, and stream inspection."""

import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.engines.base import EngineCapability
from app.core.errors import ConversionFailedError, EngineNotFoundError
from app.config import config


class FFmpegEngine(EngineCapability):
    name = "ffmpeg"
    display_name = "FFmpeg Audio & Media Engine"

    SUPPORTED_INPUTS = ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma", "aiff", "aif", "ac3", "alac"]
    SUPPORTED_OUTPUTS = ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "aiff", "ac3"]

    _cached_exe: Optional[str] = None
    _cached_version: Optional[str] = None

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        if cls._cached_exe and os.path.exists(cls._cached_exe):
            return cls._cached_exe

        # 1. Custom configured path
        custom = config.settings.custom_ffmpeg_path
        if custom and os.path.exists(custom):
            cls._cached_exe = custom
            return custom

        # 2. System PATH
        sys_path = shutil.which("ffmpeg")
        if sys_path:
            cls._cached_exe = sys_path
            return sys_path

        # 3. imageio-ffmpeg bundled binary
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and os.path.exists(exe):
                cls._cached_exe = exe
                return exe
        except Exception:
            pass

        return None

    @classmethod
    def is_available(cls) -> bool:
        return cls.get_binary_path() is not None

    @classmethod
    def get_version(cls) -> Optional[str]:
        if cls._cached_version:
            return cls._cached_version
        exe = cls.get_binary_path()
        if not exe:
            return None
        try:
            res = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.splitlines()[0]
            # e.g. ffmpeg version 7.1-essentials...
            m = re.search(r"ffmpeg version\s+([^\s]+)", first_line)
            if m:
                cls._cached_version = m.group(1)
            else:
                cls._cached_version = first_line[:30]
            return cls._cached_version
        except Exception:
            return None

    @classmethod
    def probe_media(cls, file_path: Path) -> Dict[str, Any]:
        """Inspect audio stream properties using ffmpeg."""
        exe = cls.get_binary_path()
        if not exe:
            return {}

        # Run ffmpeg -i <file> and parse stderr for stream details
        cmd = [exe, "-hide_banner", "-i", str(file_path)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = res.stderr

            info: Dict[str, Any] = {
                "format": "unknown",
                "duration_seconds": None,
                "duration_str": None,
                "bitrate_kbps": None,
                "codec": None,
                "sample_rate": None,
                "channels": None,
                "channel_layout": None,
                "bit_depth": None
            }

            # Parse Duration: 00:03:15.20, start: 0.000000, bitrate: 320 kb/s
            dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
            if dur_match:
                h, m, s = float(dur_match.group(1)), float(dur_match.group(2)), float(dur_match.group(3))
                total_secs = h * 3600 + m * 60 + s
                info["duration_seconds"] = round(total_secs, 2)
                info["duration_str"] = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

            br_match = re.search(r"bitrate:\s*(\d+)\s*kb/s", output)
            if br_match:
                info["bitrate_kbps"] = int(br_match.group(1))

            # Stream #0:0: Audio: mp3, 44100 Hz, stereo, fltp, 320 kb/s
            audio_match = re.search(r"Stream #0:\d+.*?: Audio:\s*([^,\n]+),\s*(\d+)\s*Hz,\s*([^,\n]+)", output)
            if audio_match:
                info["codec"] = audio_match.group(1).strip()
                info["sample_rate"] = int(audio_match.group(2))
                info["channel_layout"] = audio_match.group(3).strip()
                if "mono" in info["channel_layout"]:
                    info["channels"] = 1
                elif "stereo" in info["channel_layout"]:
                    info["channels"] = 2
                elif "5.1" in info["channel_layout"]:
                    info["channels"] = 6
                else:
                    info["channels"] = 2

            # Check PCM bit depth if pcm
            pcm_match = re.search(r"pcm_s(\d+)le", output)
            if pcm_match:
                info["bit_depth"] = int(pcm_match.group(1))

            return info
        except Exception:
            return {}

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert audio file using FFmpeg with advanced audio parameters."""
        exe = cls.get_binary_path()
        if not exe:
            raise EngineNotFoundError("FFmpeg", "Install FFmpeg or check imageio-ffmpeg installation.")

        fmt = target_format.lower()
        if fmt == "aif":
            fmt = "aiff"

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_cb:
            progress_cb(10, "Building audio processing pipeline...")

        # Base ffmpeg command
        cmd: List[str] = [exe, "-y", "-hide_banner", "-loglevel", "error"]

        # Trimming start before input for fast seek
        trim_start = settings.get("trim_start")
        if trim_start is not None and float(trim_start) > 0:
            cmd.extend(["-ss", str(float(trim_start))])

        cmd.extend(["-i", str(source_path)])

        # Trimming end
        trim_end = settings.get("trim_end")
        if trim_end is not None and float(trim_end) > 0:
            cmd.extend(["-to", str(float(trim_end))])

        # Audio filters pipeline
        filters: List[str] = []

        # 1. Volume adjustment
        volume_db = settings.get("volume_db")
        if volume_db is not None and float(volume_db) != 0.0:
            filters.append(f"volume={float(volume_db):.1f}dB")

        # 2. Fade in / fade out
        fade_in = settings.get("fade_in")
        if fade_in is not None and float(fade_in) > 0:
            filters.append(f"afade=t=in:ss=0:d={float(fade_in):.2f}")

        fade_out = settings.get("fade_out")
        if fade_out is not None and float(fade_out) > 0:
            # Note: afade out needs start time, or can be applied if duration is known
            dur = cls.probe_media(source_path).get("duration_seconds")
            if dur and dur > float(fade_out):
                st = dur - float(fade_out)
                filters.append(f"afade=t=out:st={st:.2f}:d={float(fade_out):.2f}")

        # 3. Loudness normalization (EBU R128 LUFS)
        if settings.get("loudness_norm", False):
            target_lufs = float(settings.get("target_lufs", -16.0))
            true_peak = float(settings.get("true_peak", -1.0))
            filters.append(f"loudnorm=I={target_lufs:.1f}:TP={true_peak:.1f}:LRA=11")

        if filters:
            cmd.extend(["-af", ",".join(filters)])

        # Codec selection & Format specific flags
        default_codecs = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "flac": "flac",
            "aac": "aac",
            "m4a": "aac",
            "ogg": "libvorbis",
            "opus": "libopus",
            "aiff": "pcm_s16le",
            "ac3": "ac3",
        }

        requested_codec = settings.get("codec")
        codec = requested_codec or default_codecs.get(fmt)
        if codec:
            cmd.extend(["-c:a", codec])

        # Bitrate
        bitrate = settings.get("bitrate")
        if bitrate and fmt in ("mp3", "aac", "m4a", "ogg", "opus", "ac3"):
            cmd.extend(["-b:a", str(bitrate)])

        # Sample rate
        sample_rate = settings.get("sample_rate")
        if sample_rate:
            cmd.extend(["-ar", str(int(sample_rate))])

        # Channels (mono/stereo)
        channels = settings.get("channels")
        if channels == "mono":
            cmd.extend(["-ac", "1"])
        elif channels == "stereo":
            cmd.extend(["-ac", "2"])
        elif channels == "5.1":
            cmd.extend(["-ac", "6"])

        # PCM depth for WAV/AIFF
        if fmt in ("wav", "aiff") and not requested_codec:
            depth = int(settings.get("pcm_depth", 16))
            if depth == 24:
                cmd.extend(["-c:a", "pcm_s24le"])
            elif depth == 32:
                cmd.extend(["-c:a", "pcm_s32le"])
            else:
                cmd.extend(["-c:a", "pcm_s16le"])

        # Strip metadata
        if settings.get("strip_metadata", False):
            cmd.extend(["-map_metadata", "-1"])

        # Output target
        cmd.append(str(target_path))

        if progress_cb:
            progress_cb(50, f"Encoding {fmt.upper()} stream...")

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode != 0:
                raise ConversionFailedError(
                    f"FFmpeg conversion exited with code {res.returncode}",
                    stderr=res.stderr,
                    exit_code=res.returncode
                )
        except subprocess.TimeoutExpired:
            raise ConversionFailedError("FFmpeg conversion timed out after 300 seconds.")
        except Exception as e:
            if isinstance(e, ConversionFailedError):
                raise
            raise ConversionFailedError(f"Subprocess execution failed: {str(e)}")

        if progress_cb:
            progress_cb(100, "Audio conversion finished.")

        return target_path
