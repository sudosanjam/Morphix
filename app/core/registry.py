"""Central Capability Registry for Morphix.

Single source of truth for all conversion routes, supported formats,
settings schemas, validation requirements, and dynamic engine availability.
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field

from app.engines.base import EngineCapability
from app.engines.images import ImageEngine
from app.engines.ffmpeg import FFmpegEngine
from app.engines.pdf import PDFEngine
from app.engines.spreadsheets import SpreadsheetEngine
from app.engines.structured_data import StructuredDataEngine
from app.engines.documents import DocumentEngine, PandocEngine, LibreOfficeEngine
from app.engines.archives import ArchiveEngine
from app.core.detector import canonical_format, FORMAT_FAMILIES


class SettingDefinition(BaseModel):
    """Schema for a single configurable setting."""
    name: str
    label: str
    type: str  # 'int', 'float', 'str', 'bool', 'select'
    default: Any
    options: Optional[List[Any]] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    step: Optional[float] = None
    category: str = "basic"  # 'basic', 'advanced', 'expert'
    description: str = ""


class ConversionRoute(BaseModel):
    """Declaration of a conversion route between formats."""
    id: str
    engine_name: str
    source_formats: List[str]
    target_formats: List[str]
    lossiness: str  # 'lossless', 'lossy', 'configurable'
    metadata_preservation: str  # 'full', 'partial', 'stripped'
    potential_info_loss: str
    warnings: List[str] = Field(default_factory=list)
    validation_type: str = "basic"  # 'image', 'audio', 'pdf', 'spreadsheet', 'data', 'basic'
    settings_schema: Dict[str, SettingDefinition] = Field(default_factory=dict)

    def is_available(self) -> bool:
        """Check if required engine is currently available at runtime."""
        engine_cls = ENGINE_MAP.get(self.engine_name)
        return bool(engine_cls and engine_cls.is_available())


# Registered engine class mapping
ENGINE_MAP: Dict[str, Type[EngineCapability]] = {
    "pillow": ImageEngine,
    "ffmpeg": FFmpegEngine,
    "pdf": PDFEngine,
    "openpyxl": SpreadsheetEngine,
    "structured_data": StructuredDataEngine,
    "documents": DocumentEngine,
    "pandoc": PandocEngine,
    "libreoffice": LibreOfficeEngine,
    "archives": ArchiveEngine,
}

# Human-friendly format labels
FORMAT_METADATA: Dict[str, Dict[str, Any]] = {
    # Images
    "png": {"name": "PNG Image", "family": "image", "mime": "image/png", "ext": ".png"},
    "jpg": {"name": "JPEG Image", "family": "image", "mime": "image/jpeg", "ext": ".jpg"},
    "webp": {"name": "WebP Image", "family": "image", "mime": "image/webp", "ext": ".webp"},
    "gif": {"name": "GIF Animation/Image", "family": "image", "mime": "image/gif", "ext": ".gif"},
    "bmp": {"name": "BMP Bitmap", "family": "image", "mime": "image/bmp", "ext": ".bmp"},
    "tiff": {"name": "TIFF Image", "family": "image", "mime": "image/tiff", "ext": ".tiff"},
    "ico": {"name": "ICO Windows Icon", "family": "image", "mime": "image/x-icon", "ext": ".ico"},
    # Audio
    "mp3": {"name": "MP3 Audio", "family": "audio", "mime": "audio/mpeg", "ext": ".mp3"},
    "wav": {"name": "WAV PCM Audio", "family": "audio", "mime": "audio/wav", "ext": ".wav"},
    "flac": {"name": "FLAC Lossless Audio", "family": "audio", "mime": "audio/flac", "ext": ".flac"},
    "aac": {"name": "AAC Audio", "family": "audio", "mime": "audio/aac", "ext": ".aac"},
    "m4a": {"name": "M4A Audio", "family": "audio", "mime": "audio/mp4", "ext": ".m4a"},
    "ogg": {"name": "OGG Vorbis Audio", "family": "audio", "mime": "audio/ogg", "ext": ".ogg"},
    "opus": {"name": "Opus Audio", "family": "audio", "mime": "audio/opus", "ext": ".opus"},
    "aiff": {"name": "AIFF Audio", "family": "audio", "mime": "audio/x-aiff", "ext": ".aiff"},
    "ac3": {"name": "AC3 Dolby Audio", "family": "audio", "mime": "audio/ac3", "ext": ".ac3"},
    # Documents
    "pdf": {"name": "PDF Document", "family": "document", "mime": "application/pdf", "ext": ".pdf"},
    "md": {"name": "Markdown Document", "family": "document", "mime": "text/markdown", "ext": ".md"},
    "html": {"name": "HTML Document", "family": "document", "mime": "text/html", "ext": ".html"},
    "txt": {"name": "Plain Text", "family": "document", "mime": "text/plain", "ext": ".txt"},
    "docx": {"name": "Microsoft Word Document", "family": "document", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "ext": ".docx"},
    "odt": {"name": "OpenDocument Text", "family": "document", "mime": "application/vnd.oasis.opendocument.text", "ext": ".odt"},
    "epub": {"name": "EPUB E-Book", "family": "ebook", "mime": "application/epub+zip", "ext": ".epub"},
    # Spreadsheets
    "xlsx": {"name": "Excel Spreadsheet", "family": "spreadsheet", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ext": ".xlsx"},
    "csv": {"name": "CSV Delimited Data", "family": "spreadsheet", "mime": "text/csv", "ext": ".csv"},
    "tsv": {"name": "TSV Tab Delimited Data", "family": "spreadsheet", "mime": "text/tab-separated-values", "ext": ".tsv"},
    # Structured Data
    "json": {"name": "JSON Structured Data", "family": "data", "mime": "application/json", "ext": ".json"},
    "yaml": {"name": "YAML Structured Data", "family": "data", "mime": "application/x-yaml", "ext": ".yaml"},
    "xml": {"name": "XML Document", "family": "data", "mime": "application/xml", "ext": ".xml"},
    # Archives
    "zip": {"name": "ZIP Archive", "family": "archive", "mime": "application/zip", "ext": ".zip"},
    "tar": {"name": "TAR Archive", "family": "archive", "mime": "application/x-tar", "ext": ".tar"},
}


class CapabilityRegistry:
    """Central registry maintaining conversion routes and capabilities."""

    def __init__(self):
        self.routes: List[ConversionRoute] = []
        self._register_default_routes()

    def _register_default_routes(self):
        # 1. Raster Images (Pillow)
        image_settings = {
            "quality": SettingDefinition(
                name="quality", label="Quality", type="int", default=85, min_val=1, max_val=100, step=1,
                category="basic", description="Output encoding quality (1-100)"
            ),
            "width": SettingDefinition(
                name="width", label="Width (px)", type="int", default=None, min_val=1, max_val=16384,
                category="advanced", description="Target pixel width"
            ),
            "height": SettingDefinition(
                name="height", label="Height (px)", type="int", default=None, min_val=1, max_val=16384,
                category="advanced", description="Target pixel height"
            ),
            "preserve_aspect": SettingDefinition(
                name="preserve_aspect", label="Preserve Aspect Ratio", type="bool", default=True,
                category="advanced", description="Retain aspect ratio when resizing"
            ),
            "fit_mode": SettingDefinition(
                name="fit_mode", label="Fit Mode", type="select", default="contain",
                options=["contain", "cover", "fit"], category="advanced", description="How to fit into target dimensions"
            ),
            "resample": SettingDefinition(
                name="resample", label="Resampling Filter", type="select", default="lanczos",
                options=["lanczos", "bicubic", "bilinear", "nearest"], category="expert", description="Interpolation algorithm"
            ),
            "grayscale": SettingDefinition(
                name="grayscale", label="Grayscale", type="bool", default=False,
                category="advanced", description="Convert image to black and white / grayscale"
            ),
            "flatten_transparency": SettingDefinition(
                name="flatten_transparency", label="Flatten Transparency", type="bool", default=False,
                category="advanced", description="Replace alpha transparency with solid background color"
            ),
            "background_color": SettingDefinition(
                name="background_color", label="Background Color", type="str", default="#FFFFFF",
                category="advanced", description="Hex background color when flattening transparency"
            ),
            "rotate": SettingDefinition(
                name="rotate", label="Rotate", type="select", default=0,
                options=[0, 90, 180, 270], category="advanced", description="Clockwise rotation in degrees"
            ),
            "brightness": SettingDefinition(
                name="brightness", label="Brightness", type="float", default=1.0, min_val=0.1, max_val=3.0, step=0.1,
                category="expert", description="Brightness multiplier"
            ),
            "contrast": SettingDefinition(
                name="contrast", label="Contrast", type="float", default=1.0, min_val=0.1, max_val=3.0, step=0.1,
                category="expert", description="Contrast multiplier"
            ),
            "lossless": SettingDefinition(
                name="lossless", label="Lossless Mode (WebP)", type="bool", default=False,
                category="advanced", description="Enable lossless compression for WebP"
            ),
            "strip_metadata": SettingDefinition(
                name="strip_metadata", label="Strip EXIF / Metadata", type="bool", default=False,
                category="advanced", description="Remove embedded metadata for privacy and size reduction"
            ),
        }

        self.routes.append(ConversionRoute(
            id="pillow_image_convert",
            engine_name="pillow",
            source_formats=["png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico"],
            target_formats=["png", "jpg", "webp", "gif", "bmp", "tiff", "ico"],
            lossiness="configurable",
            metadata_preservation="full",
            potential_info_loss="Converting transparency to JPEG flattens alpha to solid background.",
            warnings=["JPEG and BMP do not support alpha transparency."],
            validation_type="image",
            settings_schema=image_settings
        ))

        # 2. Audio Processing (FFmpeg)
        audio_settings = {
            "bitrate": SettingDefinition(
                name="bitrate", label="Bitrate", type="select", default="192k",
                options=["64k", "96k", "128k", "160k", "192k", "256k", "320k"],
                category="basic", description="Audio stream encoding bitrate"
            ),
            "sample_rate": SettingDefinition(
                name="sample_rate", label="Sample Rate", type="select", default=44100,
                options=[22050, 32000, 44100, 48000, 96000],
                category="advanced", description="Sampling rate in Hz"
            ),
            "channels": SettingDefinition(
                name="channels", label="Channels", type="select", default="preserve",
                options=["preserve", "stereo", "mono", "5.1"],
                category="advanced", description="Channel layout"
            ),
            "codec": SettingDefinition(
                name="codec", label="Encoder Codec", type="str", default=None,
                category="expert", description="Specific FFmpeg audio codec identifier"
            ),
            "loudness_norm": SettingDefinition(
                name="loudness_norm", label="Loudness Normalization (LUFS)", type="bool", default=False,
                category="advanced", description="EBU R128 integrated loudness normalization"
            ),
            "target_lufs": SettingDefinition(
                name="target_lufs", label="Target LUFS", type="float", default=-16.0, min_val=-24.0, max_val=-12.0, step=0.5,
                category="advanced", description="Target integrated loudness level in LUFS"
            ),
            "true_peak": SettingDefinition(
                name="true_peak", label="True Peak Ceiling (dBTP)", type="float", default=-1.0, min_val=-3.0, max_val=0.0, step=0.5,
                category="expert", description="True-peak limiter ceiling in dBTP"
            ),
            "volume_db": SettingDefinition(
                name="volume_db", label="Volume Adjustment (dB)", type="float", default=0.0, min_val=-20.0, max_val=20.0, step=0.5,
                category="advanced", description="Direct gain adjustment in decibels"
            ),
            "trim_start": SettingDefinition(
                name="trim_start", label="Trim Start (seconds)", type="float", default=0.0, min_val=0.0,
                category="expert", description="Start position offset in seconds"
            ),
            "trim_end": SettingDefinition(
                name="trim_end", label="Trim End (seconds)", type="float", default=None, min_val=0.0,
                category="expert", description="End position timestamp in seconds"
            ),
            "strip_metadata": SettingDefinition(
                name="strip_metadata", label="Strip Metadata / Tags", type="bool", default=False,
                category="advanced", description="Strip ID3 and container tags"
            ),
        }

        self.routes.append(ConversionRoute(
            id="ffmpeg_audio_convert",
            engine_name="ffmpeg",
            source_formats=["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma", "aiff", "ac3", "alac"],
            target_formats=["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "aiff", "ac3"],
            lossiness="configurable",
            metadata_preservation="full",
            potential_info_loss="Lossy compression (MP3, AAC, OGG) discards high-frequency audio data.",
            warnings=["Converting lossless to lossy cannot be reversed."],
            validation_type="audio",
            settings_schema=audio_settings
        ))

        # 3. PDF Operations & Document-to-PDF (pypdf & reportlab)
        pdf_settings = {
            "page_range": SettingDefinition(
                name="page_range", label="Page Range", type="str", default=None,
                category="basic", description="Page range filter (e.g. '1-5, 8')"
            ),
            "rotate_pages": SettingDefinition(
                name="rotate_pages", label="Rotate Pages", type="select", default=0,
                options=[0, 90, 180, 270], category="advanced", description="Rotate pages clockwise"
            ),
            "title": SettingDefinition(
                name="title", label="Document Title", type="str", default=None,
                category="advanced", description="PDF Metadata title"
            ),
            "author": SettingDefinition(
                name="author", label="Author", type="str", default=None,
                category="advanced", description="PDF Metadata author"
            ),
        }

        self.routes.append(ConversionRoute(
            id="pypdf_pdf_convert",
            engine_name="pdf",
            source_formats=["pdf", "txt", "md", "png", "jpg", "jpeg"],
            target_formats=["pdf", "txt"],
            lossiness="lossless",
            metadata_preservation="full",
            potential_info_loss="Extracting PDF to TXT discards vector graphics, images, and formatting.",
            warnings=["Extracting plain text from scanned PDFs requires OCR."],
            validation_type="pdf",
            settings_schema=pdf_settings
        ))

        # 4. Spreadsheets (openpyxl & csv)
        sheet_settings = {
            "delimiter": SettingDefinition(
                name="delimiter", label="Delimiter", type="select", default="comma",
                options=["comma", "tab", "semicolon", "pipe"], category="basic", description="Field separator"
            ),
            "encoding": SettingDefinition(
                name="encoding", label="Encoding", type="select", default="utf-8",
                options=["utf-8", "latin-1", "cp1252"], category="advanced", description="Character encoding"
            ),
            "quoting": SettingDefinition(
                name="quoting", label="Quoting Style", type="select", default="minimal",
                options=["minimal", "all", "nonnumeric", "none"], category="expert", description="CSV quoting rule"
            ),
            "sheet_name": SettingDefinition(
                name="sheet_name", label="Sheet Name", type="str", default=None,
                category="advanced", description="Specific worksheet to export (defaults to active sheet)"
            ),
        }

        self.routes.append(ConversionRoute(
            id="openpyxl_sheet_convert",
            engine_name="openpyxl",
            source_formats=["xlsx", "csv", "tsv"],
            target_formats=["xlsx", "csv", "tsv", "json"],
            lossiness="configurable",
            metadata_preservation="partial",
            potential_info_loss="Exporting XLSX to CSV discards multiple sheets, cell formatting, formulas, and charts.",
            warnings=["Only the active or selected sheet is exported to delimited text."],
            validation_type="spreadsheet",
            settings_schema=sheet_settings
        ))

        # 5. Structured Data (JSON, YAML, XML)
        data_settings = {
            "indent": SettingDefinition(
                name="indent", label="Indentation Spaces", type="int", default=2, min_val=0, max_val=8,
                category="basic", description="Number of indentation spaces"
            ),
            "sort_keys": SettingDefinition(
                name="sort_keys", label="Sort Keys Alphabetically", type="bool", default=False,
                category="advanced", description="Sort object dictionary keys"
            ),
            "root_tag": SettingDefinition(
                name="root_tag", label="XML Root Tag", type="str", default="root",
                category="advanced", description="Root element tag when exporting to XML"
            ),
        }

        self.routes.append(ConversionRoute(
            id="structured_data_convert",
            engine_name="structured_data",
            source_formats=["json", "yaml", "yml", "xml"],
            target_formats=["json", "yaml", "xml"],
            lossiness="lossless",
            metadata_preservation="full",
            potential_info_loss="Comments in YAML are not preserved when parsed into JSON or XML.",
            warnings=[],
            validation_type="data",
            settings_schema=data_settings
        ))

        # 6. Documents (Markdown, HTML, TXT)
        doc_settings = {
            "title": SettingDefinition(
                name="title", label="Document Title", type="str", default=None,
                category="basic", description="HTML page title"
            ),
        }

        self.routes.append(ConversionRoute(
            id="documents_convert",
            engine_name="documents",
            source_formats=["md", "markdown", "html", "htm", "txt"],
            target_formats=["html", "txt", "md"],
            lossiness="configurable",
            metadata_preservation="partial",
            potential_info_loss="Converting rich HTML or Markdown to TXT discards styling, links, and media.",
            warnings=[],
            validation_type="basic",
            settings_schema=doc_settings
        ))

        # 7. Pandoc Adapter (Optional)
        self.routes.append(ConversionRoute(
            id="pandoc_office_convert",
            engine_name="pandoc",
            source_formats=["docx", "odt", "epub", "md", "html", "rtf"],
            target_formats=["md", "html", "docx", "epub", "pdf"],
            lossiness="configurable",
            metadata_preservation="full",
            potential_info_loss="Complex document layout and custom macros may be altered.",
            warnings=["Requires Pandoc executable."],
            validation_type="basic",
            settings_schema={}
        ))

        # 8. LibreOffice Adapter (Optional)
        self.routes.append(ConversionRoute(
            id="libreoffice_office_convert",
            engine_name="libreoffice",
            source_formats=["docx", "doc", "odt", "rtf", "pptx", "ppt", "odp", "xlsx", "ods"],
            target_formats=["pdf"],
            lossiness="lossless",
            metadata_preservation="full",
            potential_info_loss="Font substitution may occur if original document fonts are missing on this system.",
            warnings=["Requires LibreOffice / soffice installation."],
            validation_type="pdf",
            settings_schema={}
        ))

        # 9. Archives (ZIP, TAR)
        self.routes.append(ConversionRoute(
            id="archives_convert",
            engine_name="archives",
            source_formats=["zip", "tar", "gz"],
            target_formats=["zip", "tar"],
            lossiness="lossless",
            metadata_preservation="full",
            potential_info_loss="None.",
            warnings=[],
            validation_type="basic",
            settings_schema={}
        ))

    def find_route(self, source_fmt: str, target_fmt: str) -> Optional[ConversionRoute]:
        """Find a route for the given format pair, verifying engine availability."""
        src = canonical_format(source_fmt)
        tgt = canonical_format(target_fmt)

        for route in self.routes:
            if src in route.source_formats and tgt in route.target_formats:
                # Check engine availability
                if route.is_available():
                    return route
        return None

    def get_available_targets(self, source_fmt: str) -> List[Dict[str, Any]]:
        """Return available target formats for a given source format whose engine is operational."""
        src = canonical_format(source_fmt)
        available_targets: Dict[str, Dict[str, Any]] = {}

        for route in self.routes:
            if src in route.source_formats and route.is_available():
                for tgt in route.target_formats:
                    if tgt != src and tgt not in available_targets:
                        meta = FORMAT_METADATA.get(tgt, {
                            "name": tgt.upper(),
                            "family": FORMAT_FAMILIES.get(tgt, "other"),
                            "ext": f".{tgt}"
                        })
                        available_targets[tgt] = {
                            "format": tgt,
                            "name": meta.get("name", tgt.upper()),
                            "family": meta.get("family", "other"),
                            "engine": route.engine_name,
                            "lossiness": route.lossiness,
                            "potential_loss": route.potential_info_loss,
                            "warnings": route.warnings
                        }

        return list(available_targets.values())

    def get_all_supported_formats(self) -> Dict[str, Any]:
        """Return list of all registered formats categorized by family with availability indicators."""
        result = {}
        for fmt, meta in FORMAT_METADATA.items():
            # Check if this format has at least one working route as input or output
            has_route = any(
                (fmt in r.source_formats or fmt in r.target_formats) and r.is_available()
                for r in self.routes
            )
            result[fmt] = {
                "format": fmt,
                "name": meta["name"],
                "family": meta["family"],
                "mime": meta["mime"],
                "extension": meta["ext"],
                "available": has_route
            }
        return result

    def get_engine_statuses(self) -> List[Dict[str, Any]]:
        """Return status and versions of all conversion engines."""
        statuses = []
        for name, cls in ENGINE_MAP.items():
            statuses.append(cls.get_status())
        return statuses


# Singleton registry instance
registry = CapabilityRegistry()
