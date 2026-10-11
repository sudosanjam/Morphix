# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys
import os

block_cipher = None

workspace_dir = Path(os.path.abspath(".")).resolve()
web_dir = workspace_dir / "app" / "web"

datas = [
    (str(web_dir), os.path.join("app", "web")),
]

# Check if imageio_ffmpeg has binaries
try:
    import imageio_ffmpeg
    ffmpeg_bin = Path(imageio_ffmpeg.get_ffmpeg_exe()).parent
    if ffmpeg_bin.exists():
        datas.append((str(ffmpeg_bin), os.path.join("imageio_ffmpeg", "binaries")))
except Exception:
    pass

hidden_imports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "PIL",
    "PIL.Image",
    "pypdf",
    "reportlab",
    "openpyxl",
    "yaml",
    "markdown",
    "defusedxml",
    "typer",
    "rich",
    "rich.console",
    "rich.table",
    "rich.progress",
    "sqlite3",
    "email.mime.text",
    "email.mime.multipart",
]

launcher_script = str(workspace_dir / "packaging" / "windows" / "launcher.py")

a = Analysis(
    [launcher_script],
    pathex=[str(workspace_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='morphix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Morphix',
)
