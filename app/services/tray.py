"""Windows System Tray integration for Morphix.

Provides background tray icon, console minimization/hiding,
quick browser opening, and graceful shutdown controls.
"""

import sys
import os
import time
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Callable

from app.config import config, APP_NAME, VERSION

# Win32 constants
WM_TRAY = 0x8000 + 20  # WM_USER + 20
ID_OPEN_BROWSER = 1001
ID_TOGGLE_CONSOLE = 1002
ID_OPEN_FOLDER = 1003
ID_QUIT = 1004


class SystemTrayService:
    """Manages the Windows notification area (system tray) icon and console minimization."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7474, on_exit: Optional[Callable[[], None]] = None):
        self.host = host
        self.port = port
        self.on_exit = on_exit
        self.console_hwnd = None
        self.console_visible = False
        self.tray_hwnd = None
        self.thread: Optional[threading.Thread] = None
        self._is_running = False
        self._hicon = None

    def start(self, minimize_console: bool = True):
        """Start the system tray icon and optionally hide/minimize the console window."""
        if sys.platform != "win32":
            return

        import ctypes
        try:
            self.console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        except Exception:
            self.console_hwnd = None

        if minimize_console and self.console_hwnd:
            try:
                import win32gui
                import win32con
                # Hide console window from desktop and taskbar
                win32gui.ShowWindow(self.console_hwnd, win32con.SW_HIDE)
                self.console_visible = False
            except Exception:
                pass

        self._is_running = True
        self.thread = threading.Thread(target=self._run_tray_loop, name="morphix-tray", daemon=True)
        self.thread.start()

    def stop(self):
        """Remove the tray icon and restore the console if running."""
        self._is_running = False
        if sys.platform != "win32" or not self.tray_hwnd:
            return

        try:
            import win32gui
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.tray_hwnd, 0))
            win32gui.PostMessage(self.tray_hwnd, win32gui.WM_CLOSE, 0, 0)
        except Exception:
            pass

        # If console was hidden, restore it on shutdown
        if self.console_hwnd and not self.console_visible:
            try:
                import win32gui
                import win32con
                win32gui.ShowWindow(self.console_hwnd, win32con.SW_SHOW)
                self.console_visible = True
            except Exception:
                pass

    def _run_tray_loop(self):
        try:
            import win32gui
            import win32con
            import win32api
        except ImportError:
            return

        class_name = f"MorphixTrayWnd_{os.getpid()}"
        wc = win32gui.WNDCLASS()
        hinst = win32gui.GetModuleHandle(None)
        wc.hInstance = hinst
        wc.lpszClassName = class_name
        wc.lpfnWndProc = self._wndproc

        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass

        self.tray_hwnd = win32gui.CreateWindowEx(
            0, class_name, "Morphix Tray",
            0, 0, 0, 0, 0,
            0, 0, hinst, None
        )

        # Locate .ico icon
        ico_path = Path(__file__).resolve().parent.parent / "web" / "assets" / "morphix.ico"
        if not ico_path.exists():
            # Fallback to default application icon
            self._hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        else:
            try:
                self._hicon = win32gui.LoadImage(
                    0, str(ico_path), win32con.IMAGE_ICON, 16, 16,
                    win32con.LR_LOADFROMFILE
                )
            except Exception:
                self._hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        tooltip = f"{APP_NAME} — Offline File Conversion ({self.host}:{self.port})"
        nid = (self.tray_hwnd, 0, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP, WM_TRAY, self._hicon, tooltip)

        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except Exception:
            # Taskbar not available (e.g. headless/service session)
            return

        # Message pump
        win32gui.PumpMessages()

    def _wndproc(self, hwnd, msg, wparam, lparam):
        import win32gui
        import win32con

        if msg == WM_TRAY:
            if lparam in (win32con.WM_LBUTTONUP, win32con.WM_LBUTTONDBLCLK):
                # Open browser
                webbrowser.open(f"http://{self.host}:{self.port}")
                return 0
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_context_menu(hwnd)
                return 0

        elif msg == win32con.WM_COMMAND:
            cmd_id = win32gui.LOWORD(wparam)
            if cmd_id == ID_OPEN_BROWSER:
                webbrowser.open(f"http://{self.host}:{self.port}")
            elif cmd_id == ID_TOGGLE_CONSOLE:
                self._toggle_console()
            elif cmd_id == ID_OPEN_FOLDER:
                self._open_output_folder()
            elif cmd_id == ID_QUIT:
                self._quit_application()
            return 0

        elif msg == win32con.WM_DESTROY:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 0))
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_context_menu(self, hwnd):
        import win32gui
        import win32con

        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_DEFAULT, ID_OPEN_BROWSER, "Open Morphix (Browser)")
        
        console_text = "Show Console Window" if not self.console_visible else "Hide Console Window"
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_TOGGLE_CONSOLE, console_text)
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_OPEN_FOLDER, "Open Output Folder")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, ID_QUIT, "Exit Morphix")

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN | win32con.TPM_BOTTOMALIGN, pos[0], pos[1], 0, hwnd, None)
        win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)

    def _toggle_console(self):
        if not self.console_hwnd:
            return
        import win32gui
        import win32con

        if self.console_visible:
            win32gui.ShowWindow(self.console_hwnd, win32con.SW_HIDE)
            self.console_visible = False
        else:
            win32gui.ShowWindow(self.console_hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(self.console_hwnd)
            self.console_visible = True

    def _open_output_folder(self):
        try:
            folder = config.settings.default_output_dir or config.temp_dir
            target = Path(folder).resolve()
            target.mkdir(parents=True, exist_ok=True)
            os.startfile(str(target))
        except Exception:
            pass

    def _quit_application(self):
        self.stop()
        if self.on_exit:
            try:
                self.on_exit()
            except Exception:
                pass
        import signal
        os.kill(os.getpid(), signal.SIGINT)
