# Morphix Packaging & Distribution Guide

Morphix is designed for offline desktop deployment on **Windows 10/11** and **Linux** without requiring users to configure developer environments or virtual environments manually.

---

## 1. Windows Packaging

Windows builds can be packaged into two formats:
1. **One-Click Installer:** `Morphix-Setup.exe` (using PyInstaller + Inno Setup)
2. **Portable Distribution:** `Morphix-v1.0.0-windows-x64.zip` with `run_morphix.bat` and `morphix.bat`.

### Building the Windows Package:
Run the build script:
```powershell
python packaging/windows/build_windows_installer.py
```
Or double-click `packaging\windows\build_windows_installer.bat`.

### Build Pipeline Stages:
1. **PyInstaller:** Packages the Python runtime, all libraries, and bundled FFmpeg binaries into `dist/Morphix/`.
2. **Asset Bundling:** Automatically includes `app/web/` (HTML, CSS, JS) and required metadata.
3. **Inno Setup:** If Inno Setup 6 (`ISCC.exe`) is installed, compiles `dist/Morphix-Setup.exe`.
4. **Portable Zip:** Generates `dist/Morphix-v1.0.0-windows-x64.zip`.

### Installer Specifications:
- Per-user installation (`PrivilegesRequired=lowest`).
- Adds Morphix to the User `PATH` environment variable so `morphix` can be run in PowerShell or CMD.
- Creates Start Menu shortcut and optional Desktop icon.
- Uninstaller preserves user conversion history and presets unless explicitly selected.

---

## 2. Linux Packaging

Linux distribution is handled via:
1. **One-Command Installer:** `install.sh`
2. **Offline Bundle:** `morphix-v1.0.0-linux-offline.tar.gz`

### Creating the Offline Linux Bundle:
```bash
python packaging/linux/create_offline_bundle.py
```
Produces `dist/morphix-v1.0.0-linux-offline.tar.gz`.

### Installing on Linux:
```bash
tar -xzf morphix-v1.0.0-linux-offline.tar.gz
cd morphix
chmod +x install.sh
./install.sh
```

### Installation Details:
- Isolated per-user installation in `~/.local/share/morphix`.
- CLI launcher registered in `~/.local/bin/morphix`.
- Desktop entry registered in `~/.local/share/applications/morphix.desktop`.
- Icon installed in `~/.local/share/icons/hicolor/scalable/apps/morphix.svg`.
- No root / `sudo` privileges required.
- Safe uninstallation script provided: `uninstall.sh`.
