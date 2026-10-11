# Morphix — Universal Offline File Conversion Suite

> **High-performance, privacy-first cross-platform file conversion, optimization, and document processing utility.**  
> 100% offline local processing · Zero network telemetry · Desktop-grade Web GUI & CLI · Windows 10/11 & Linux

---

## 1. Overview

**Morphix** is a purpose-built desktop and command-line utility for converting, optimizing, and transforming media and documents without cloud dependencies or third-party web uploads. Built with a shared modular conversion core in Python 3, a local FastAPI/Uvicorn server, and a high-density, responsive vanilla HTML5/CSS/JavaScript interface, Morphix handles single-file quick conversions as well as high-throughput batch operations.

### Key Capabilities
- **Strictly Offline & Private:** Operates 100% locally on your machine. No accounts, API keys, tracking, or network calls.
- **Unified Core:** Both the local web GUI and the `morphix` CLI share the identical capability registry, conversion planner, and validation pipeline.
- **Multi-Format Processing:** Raster images, high-fidelity audio, documents, spreadsheets, presentations, and structured data.
- **Deep Format Settings:** Exposes granular audio bitrate, EBU R128 LUFS loudness normalization, true-peak limiting, image dimensions, resampling filters, WebP lossless mode, PDF page ranges/rotation, and spreadsheet delimiters.
- **Pre-Flight Validation:** All generated outputs are deeply validated by format decoders and checked for non-empty sizes before reporting success.
- **Safe by Default:** Originals are never overwritten by default; collisions are automatically renamed (`_1`, `_2`), and partial outputs from failed jobs are cleaned up immediately.

---

## 2. Supported Formats & Capability Matrix

| Family | Input Formats | Target Formats | Engine | Status | Lossiness |
|---|---|---|---|---|---|
| **Images** | `PNG`, `JPG`, `WebP`, `GIF`, `BMP`, `TIFF`, `ICO` | `PNG`, `JPG`, `WebP`, `GIF`, `BMP`, `TIFF`, `ICO` | Pillow | Built-in | Configurable (Quality 1–100, Lossless WebP) |
| **Audio** | `MP3`, `WAV`, `FLAC`, `AAC`, `M4A`, `OGG`, `Opus`, `AIFF`, `AC3` | `MP3`, `WAV`, `FLAC`, `AAC`, `M4A`, `OGG`, `Opus`, `AIFF`, `AC3` | FFmpeg | Built-in / Bundled | Configurable (Bitrate 64k–320k, Sample Rate, Channels, LUFS) |
| **PDF Tools** | `PDF`, `TXT`, `MD`, `PNG`, `JPG` | `PDF`, `TXT` | pypdf & ReportLab | Built-in | Lossless / Extraction |
| **Documents** | `MD`, `HTML`, `TXT` | `HTML`, `TXT`, `MD`, `PDF` | Python Markdown & Platypus | Built-in | Configurable |
| **Office Docs** | `DOCX`, `DOC`, `ODT`, `PPTX`, `PPT`, `ODP` | `PDF`, `TXT` | LibreOffice / Pandoc | Optional Adapters | Lossless PDF Export |
| **Spreadsheets** | `XLSX`, `CSV`, `TSV` | `XLSX`, `CSV`, `TSV`, `JSON` | openpyxl & csv | Built-in | Configurable (Delimiters, Quotes, Sheets) |
| **Data** | `JSON`, `YAML`, `XML` | `JSON`, `YAML`, `XML` | pyyaml & defusedxml | Built-in | Lossless |
| **Archives** | `ZIP`, `TAR`, `GZ` | `ZIP`, `TAR` | Python standard | Built-in | Lossless |

---

## 3. Installation & Setup

### 3.1 One-Click Setup from Git ZIP / Source (Recommended)

When you download and extract the Git ZIP package on any new computer:

#### On Windows:
Double-click or run the root installer:
```cmd
windows_install.bat
```
*(or run `powershell -ExecutionPolicy Bypass -File .\windows_install.ps1`)*

- Automatically detects or prompts for Python 3 (>= 3.10).
- Creates an isolated `.venv` virtual environment in the project directory.
- Installs all dependencies (`requirements.txt`).
- Creates a Desktop shortcut and root launcher `run_morphix.bat`.
- Immediately launches the Morphix Web GUI in your default browser at `http://127.0.0.1:7474`.

#### On Linux:
Run the root installer:
```bash
./linux_install.sh
# or: bash linux_install.sh
```
- Checks for Python 3 (>= 3.10) and distro dependencies (`python3-venv`, `pip`).
- Sets up an isolated `.venv` environment and installs dependencies.
- Creates root launcher `./run_morphix.sh`, registers `~/.local/bin/morphix` in PATH, and adds `morphix.desktop`.
- Immediately launches the Morphix Web GUI in your default browser at `http://127.0.0.1:7474`.

---

### 3.2 Pre-Packaged Binary Distributions

#### Windows Pre-built Installer / Portable:
- **`Morphix-Setup.exe`**: Inno Setup installer registering Start Menu and PATH.
- **`Morphix.exe`**: Portable standalone executable. Double-click to run anywhere.

