#!/usr/bin/env bash
# ==============================================================================
# Morphix - Universal Offline File Conversion Suite
# One-Click Linux Installer & Environment Setup
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

NO_LAUNCH=0
for arg in "$@"; do
    case "$arg" in
        --no-launch|-n)
            NO_LAUNCH=1
            shift
            ;;
    esac
done

echo ""
echo -e "\033[1;36m======================================================================\033[0m"
echo -e "\033[1;36m   __  __                  _     _       \033[0m"
echo -e "\033[1;36m  |  \/  |___  _ _ _ __  | |_  (_)__ __ \033[0m"
echo -e "\033[1;36m  | |\/| / _ \| '_| '_ \ | ' \ | |\ \ / \033[0m"
echo -e "\033[1;36m  |_|  |_\___/|_| | .__/ |_||_||_|/_\_\ \033[0m"
echo -e "\033[1;36m                  |_|                    \033[0m"
echo -e "\033[1;37m   Morphix - Universal Offline File Conversion Suite\033[0m"
echo -e "\033[0;90m   Linux One-Click Setup & Launcher\033[0m"
echo -e "\033[1;36m======================================================================\033[0m"
echo ""

# -----------------------------------------------------------------------------
# 1. Detect Architecture and Distribution
# -----------------------------------------------------------------------------
ARCH=$(uname -m)
DISTRO="Linux"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="${NAME:-Linux} ${VERSION_ID:-}"
fi
echo -e "\033[1;33m[1/5] Detecting System Environment...\033[0m"
echo "  Architecture : ${ARCH}"
echo "  Distribution : ${DISTRO}"

