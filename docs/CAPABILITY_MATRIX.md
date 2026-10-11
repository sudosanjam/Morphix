# Morphix Capability Matrix

This document provides a comprehensive reference of all conversion routes implemented in Morphix, their required engines, available settings, and fidelity characteristics.

---

## 1. Raster Images (Engine: `pillow`)

- **Source Formats:** `PNG`, `JPG`, `JPEG`, `WebP`, `GIF`, `BMP`, `TIFF`, `ICO`
- **Target Formats:** `PNG`, `JPG`, `WebP`, `GIF`, `BMP`, `TIFF`, `ICO`
- **Availability:** Built-in Python runtime (`Pillow`)
- **Lossiness:** Configurable
- **Preservation:** Full image structure; EXIF metadata preserved unless `strip_metadata` is selected.

### Supported Settings:
| Setting | Type | Range / Options | Default | Description |
|---|---|---|---|---|
| `quality` | int | 1 – 100 | 85 | Output encoding quality for lossy formats |
| `width` | int | 1 – 16384 | None | Target width in pixels |
| `height` | int | 1 – 16384 | None | Target height in pixels |
| `preserve_aspect` | bool | True / False | True | Retains aspect ratio when resizing |
| `fit_mode` | select | `contain`, `cover`, `fit` | `contain` | Sizing behavior when both dimensions specified |
| `resample` | select | `lanczos`, `bicubic`, `bilinear`, `nearest` | `lanczos` | Interpolation filter |
| `lossless` | bool | True / False | False | Enable lossless compression (WebP) |
| `flatten_transparency` | bool | True / False | False | Flatten alpha transparency to solid background |
| `background_color` | str | Hex (e.g. `#FFFFFF`) | `#FFFFFF` | Background color for flattened transparency |
| `rotate` | select | 0, 90, 180, 270 | 0 | Clockwise rotation in degrees |
| `grayscale` | bool | True / False | False | Convert to grayscale |
| `brightness` | float | 0.1 – 3.0 | 1.0 | Brightness multiplier |
| `contrast` | float | 0.1 – 3.0 | 1.0 | Contrast multiplier |
| `strip_metadata` | bool | True / False | False | Remove EXIF and embedded metadata |

---

## 2. Audio Processing (Engine: `ffmpeg`)

- **Source Formats:** `MP3`, `WAV`, `FLAC`, `AAC`, `M4A`, `OGG`, `Opus`, `WMA`, `AIFF`, `AC3`, `ALAC`
- **Target Formats:** `MP3`, `WAV`, `FLAC`, `AAC`, `M4A`, `OGG`, `Opus`, `AIFF`, `AC3`
- **Availability:** Detected via system PATH or bundled `imageio-ffmpeg`
- **Lossiness:** Configurable

### Supported Settings:
| Setting | Type | Range / Options | Default | Description |
|---|---|---|---|---|
| `bitrate` | select | `64k`, `96k`, `128k`, `160k`, `192k`, `256k`, `320k` | `192k` | Output encoding bitrate |
| `sample_rate` | select | 22050, 32000, 44100, 48000, 96000 | 44100 | Audio sampling rate in Hz |
| `channels` | select | `preserve`, `stereo`, `mono`, `5.1` | `preserve` | Channel layout / downmix |
| `codec` | str | Any valid FFmpeg audio encoder | Auto | Specific encoder identifier |
| `loudness_norm` | bool | True / False | False | EBU R128 integrated loudness normalization |
| `target_lufs` | float | -24.0 to -12.0 | -16.0 | Target integrated loudness in LUFS |
| `true_peak` | float | -3.0 to 0.0 | -1.0 | True peak ceiling in dBTP |
| `volume_db` | float | -20.0 to +20.0 | 0.0 | Direct gain adjustment in dB |
| `trim_start` | float | >= 0.0 | 0.0 | Start offset in seconds |
| `trim_end` | float | >= 0.0 | None | End offset in seconds |
| `strip_metadata` | bool | True / False | False | Strip ID3 tags and metadata |

---

## 3. PDF Operations (Engine: `pdf` / `pypdf` & `reportlab`)

- **Source Formats:** `PDF`, `TXT`, `MD`, `PNG`, `JPG`
- **Target Formats:** `PDF`, `TXT`
- **Availability:** Built-in Python runtime
- **Lossiness:** Lossless (page manipulation) / Text extraction

### Supported Settings:
| Setting | Type | Options | Default | Description |
|---|---|---|---|---|
| `page_range` | str | e.g. `1-3, 5` | None | Extract specific page ranges |
| `rotate_pages` | select | 0, 90, 180, 270 | 0 | Clockwise page rotation |
| `title` | str | text | None | Document metadata title |
| `author` | str | text | None | Document metadata author |

---

## 4. Spreadsheets & Delimited Data (Engine: `openpyxl`)

- **Source Formats:** `XLSX`, `CSV`, `TSV`
- **Target Formats:** `XLSX`, `CSV`, `TSV`, `JSON`
- **Availability:** Built-in Python runtime

### Supported Settings:
| Setting | Type | Options | Default | Description |
|---|---|---|---|---|
| `delimiter` | select | `comma`, `tab`, `semicolon`, `pipe` | `comma` | Field delimiter |
| `encoding` | select | `utf-8`, `latin-1`, `cp1252` | `utf-8` | Text encoding |
| `sheet_name` | str | text | Active Sheet | Specific worksheet to export |
| `quoting` | select | `minimal`, `all`, `nonnumeric`, `none` | `minimal` | Quoting rule |

---

## 5. Structured Data (Engine: `structured_data`)

- **Source Formats:** `JSON`, `YAML`, `XML`
- **Target Formats:** `JSON`, `YAML`, `XML`
- **Availability:** Built-in Python runtime

---

## 6. Optional System Adapters

- **Pandoc (`pandoc`):** DOCX, ODT, EPUB, RTF conversions. Detected dynamically at runtime.
- **LibreOffice (`libreoffice` / `soffice`):** Office documents (DOCX, PPTX, ODP) to PDF export. Detected dynamically at runtime.
