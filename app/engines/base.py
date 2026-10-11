"""Base engine abstraction and status reporting."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class EngineCapability(ABC):
    """Abstract base class for all conversion engines in Morphix."""

    name: str = "base"
    display_name: str = "Base Engine"

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if engine runtime or binary is detected and operational."""
        pass

    @classmethod
    @abstractmethod
    def get_version(cls) -> Optional[str]:
        """Return detected engine version string or None."""
        pass

    @classmethod
    @abstractmethod
    def get_binary_path(cls) -> Optional[str]:
        """Return path to executable if external binary, or 'bundled-python'."""
        pass

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Return comprehensive engine status dict."""
        avail = cls.is_available()
        return {
            "name": cls.name,
            "display_name": cls.display_name,
            "available": avail,
            "version": cls.get_version() if avail else None,
            "path": cls.get_binary_path() if avail else None,
        }
