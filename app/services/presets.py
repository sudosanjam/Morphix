"""Preset Management: built-in and user custom conversion presets."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.config import config
from app.core.registry import registry


class Preset(BaseModel):
    id: str
    name: str
    description: str
    category: str  # 'image', 'audio', 'document', 'spreadsheet', 'data'
    target_format: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    is_builtin: bool = False


BUILTIN_PRESETS: List[Preset] = [
    Preset(
        id="web_image",
        name="Web Image (WebP 80%)",
        description="Optimized modern WebP for web delivery with balanced compression",
        category="image",
        target_format="webp",
        settings={"quality": 80, "preserve_aspect": True, "strip_metadata": True},
        is_builtin=True
    ),
    Preset(
        id="high_quality_image",
        name="High-Quality PNG",
        description="Lossless high fidelity PNG image preserving full detail and transparency",
        category="image",
        target_format="png",
        settings={"optimize": True, "png_compression": 6},
        is_builtin=True
    ),
    Preset(
        id="small_image",
        name="Small Web Image (1280px)",
        description="Lightweight WebP scaled down to 1280px max width for rapid mobile loading",
        category="image",
        target_format="webp",
        settings={"width": 1280, "quality": 70, "preserve_aspect": True, "strip_metadata": True},
        is_builtin=True
    ),
    Preset(
        id="podcast_audio",
        name="Podcast Audio (MP3 128k LUFS)",
        description="Standard broadcast podcast audio with -16 LUFS loudness normalization",
        category="audio",
        target_format="mp3",
        settings={"bitrate": "128k", "loudness_norm": True, "target_lufs": -16.0, "true_peak": -1.0},
        is_builtin=True
    ),
    Preset(
        id="voice_recording",
        name="Voice Recording (Opus Mono 64k)",
        description="Ultra-efficient voice audio encoding with speech optimization and LUFS normalization",
        category="audio",
        target_format="opus",
        settings={"bitrate": "64k", "channels": "mono", "loudness_norm": True, "target_lufs": -16.0},
        is_builtin=True
    ),
    Preset(
        id="lossless_audio",
        name="Lossless Archive (FLAC)",
        description="Bit-perfect FLAC audio archive preserving all dynamic range and channel fidelity",
        category="audio",
        target_format="flac",
        settings={"sample_rate": 44100, "channels": "preserve"},
        is_builtin=True
    ),
    Preset(
        id="pdf_export",
        name="Clean PDF Export",
        description="Standard PDF document export with clean pagination",
        category="document",
        target_format="pdf",
        settings={},
        is_builtin=True
    ),
    Preset(
        id="pdf_to_images",
        name="PDF to PNG Pages (150 DPI)",
        description="Render all pages of a PDF document to crisp individual PNG images",
        category="document",
        target_format="png",
        settings={"dpi": 150},
        is_builtin=True
    ),
    Preset(
        id="spreadsheet_export",
        name="Standard CSV Export",
        description="Clean comma-separated values in UTF-8 encoding for cross-platform data interchange",
        category="spreadsheet",
        target_format="csv",
        settings={"delimiter": "comma", "encoding": "utf-8", "quoting": "minimal"},
        is_builtin=True
    ),
]


class PresetService:
    """Manages preset retrieval, creation, updating, and exporting."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or config.presets_file
        self.user_presets: List[Preset] = self._load_user_presets()

    def _load_user_presets(self) -> List[Preset]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [Preset(**item) for item in data]
            except Exception:
                pass
        return []

    def _save_user_presets(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in self.user_presets], f, indent=2)

    def list_presets(self, category: Optional[str] = None) -> List[Preset]:
        all_presets = BUILTIN_PRESETS + self.user_presets
        if category:
            return [p for p in all_presets if p.category == category]
        return all_presets

    def get_preset(self, preset_id: str) -> Optional[Preset]:
        for p in BUILTIN_PRESETS + self.user_presets:
            if p.id == preset_id:
                return p
        return None

    def create_preset(
        self,
        name: str,
        description: str,
        category: str,
        target_format: str,
        settings: Dict[str, Any]
    ) -> Preset:
        import uuid
        new_id = f"custom_{uuid.uuid4().hex[:8]}"
        preset = Preset(
            id=new_id,
            name=name,
            description=description,
            category=category,
            target_format=target_format,
            settings=settings,
            is_builtin=False
        )
        self.user_presets.append(preset)
        self._save_user_presets()
        return preset

    def delete_preset(self, preset_id: str) -> bool:
        # Cannot delete builtin presets
        for p in BUILTIN_PRESETS:
            if p.id == preset_id:
                return False
        orig_len = len(self.user_presets)
        self.user_presets = [p for p in self.user_presets if p.id != preset_id]
        if len(self.user_presets) < orig_len:
            self._save_user_presets()
            return True
        return False

    def export_presets_json(self) -> str:
        return json.dumps([p.model_dump() for p in self.list_presets()], indent=2)

    def import_presets_json(self, json_str: str) -> int:
        data = json.loads(json_str)
        count = 0
        for item in data:
            if not item.get("is_builtin"):
                # assign unique ID to prevent conflicts
                item["id"] = f"imported_{item.get('id', 'preset')}"
                self.user_presets.append(Preset(**item))
                count += 1
        self._save_user_presets()
        return count


# Singleton presets instance
presets = PresetService()
