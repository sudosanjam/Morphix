"""System diagnostics and environment inspection service."""

import os
import sys
import platform
import shutil
from pathlib import Path
from typing import Dict, Any, List

from app.config import config, VERSION, APP_NAME
from app.core.registry import registry
from app.core.metadata import format_bytes


def run_diagnostics() -> Dict[str, Any]:
    """Execute real diagnostic health checks on host system and engines."""
    # Disk space
    disk_total, disk_used, disk_free = 0, 0, 0
    try:
        usage = shutil.disk_usage(str(config.data_dir))
        disk_total, disk_used, disk_free = usage.total, usage.used, usage.free
    except Exception:
        pass

    # Directory permissions
    temp_writable = os.access(str(config.temp_dir), os.W_OK)
    data_writable = os.access(str(config.data_dir), os.W_OK)
    config_writable = os.access(str(config.config_dir), os.W_OK)

    # Engine statuses
    engine_statuses = registry.get_engine_statuses()

    # Calculate active routes vs total routes
    total_routes = len(registry.routes)
    active_routes = sum(1 for r in registry.routes if r.is_available())

    # Read last 30 lines of log if exists
    log_tail = []
    log_file = config.log_dir / "morphix.log"
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                log_tail = [l.strip() for l in lines[-30:]]
        except Exception:
            pass

    return {
        "app": {
            "name": APP_NAME,
            "version": VERSION,
            "status": "operational",
            "offline_mode": True
        },
        "system": {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count() or 1,
            "python_version": sys.version.split()[0],
            "python_executable": sys.executable
        },
        "storage": {
            "config_dir": str(config.config_dir),
            "data_dir": str(config.data_dir),
            "temp_dir": str(config.temp_dir),
            "log_dir": str(config.log_dir),
            "temp_writable": temp_writable,
            "data_writable": data_writable,
            "disk_free_bytes": disk_free,
            "disk_free_formatted": format_bytes(disk_free),
            "disk_total_formatted": format_bytes(disk_total),
        },
        "capabilities": {
            "total_routes": total_routes,
            "active_routes": active_routes,
            "engines": engine_statuses
        },
        "recent_logs": log_tail
    }
