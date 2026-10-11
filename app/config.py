"""Morphix configuration management and platform-specific path resolution."""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

APP_NAME = "Morphix"
VERSION = "1.0.0"


def get_default_config_dir() -> Path:
    """Return platform-appropriate configuration directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / f".{APP_NAME.lower()}"
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / APP_NAME.lower()
        return Path.home() / ".config" / APP_NAME.lower()


def get_default_data_dir() -> Path:
    """Return platform-appropriate application data directory."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
        return get_default_config_dir()
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / APP_NAME.lower()
        return Path.home() / ".local" / "share" / APP_NAME.lower()


def get_default_cache_dir() -> Path:
    """Return platform-appropriate cache/temp directory."""
    data_dir = get_default_data_dir()
    return data_dir / "cache"


class AppSettings(BaseModel):
    """User-configurable application settings."""
    theme: str = Field(default="dark", description="'dark' or 'light'")
    default_output_dir: Optional[str] = Field(default=None, description="Default destination folder for converted files")
    overwrite_policy: str = Field(default="rename", description="'rename', 'overwrite', or 'skip'")
    max_workers: int = Field(default_factory=lambda: max(2, min(8, (os.cpu_count() or 4))), description="Concurrency limit")
    history_retention_days: int = Field(default=30, description="Number of days to keep conversion history")
    server_host: str = Field(default="127.0.0.1", description="Local web GUI bind host")
    server_port: int = Field(default=7474, description="Local web GUI port")
    log_level: str = Field(default="INFO", description="Logging level")
    custom_ffmpeg_path: Optional[str] = Field(default=None, description="Custom path to ffmpeg executable")
    custom_pandoc_path: Optional[str] = Field(default=None, description="Custom path to pandoc executable")
    custom_libreoffice_path: Optional[str] = Field(default=None, description="Custom path to soffice executable")


class ConfigManager:
    """Manages application paths, settings persistence, and logging."""

    def __init__(self, config_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.config_dir = (config_dir or get_default_config_dir()).resolve()
        self.data_dir = (data_dir or get_default_data_dir()).resolve()
        self.cache_dir = self.data_dir / "cache"
        self.temp_dir = self.data_dir / "temp"
        self.log_dir = self.data_dir / "logs"

        # Ensure essential directories exist
        for d in [self.config_dir, self.data_dir, self.cache_dir, self.temp_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.config_dir / "settings.json"
        self.presets_file = self.config_dir / "presets.json"
        self.history_db = self.data_dir / "history.db"
        self.settings: AppSettings = self.load_settings()

    def load_settings(self) -> AppSettings:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AppSettings(**data)
            except Exception as e:
                logging.getLogger("morphix").warning(f"Failed to read settings from {self.settings_file}: {e}")
        return AppSettings()

    def save_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        with open(self.settings_file, "w", encoding="utf-8") as f:
            f.write(self.settings.model_dump_json(indent=2))

    def update_settings(self, updates: Dict[str, Any]) -> AppSettings:
        curr = self.settings.model_dump()
        curr.update(updates)
        self.settings = AppSettings(**curr)
        self.save_settings(self.settings)
        return self.settings

    def clean_temp_files(self) -> int:
        """Clean all temporary files generated during conversions."""
        count = 0
        if self.temp_dir.exists():
            for item in self.temp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        count += 1
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item, ignore_errors=True)
                        count += 1
                except Exception:
                    pass
        return count


# Singleton instance
config = ConfigManager()


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Configure structured local logging."""
    logger = logging.getLogger("morphix")
    level_name = log_level or config.settings.log_level
    numeric_level = getattr(logging, level_name.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler
        log_file = config.log_dir / "morphix.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(numeric_level)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(numeric_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger
