import argparse
import ctypes
import sys

from ai_blocker.constants import CURRENT_OS
from ai_blocker.network_backends import list_network_backends
from ai_blocker.system_utils import get_hosts_status, is_admin, relaunch_as_admin


def acquire_single_instance_lock():
    if CURRENT_OS == "Windows":
        mutex_name = "Global\\AIDevSecGateway_SingleInstance_Mutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return False, None
        return True, mutex
    else:
        try:
            import fcntl
            lock_file = "/tmp/ai_devsec_gateway.lock"
            fp = open(lock_file, "w")
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True, fp
        except (IOError, OSError, ImportError):
            return False, None

def main():
    parser = argparse.ArgumentParser(description="AI DevSec Gateway CLI")
    parser.add_argument("--block", choices=["work", "personal", "free"], help="Activate blocking for the specified profile")
    parser.add_argument("--unblock", action="store_true", help="Deactivate all AI domain blocks")
    parser.add_argument("--status", action="store_true", help="Show current blocking status and active editors")
    parser.add_argument("--list-backends", action="store_true", help="List available network backends")
    parser.add_argument("--backend", choices=["hosts", "firewall-redirect"], default="hosts", help="Select network backend")
    parser.add_argument("--dry-run", action="store_true", help="Show planned actions without applying changes")
    parser.add_argument("--dlp", action="store_true", default=True, help="Enable DLP content inspection (default: enabled)")
    parser.add_argument("--guardrails", action="store_true", default=True, help="Enable prompt guardrails (default: enabled)")
    parser.add_argument("--no-dlp", action="store_true", help="Disable DLP content inspection")
    parser.add_argument("--no-guardrails", action="store_true", help="Disable prompt guardrails")

    args, unknown = parser.parse_known_args()

    # CLI execution path
    if args.list_backends:
        for backend in list_network_backends():
            suffix = " [experimental]" if backend.experimental else ""
            print(f"- {backend.name}{suffix}: {backend.description}")
        sys.exit(0)

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

        # Dry-run must be inspectable without elevated privileges.
        if not args.dry_run and not is_admin():
            print("Error: Administrator/root privileges are required for this action.")
            if CURRENT_OS == "Windows":
                print("Requesting Administrator elevation...")
                relaunch_as_admin()
            sys.exit(1)

        from ai_blocker.block_actions import activate_block, deactivate_block

        if args.unblock:
            ok, msg = deactivate_block("en", backend_name=args.backend, dry_run=args.dry_run)
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
                ok, msg = deactivate_block("en", backend_name=args.backend, dry_run=args.dry_run)
            else:
                ok, msg = activate_block("en", cats, backend_name=args.backend, dry_run=args.dry_run)
            print(msg.strip())
            sys.exit(0 if ok else 1)

    # GUI execution path
    ok, lock_ref = acquire_single_instance_lock()
    if not ok:
        print("AI DevSec Gateway is already running.")
        sys.exit(0)

    if not is_admin():
        relaunch_as_admin()
        sys.exit(0)

    import tkinter as tk

    from ai_blocker.ui import AIBlockerApp

    root = tk.Tk()
    AIBlockerApp(root)
    if "--minimized" in sys.argv and CURRENT_OS == "Windows":
        root.withdraw()
    root.mainloop()

if __name__ == "__main__":
    main()
