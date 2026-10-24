"""Unit tests for Windows system tray service."""

import sys
import pytest
from app.services.tray import SystemTrayService


def test_tray_initialization():
    service = SystemTrayService(host="127.0.0.1", port=7474)
    assert service.host == "127.0.0.1"
    assert service.port == 7474
    assert service.console_visible is False


def test_tray_start_and_stop():
    service = SystemTrayService(host="127.0.0.1", port=7474)
    # Start with minimize_console=False to avoid affecting test runner console
    service.start(minimize_console=False)
    # Give thread a moment
    import time
    time.sleep(0.1)
    service.stop()
    assert service._is_running is False
