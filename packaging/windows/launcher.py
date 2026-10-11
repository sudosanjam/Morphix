"""Morphix Unified Desktop & CLI Launcher for Packaged Distribution."""

import sys
import os

# Ensure package root is in sys.path
sys.path.insert(0, os.path.abspath("."))

def main():
    # If launched with command line arguments (e.g. morphix convert, morphix doctor), run Typer CLI
    if len(sys.argv) > 1 and sys.argv[1] not in ("--gui", "serve"):
        from app.cli.main import app
        app()
    else:
        # Default desktop action: launch server and open GUI in browser
        from app.cli.main import serve_cmd
        serve_cmd(host="127.0.0.1", port=7474, open_browser=True)

if __name__ == "__main__":
    main()
