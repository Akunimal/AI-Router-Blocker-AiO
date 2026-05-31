# -*- coding: utf-8 -*-
import os
import threading
from typing import Any

from ai_blocker.constants import CURRENT_OS

_tray_icon_class: type[Any]

if CURRENT_OS == "Windows":
    import ctypes
    from ctypes import wintypes

    WM_USER = 1024
    WM_TRAYICON = WM_USER + 20
    NIM_ADD = 0
    NIM_MODIFY = 1
    NIM_DELETE = 2
    NIF_ICON = 2
    NIF_MESSAGE = 1
    NIF_TIP = 4
    WM_LBUTTONDBLCLK = 515
    WM_RBUTTONUP = 517
    WM_DESTROY = 2

    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uID", wintypes.UINT),
            ("uFlags", wintypes.UINT),
            ("uCallbackMessage", wintypes.UINT),
            ("hIcon", wintypes.HICON),
            ("szTip", ctypes.c_wchar * 128),
            ("dwState", wintypes.DWORD),
            ("dwStateMask", wintypes.DWORD),
            ("szInfo", ctypes.c_wchar * 256),
            ("uTimeout", wintypes.UINT),
            ("szInfoTitle", ctypes.c_wchar * 64),
            ("dwInfoFlags", wintypes.DWORD),
            ("guidItem", ctypes.c_byte * 16),
            ("hBalloonIcon", wintypes.HICON),
        ]

    class _WindowsTrayIconImpl:
        def __init__(self, app):
            self.app = app
            self.hwnd = None
            self.tip = "AI Network Blocker"
            self._added = False

            # Start message loop in a daemon thread
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

        def _run_loop(self):
            WndProcType = ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

            @WndProcType
            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == WM_TRAYICON:
                    if lparam == WM_LBUTTONDBLCLK:
                        self.app.root.after(0, self.app.show_window)
                    elif lparam == WM_RBUTTONUP:
                        self.app.root.after(0, self.app.show_tray_menu)
                    return 0
                elif msg == WM_DESTROY:
                    user32.PostQuitMessage(0)
                    return 0
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

            self.wnd_proc_ref = wnd_proc  # Keep reference

            hinstance = kernel32.GetModuleHandleW(None)
            class_name = "AIBlockerTrayClass"

            wndclass = WNDCLASSW()
            wndclass.style = 0
            wndclass.lpfnWndProc = wnd_proc
            wndclass.cbClsExtra = 0
            wndclass.cbWndExtra = 0
            wndclass.hInstance = hinstance
            wndclass.hIcon = 0
            wndclass.hCursor = 0
            wndclass.hbrBackground = 0
            wndclass.lpszMenuName = None
            wndclass.lpszClassName = class_name

            user32.RegisterClassW(ctypes.byref(wndclass))

            self.hwnd = user32.CreateWindowExW(
                0, class_name, "AI Blocker Tray Window",
                0, 0, 0, 0, 0,
                0, 0, hinstance, None
            )

            self.update_icon()

            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        def update_icon(self):
            if not self.hwnd:
                return

            # Try to load state-specific icon
            if self.app.is_blocked:
                icon_name = "icon_green.ico"
            else:
                icon_name = "icon_red.ico"

            # Check inside package folder first, then parent directory (where raw script runs)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, icon_name)
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.path.dirname(base_dir), icon_name)
            if not os.path.exists(icon_path):
                icon_path = os.path.join(base_dir, "icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(os.path.dirname(base_dir), "icon.ico")

            hicon = 0
            if os.path.exists(icon_path):
                hicon = user32.LoadImageW(
                    0, icon_path, 1, 0, 0, 16 | 80  # IMAGE_ICON, LR_LOADFROMFILE | LR_DEFAULTSIZE
                )

            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd = self.hwnd
            nid.uID = 1
            nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP
            nid.uCallbackMessage = WM_TRAYICON
            nid.hIcon = hicon
            nid.szTip = self.tip

            if self._added:
                shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
            else:
                shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
                self._added = True

        def remove(self):
            if self.hwnd and self._added:
                nid = NOTIFYICONDATAW()
                nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
                nid.hWnd = self.hwnd
                nid.uID = 1
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                self._added = False

    _tray_icon_class = _WindowsTrayIconImpl

else:
    # Stub implementation for non-Windows platforms
    class _WindowsTrayIconStub:
        def __init__(self, app):
            pass
        def update_icon(self):
            pass
        def remove(self):
            pass

    _tray_icon_class = _WindowsTrayIconStub

WindowsTrayIcon = _tray_icon_class
