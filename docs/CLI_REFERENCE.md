# Morphix CLI Reference

Command line interface reference for `morphix`.

---

## Commands Summary

- `morphix convert`: Convert a single file with optional format-specific parameters.
- `morphix batch`: Convert all matching files in a folder with batch concurrency.
- `morphix inspect`: Inspect format, dimensions, streams, and properties of any file.
- `morphix formats`: List all supported formats or targets for a specific input file.
- `morphix preset`: View, show, or apply conversion presets.
- `morphix history`: View or clear persistent conversion history.
- `morphix doctor`: Run real system diagnostics, engine verification, and permission checks.
- `morphix serve`: Launch local offline web GUI server.
- `morphix --version`: Show version and exit.
- `morphix --help`: Show help instructions.

---

## 1. `morphix convert`

Convert a single file with optional format-specific parameters.

### Syntax:
```bash
morphix convert [OPTIONS] SOURCE_FILE
```

### Arguments:
- `SOURCE_FILE`: Path to the source file to convert (required, relative or absolute).

### Options:
- `-t, --to TEXT`: Target output format (required, e.g. `webp`, `mp3`, `pdf`, `csv`).
- `-o, --output PATH`: Target output file or destination directory.
- `-p, --preset TEXT`: Apply a pre-configured preset (e.g. `web_image`, `podcast_audio`).
- `-q, --quality INTEGER`: Quality (1–100) for lossy images and audio.
- `-w, --width INTEGER`: Target width in pixels (images).
- `-h, --height INTEGER`: Target height in pixels (images).
- `-b, --bitrate TEXT`: Audio bitrate (e.g. `128k`, `192k`, `320k`).
- `--sample-rate INTEGER`: Audio sample rate in Hz (e.g. `44100`, `48000`).
- `--channels TEXT`: Audio channels (`mono`, `stereo`, `preserve`).
- `--loudnorm`: Apply EBU R128 loudness normalization.
- `--overwrite`: Overwrite existing output files instead of auto-renaming.
- `--json`: Output machine-readable JSON result.

### Examples:
```bash
morphix convert image.png --to webp --quality 85
morphix convert photo.jpg --to webp --width 1280 --height 720
morphix convert episode.wav --to mp3 --bitrate 192k --loudnorm
morphix convert notes.md --to pdf --output ./notes.pdf
morphix convert table.xlsx --to csv --output ./table.csv
```

---

## 2. `morphix batch`

Batch convert all matching files in a directory.

### Syntax:
```bash
morphix batch [OPTIONS] SOURCE_DIR
```

### Options:
- `-t, --to TEXT`: Target output format (required).
- `-o, --output PATH`: Target output directory.
- `-r, --recursive`: Traverse subdirectories recursively.
- `--pattern TEXT`: Filename pattern to match (default: `*`, e.g. `*.png`).
- `--overwrite`: Overwrite existing files.
- `--json`: Output machine-readable JSON summary.

---

## 3. `morphix inspect`

Deep inspect file metadata, dimensions, audio streams, bitrates, and headers.

### Syntax:
```bash
morphix inspect FILE_PATH [--json]
```

---

## 4. `morphix doctor`

Run real system diagnostics, engine verification, and permission checks.

### Syntax:
```bash
morphix doctor [--json]
```

---

## 5. `morphix serve`

Launch the local offline web GUI server.

### Syntax:
```bash
morphix serve [--host 127.0.0.1] [--port 7474] [--no-open-browser]
```
