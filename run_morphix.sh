#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "${SCRIPT_DIR}/.venv/bin/python" ]; then
    echo "======================================================================"
    echo " [ERROR] Morphix virtual environment not found!"
    echo " Please run './linux_install.sh' first to set up dependencies."
    echo "======================================================================"
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Starting Morphix Web GUI (http://127.0.0.1:7474)..."
    echo "Press Ctrl+C to stop the server."
    exec "${SCRIPT_DIR}/.venv/bin/python" -m app.cli.main serve
else
    exec "${SCRIPT_DIR}/.venv/bin/python" -m app.cli.main "$@"
fi
