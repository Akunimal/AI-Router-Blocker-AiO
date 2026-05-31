import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
import argparse

from ai_blocker.constants import CURRENT_OS
from ai_blocker.i18n import STRINGS, detect_system_language
from ai_blocker.system_utils import is_admin, relaunch_as_admin, get_hosts_status
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
    parser = argparse.ArgumentParser(description="AI Network Blocker & DevSec Gateway CLI")
    parser.add_argument("--block", choices=["work", "personal", "free"], help="Activate blocking for the specified profile")
    parser.add_argument("--unblock", action="store_true", help="Deactivate all AI domain blocks")
    parser.add_argument("--status", action="store_true", help="Show current blocking status and active editors")
    
    args, unknown = parser.parse_known_args()

    # CLI execution path
    if args.block or args.unblock or args.status:
        if args.status:
            is_blocked, count = get_hosts_status()
            print(f"Status: {'PROTECTED (Blocking active)' if is_blocked else 'EXPOSED (No protection)'}")
            print(f"Blocked domains: {count}")
            
            from ai_blocker.block_actions import detect_running_ai_editors
            editors = detect_running_ai_editors()
            if editors:
                print(f"Active AI editors detected: {', '.join(editors)}")
            else:
                print("No active AI editors detected.")
            sys.exit(0)

        # For block/unblock, verify admin privileges
        if not is_admin():
            print("Error: Administrator/root privileges are required for this action.")
            if CURRENT_OS == "Windows":
                print("Requesting Administrator elevation...")
                relaunch_as_admin()
            sys.exit(1)

        from ai_blocker.block_actions import activate_block, deactivate_block

        if args.unblock:
            ok, msg = deactivate_block("en")
            print(msg.strip())
            sys.exit(0 if ok else 1)

        if args.block:
            from ai_blocker.constants import BLOCKLIST
            if args.block == "work":
                cats = list(BLOCKLIST.keys())
            elif args.block == "personal":
                cats = [c for c in BLOCKLIST.keys() if "copilot" in c.lower()]
            else: # free
                cats = []

            if not cats:
                ok, msg = deactivate_block("en")
            else:
                ok, msg = activate_block("en", cats)
            print(msg.strip())
            sys.exit(0 if ok else 1)

    # GUI execution path
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