#### Everyday Launching:
After the initial one-click install, you can start Morphix at any time by:
- **Windows**: Double-clicking `run_morphix.bat` or the Desktop shortcut.
- **Linux**: Running `./run_morphix.sh` or typing `morphix` in your terminal.

---

## 4. Usage Guide

### 4.1 Launching the Web GUI
You can start the local desktop server in your default browser either by:
1. **Double-clicking `Morphix.exe`** on Windows (packaged standalone).
2. Or running via CLI / Python:
```bash
morphix serve
```
Or:
```bash
python -m app.cli.main serve
```
By default, the server securely binds to `http://127.0.0.1:7474`.

#### GUI Navigation & Shortcuts:
- **Ctrl+K**: Open Quick Command Palette
- **Ctrl+O**: Open file selection dialog
- **Ctrl+Enter**: Start queue conversion
- **Ctrl+,**: Open Application Settings
- **Escape**: Close dialog or modal

### 4.2 Command-Line Interface (CLI)

The executable command is `morphix`.

#### Convert a Single File:
```bash
# Convert PNG image to WebP with 85% quality
morphix convert photo.png --to webp --quality 85

# Resize image maintaining aspect ratio
morphix convert wallpaper.png --to webp --width 1920 --height 1080

# Convert audio to MP3 with broadcast loudness normalization
morphix convert podcast.wav --to mp3 --bitrate 192k --loudnorm

# Extract pages from a PDF
morphix convert document.pdf --to pdf --output ./pages1-5.pdf

# Export Excel sheet to CSV
morphix convert sales.xlsx --to csv --output ./sales.csv
```

#### Batch Conversion:
```bash
# Convert all images in a directory to WebP
morphix batch ./photos --to webp --output ./converted

# Recursive folder traversal
morphix batch ./recordings --to mp3 --recursive --output ./mp3_out
```

#### File Inspection:
```bash
morphix inspect audio_sample.flac
morphix inspect photo.jpg --json
```

#### Available Routes & Engine Doctor:
```bash
# View available target formats for a file
morphix formats --input recording.wav

# Run system diagnostic health check
morphix doctor
```

#### Presets & History:
```bash
# List built-in and custom presets
morphix preset list

# View conversion history
morphix history list --limit 20
```

---

## 5. Architecture & Components

```
Morphix/
├── app/
│   ├── config.py           # Platform paths & settings manager
│   ├── main.py             # FastAPI server & static file host
│   ├── core/
│   │   ├── detector.py     # Magic byte format detection
│   │   ├── registry.py     # Central capability registry
│   │   ├── planner.py      # Conversion route planner & settings validator
│   │   ├── converter.py    # Execution orchestrator & cleanup
│   │   ├── validation.py   # Output integrity verification
│   │   ├── metadata.py     # Deep metadata & stream inspector
│   │   ├── jobs.py         # Thread-safe bounded job worker pool
│   │   └── errors.py       # Normalized exception hierarchy
│   ├── engines/            # Modular conversion engines
│   │   ├── images.py       # Pillow raster engine
│   │   ├── ffmpeg.py       # FFmpeg audio & loudness engine
│   │   ├── pdf.py          # pypdf & ReportLab engine
│   │   ├── spreadsheets.py # openpyxl & csv engine
│   │   ├── structured_data.py # JSON, YAML, XML engine
│   │   ├── documents.py    # Markdown & Document adapters
│   │   └── archives.py     # ZIP & TAR engine
│   ├── services/           # History (SQLite), Presets (JSON), Diagnostics
│   ├── api/                # REST endpoints
│   ├── cli/                # Typer CLI commands
│   └── web/                # Desktop Web GUI (HTML5, CSS3, ES modules)
├── tests/                  # Automated unit, integration, and CLI tests
├── packaging/
│   ├── windows/            # PyInstaller spec & Inno Setup scripts
│   └── linux/              # install.sh, uninstall.sh, morphix.desktop
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 6. Testing

Morphix includes an automated test suite verifying:
- Magic signature byte detection & extension mismatch alerts
- Central capability registry lookups
- Real image conversions (PNG, JPEG, WebP, dimensions, rotation)
- Real audio conversions & LUFS loudness normalization with FFmpeg
- Real PDF page extraction, rotation, and Markdown-to-PDF rendering
- Real spreadsheet & structured data conversions
- CLI commands (`convert`, `batch`, `inspect`, `doctor`, `presets`, `history`)
- Network isolation (100% offline verification blocking external sockets and DNS)

To run the test suite:
```bash
python -m pytest tests/
```

---

## 7. Configuration & Data Locations

Morphix stores settings, persistent history, and logs in platform-standard directories:
- **Windows:**
  - Config & Presets: `%APPDATA%\Morphix\settings.json`, `presets.json`
  - History & Cache: `%LOCALAPPDATA%\Morphix\history.db`, `temp/`, `logs/`
- **Linux:**
  - Config: `~/.config/morphix/settings.json`, `presets.json`
  - Data & History: `~/.local/share/morphix/history.db`, `temp/`, `logs/`

---

## 8. License

Morphix is released under the **MIT License**. All bundled components (Pillow, FFmpeg essentials, pypdf, reportlab, openpyxl) are redistributed under their respective open-source licenses.
