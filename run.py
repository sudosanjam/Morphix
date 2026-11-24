"""
Morphix - Universal Media Engine
Launches the local web server and hides the console to the system tray.
Browser opening is handled by the Morphix.exe launcher (Run.cs).
"""

import sys
import uvicorn
from pathlib import Path

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import config


def main():
    host = getattr(config.settings, "server_host", "127.0.0.1")
    port = getattr(config.settings, "server_port", 7474)

    # Hide console to tray immediately — no delays, no browser (Run.cs handles that)
    tray_service = None
    if sys.platform == "win32":
        try:
            from app.services.tray import SystemTrayService
            tray_service = SystemTrayService(host=host, port=port)
            tray_service.start(minimize_console=True)
        except Exception:
            pass

    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
    finally:
        if tray_service:
            try:
                tray_service.stop()
            except Exception:
                pass


if __name__ == "__main__":
    main()