# -----------------------------------------------------------------------------
# 2. Check Python 3 (>= 3.10)
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[1;33m[2/5] Checking for Python 3 (>= 3.10)...\033[0m"

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "\033[1;31m[ERROR] Python 3 is not installed on this system.\033[0m"
    echo "Please install Python 3 (>= 3.10) using your distribution package manager:"
    if command -v apt-get >/dev/null 2>&1; then
        echo -e "  \033[1;32msudo apt update && sudo apt install -y python3 python3-pip python3-venv ffmpeg\033[0m"
    elif command -v dnf >/dev/null 2>&1; then
        echo -e "  \033[1;32msudo dnf install -y python3 python3-pip ffmpeg\033[0m"
    elif command -v pacman >/dev/null 2>&1; then
        echo -e "  \033[1;32msudo pacman -S python python-pip ffmpeg\033[0m"
    elif command -v zypper >/dev/null 2>&1; then
        echo -e "  \033[1;32msudo zypper install -y python3 python3-pip ffmpeg\033[0m"
    else
        echo "  Install Python 3.10+, pip, and python3-venv."
    fi
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
PY_COMPAT=$(python3 -c "import sys; print(1 if sys.version_info >= (3, 10) else 0)")

if [ "${PY_COMPAT}" != "1" ]; then
    echo -e "\033[1;31m[ERROR] Detected Python ${PY_VER}, but Morphix requires Python >= 3.10.\033[0m"
    exit 1
fi
echo -e "  \033[1;32m[OK] Found Python ${PY_VER}\033[0m"

# Verify python3 -m venv support (common Debian/Ubuntu gotcha where python3-venv is separate)
if ! python3 -m venv --help >/dev/null 2>&1; then
    echo -e "\033[1;31m[ERROR] The 'python3-venv' module is missing.\033[0m"
    echo "On Debian/Ubuntu systems, install it with:"
    echo -e "  \033[1;32msudo apt install -y python3-venv\033[0m"
    exit 1
fi

# -----------------------------------------------------------------------------
# 3. Create Isolated Virtual Environment
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[1;33m[3/5] Setting up isolated Python virtual environment...\033[0m"
VENV_DIR="${SCRIPT_DIR}/.venv"

if [ ! -f "${VENV_DIR}/bin/python" ]; then
    echo "  Creating virtual environment in ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
    echo -e "  \033[1;32m[OK] Virtual environment created successfully.\033[0m"
else
    echo -e "  \033[1;32m[OK] Existing virtual environment found.\033[0m"
fi

# -----------------------------------------------------------------------------
# 4. Install Dependencies
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[1;33m[4/5] Installing Morphix dependencies from requirements.txt...\033[0m"
echo "  Upgrading pip..."
"${VENV_DIR}/bin/pip" install --upgrade pip --quiet --disable-pip-version-check

echo "  Installing packages (FastAPI, Uvicorn, Pillow, FFmpeg tools, OpenPyXL, ReportLab)..."
"${VENV_DIR}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt" --disable-pip-version-check

echo "  Registering Morphix package in environment..."
"${VENV_DIR}/bin/pip" install -e "${SCRIPT_DIR}" --no-deps --disable-pip-version-check
echo -e "  \033[1;32m[OK] Dependencies installed and verified.\033[0m"

# -----------------------------------------------------------------------------
# 5. Create Quick Launchers and Desktop Integration
# -----------------------------------------------------------------------------
echo ""
echo -e "\033[1;33m[5/5] Configuring launchers and desktop integration...\033[0m"

# 5.1 Root launcher script
cat << 'EOF' > "${SCRIPT_DIR}/run_morphix.sh"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/.venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Please run ./linux_install.sh first."
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Starting Morphix Web GUI (http://127.0.0.1:7474)..."
    echo "Press Ctrl+C to stop the server."
    exec "${SCRIPT_DIR}/.venv/bin/python" -m app.cli.main serve
else
    exec "${SCRIPT_DIR}/.venv/bin/python" -m app.cli.main "$@"
fi
EOF
chmod +x "${SCRIPT_DIR}/run_morphix.sh"
chmod +x "${SCRIPT_DIR}/linux_install.sh"
echo -e "  \033[1;32m[OK] Created executable launcher: ${SCRIPT_DIR}/run_morphix.sh\033[0m"

# 5.2 User PATH binary in ~/.local/bin/morphix (if directory exists or can be created)
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"
cat << EOF > "${BIN_DIR}/morphix"
#!/usr/bin/env bash
exec "${SCRIPT_DIR}/run_morphix.sh" "\$@"
EOF
chmod +x "${BIN_DIR}/morphix"
echo -e "  \033[1;32m[OK] Registered user CLI command: ${BIN_DIR}/morphix\033[0m"

# 5.3 Desktop Entry
DESKTOP_DIR="${HOME}/.local/share/applications"
mkdir -p "${DESKTOP_DIR}"
cat << EOF > "${DESKTOP_DIR}/morphix.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Morphix
Comment=Universal Offline File Conversion Suite
Exec=${SCRIPT_DIR}/run_morphix.sh
Icon=utilities-system-monitor
Terminal=true
Categories=Utility;AudioVideo;Graphics;Office;
StartupNotify=true
EOF
chmod +x "${DESKTOP_DIR}/morphix.desktop"
echo -e "  \033[1;32m[OK] Registered Desktop Application: ${DESKTOP_DIR}/morphix.desktop\033[0m"

# -----------------------------------------------------------------------------
# Diagnostics & Summary
# -----------------------------------------------------------------------------
echo ""
echo "--- Running Pre-Flight Engine Diagnostics ---"
"${VENV_DIR}/bin/python" -m app.cli.main doctor || true

echo ""
echo -e "\033[1;32m======================================================================\033[0m"
echo -e "\033[1;32m [SUCCESS] Morphix installation completed successfully!\033[0m"
echo ""
echo -e "  - Local Web GUI URL  : \033[1;37mhttp://127.0.0.1:7474\033[0m"
echo -e "  - Everyday Launcher  : \033[1;37m./run_morphix.sh\033[0m"
echo -e "  - Terminal Command   : \033[1;37mmorphix --help\033[0m (via ~/.local/bin)"
echo -e "\033[1;32m======================================================================\033[0m"
echo ""

if [ "${NO_LAUNCH}" -eq 1 ]; then
    echo "Setup finished (--no-launch specified). Start Morphix anytime using ./run_morphix.sh"
    exit 0
fi

echo -e "\033[1;36m[*] Launching Morphix Web GUI in your browser now...\033[0m"
echo "    (Press Ctrl+C in this terminal anytime to stop the server)"
echo ""

exec "${VENV_DIR}/bin/python" -m app.cli.main serve
