# Command Line Interface (CLI) Reference

Starting in v1.2.1, AI DevSec Gateway supports a fully headless CLI mode. This allows you to manage blocks, check status, and script routing configurations without launching the Tkinter graphical interface.

---

## Command Syntax

```bash
ai-devsec-gateway [options]
# Or from source:
python ai_blocker.py [options]
```

---

## Available Options

| Option | Argument | Description |
|---|---|---|
| `--block` | `work` \| `personal` \| `free` | Activate system hosts blocking using the specified profile template. |
| `--unblock` | *(None)* | Remove all AI-Block comments and restore normal network access. |
| `--status` | *(None)* | Query the hosts file state and list active editor processes. |
| `--list-backends` | *(None)* | List available network backends and mark experimental ones. |
| `--backend` | `hosts` \| `firewall-redirect` | Select the network backend. Defaults to `hosts`. |
| `--dry-run` | *(None)* | Show the planned backend action without changing hosts or network rules. |
| `-h`, `--help` | *(None)* | Show help menu and list parameters. |

---

## Profile Details

*   **`work`:** Blocks all 38+ domains across all categories (OpenAI, Anthropic, Google, Copilot, etc.). Recommended for enterprise work.
*   **`personal`:** Blocks cloud editors but keeps Copilot-specific categories accessible (custom configuration).
*   **`free`:** Deactivates all categories.

---

## Examples

### Check Current Status
```bash
python ai_blocker.py --status
```
**Output:**
```
Status: PROTECTED (Blocking active)
Blocked domains: 38
Active AI editors detected: Cursor, Cline
```

### Activate Block Headless (Linux/macOS)
```bash
sudo python3 ai_blocker.py --block work
```
**Output:**
```
Block successfully activated!
✓ 38 domains blocked in hosts file.
✓ Closed processes: Cursor, code
✓ DNS cache flushed.
```

### Deactivate Block Headless (Windows)
```bash
python ai_blocker.py --unblock
```
*(Triggers UAC check if not elevated)*
**Output:**
```
Block successfully deactivated!
✓ 38 entries removed from hosts file.
✓ DNS cache flushed.
```

### Inspect Available Backends
```bash
python ai_blocker.py --list-backends
```
**Output:**
```
- hosts: Hosts file redirection to 127.0.0.1 (default backend).
- firewall-redirect [experimental]: Firewall/redirect command backend (experimental, opt-in).
```

### Dry-Run Experimental Firewall Backend
```bash
python ai_blocker.py --backend firewall-redirect --block work --dry-run
```
This prints the planned commands without applying firewall or redirect rules. Use this mode before any experimental backend run.
