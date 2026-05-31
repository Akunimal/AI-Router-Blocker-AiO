# -*- coding: utf-8 -*-
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox

from ai_blocker.constants import CURRENT_OS
from ai_blocker.i18n import STRINGS, detect_system_language
from ai_blocker.system_utils import is_admin, relaunch_as_admin
from ai_blocker.ui import AIBlockerApp

def acquire_single_instance_lock():
    if CURRENT_OS == "Windows":
        mutex_name = "Global\\AIBlocker_SingleInstance_Mutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return False, None
        return True, mutex
    else:
        try:
            import fcntl
            lock_file = "/tmp/ai_blocker.lock"
            fp = open(lock_file, "w")
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True, fp
        except (IOError, OSError, ImportError):
            return False, None

def main():
    ok, lock_ref = acquire_single_instance_lock()
    if not ok:
        print("AI Network Blocker is already running.")
        sys.exit(0)

    if not is_admin():
        relaunch_as_admin()

        detected_lang = detect_system_language()
        s = STRINGS[detected_lang]

        root_temp = tk.Tk()
        root_temp.withdraw()
        messagebox.showerror(
            s["admin_required_title"],
            s["admin_required_msg"]
        )
        root_temp.destroy()
        sys.exit(1)

    root = tk.Tk()
    app = AIBlockerApp(root)
    if "--minimized" in sys.argv and CURRENT_OS == "Windows":
        root.withdraw()
    root.mainloop()

if __name__ == "__main__":
    main()
