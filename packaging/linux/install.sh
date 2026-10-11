#!/usr/bin/env bash
# Morphix - Universal Offline File Conversion Suite
# One-command Per-User Linux Setup Script

set -e

APP_NAME="morphix"
APP_DISPLAY_NAME="Morphix"
VERSION="1.0.0"

INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"
CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/${APP_NAME}"

echo "=========================================================="
echo " ${APP_DISPLAY_NAME} v${VERSION} — Offline Linux Installation"
echo "=========================================================="

# 1. Architecture and environment detection
ARCH=$(uname -m)
echo "[INFO] Detected Architecture: ${ARCH}"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "[INFO] Detected Distribution: ${NAME} ${VERSION_ID:-}"
fi

# 2. Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3 is required. Please install python3 (>= 3.10) using your package manager."
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[INFO] Detected Python Version: ${PY_VER}"

# 3. Create destination directories
mkdir -p "${INSTALL_DIR}"
mkdir -p "${BIN_DIR}"
mkdir -p "${DESKTOP_DIR}"
mkdir -p "${ICON_DIR}"
mkdir -p "${CONFIG_DIR}"

# 4. Copy application source and assets
echo "[INFO] Installing application files to ${INSTALL_DIR}..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Copy app, requirements, pyproject
cp -r "${ROOT_DIR}/app" "${INSTALL_DIR}/"
cp "${ROOT_DIR}/pyproject.toml" "${INSTALL_DIR}/"
cp "${ROOT_DIR}/requirements.txt" "${INSTALL_DIR}/"

# 5. Setup Python virtual environment
echo "[INFO] Configuring isolated Python runtime in ${INSTALL_DIR}/venv..."
if [ ! -d "${INSTALL_DIR}/venv" ]; then
    python3 -m venv "${INSTALL_DIR}/venv"
fi

# Check for offline wheels directory in bundle
if [ -d "${SCRIPT_DIR}/wheels" ]; then
    echo "[INFO] Installing from offline wheels bundle (Zero internet required)..."
    "${INSTALL_DIR}/venv/bin/pip" install --no-index --find-links="${SCRIPT_DIR}/wheels" -r "${INSTALL_DIR}/requirements.txt"
else
    echo "[INFO] Installing Python dependencies into isolated venv..."
    "${INSTALL_DIR}/venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"
fi

# 6. Create CLI launcher script
echo "[INFO] Creating 'morphix' CLI executable in ${BIN_DIR}/morphix..."
cat << 'EOF' > "${BIN_DIR}/morphix"
#!/usr/bin/env bash
INSTALL_DIR="${HOME}/.local/share/morphix"
exec "${INSTALL_DIR}/venv/bin/python" -m app.cli.main "$@"
EOF
chmod +x "${BIN_DIR}/morphix"

# 7. Create Desktop Launcher
echo "[INFO] Registering Desktop Application Launcher..."
cat << EOF > "${DESKTOP_DIR}/morphix.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Morphix
Comment=Universal Offline File Conversion Suite
Exec=${BIN_DIR}/morphix serve --no-open-browser
Icon=morphix
Terminal=false
Categories=Utility;AudioVideo;Graphics;Office;
StartupNotify=true
EOF
chmod +x "${DESKTOP_DIR}/morphix.desktop"

# Copy logo SVG as system icon
if [ -f "${ROOT_DIR}/app/web/index.html" ]; then
    cat << 'EOF' > "${ICON_DIR}/morphix.svg"
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
  <polyline points="2 17 12 22 22 17"></polyline>
  <polyline points="2 12 12 17 22 12"></polyline>
</svg>
EOF
fi

# 8. Check Optional System Engines
echo ""
echo "--- Checking Conversion Engines ---"
if command -v ffmpeg >/dev/null 2>&1; then
    echo "  [OK] System FFmpeg detected: $(ffmpeg -version | head -n 1)"
else
    echo "  [INFO] System FFmpeg not found (Using bundled Python audio tools or install with: sudo apt install ffmpeg)"
fi

if command -v soffice >/dev/null 2>&1; then
    echo "  [OK] LibreOffice detected (Headless office conversion ready)"
else
    echo "  [INFO] LibreOffice not installed (Install 'libreoffice' for DOCX/PPTX to PDF support)"
fi

if command -v pandoc >/dev/null 2>&1; then
    echo "  [OK] Pandoc detected: $(pandoc --version | head -n 1)"
else
    echo "  [INFO] Pandoc not installed (Install 'pandoc' for advanced document formats)"
fi

# 9. PATH check
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "[NOTE] ${BIN_DIR} is not in your current PATH."
    echo "To run 'morphix' directly from any terminal, add this to your ~/.bashrc or ~/.zshrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "=========================================================="
echo " ${APP_DISPLAY_NAME} Installation Complete!"
echo " - Run GUI: ${BIN_DIR}/morphix serve"
echo " - Run CLI: ${BIN_DIR}/morphix --help"
echo " - Run Diagnostics: ${BIN_DIR}/morphix doctor"
echo "=========================================================="
