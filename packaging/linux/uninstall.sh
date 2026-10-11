#!/usr/bin/env bash
# Morphix Safe Linux Uninstaller

set -e

APP_NAME="morphix"
INSTALL_DIR="${HOME}/.local/share/${APP_NAME}"
BIN_FILE="${HOME}/.local/bin/morphix"
DESKTOP_FILE="${HOME}/.local/share/applications/morphix.desktop"
ICON_FILE="${HOME}/.local/share/icons/hicolor/scalable/apps/morphix.svg"
CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/${APP_NAME}"

echo "=========================================================="
echo " Morphix Uninstaller"
echo "=========================================================="

echo "[INFO] Removing launcher and shortcuts..."
rm -f "${BIN_FILE}"
rm -f "${DESKTOP_FILE}"
rm -f "${ICON_FILE}"

echo "[INFO] Removing application binaries from ${INSTALL_DIR}..."
rm -rf "${INSTALL_DIR}"

read -p "Do you also want to remove your saved presets and configuration in ${CONFIG_DIR}? [y/N]: " REMOVE_CONFIG
if [[ "$REMOVE_CONFIG" =~ ^[Yy]$ ]]; then
    rm -rf "${CONFIG_DIR}"
    echo "[INFO] Configuration and presets removed."
else
    echo "[INFO] Presets and configuration preserved in ${CONFIG_DIR}."
fi

echo "[SUCCESS] Morphix has been successfully uninstalled from your system."
