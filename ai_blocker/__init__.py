# -*- coding: utf-8 -*-
# ruff: noqa: F401
__version__ = "1.3.2"
APP_VERSION = __version__

# Expose everything to maintain backwards compatibility and test stability
from ai_blocker.block_actions import activate_block, deactivate_block, detect_running_ai_editors, force_close_processes
from ai_blocker.config import (
    SENSITIVE_CONFIG_KEYS,
    get_config_path,
    get_windows_autostart,
    load_config,
    save_config,
    set_windows_autostart,
)
from ai_blocker.constants import (
    BLOCKLIST,
    CATEGORY_ICONS,
    COL_BASE,
    COL_BLUE,
    COL_GREEN,
    COL_MAUVE,
    COL_RED,
    COL_SUBTEXT,
    COL_SURFACE0,
    COL_SURFACE1,
    COL_TEXT,
    COL_YELLOW,
    COMMENT_TAG,
    CURRENT_OS,
    HOSTS_PATH,
    PROCESS_LIST,
    UI_FONT,
    _get_ui_font,
)
from ai_blocker.gateway import GatewayHandler
from ai_blocker.i18n import (
    CATEGORY_TRANSLATIONS,
    LANG_CODE_MAP,
    LANG_DISPLAY_MAP,
    STRINGS,
    detect_system_language,
    load_translations,
)
from ai_blocker.network_backends import (
    BackendResult,
    FirewallRedirectBackend,
    HostsBackend,
    NetworkBackend,
    get_network_backend,
)
from ai_blocker.system_utils import (
    _get_subprocess_kwargs,
    count_total_domains,
    flush_dns,
    get_hosts_status,
    is_admin,
    relaunch_as_admin,
)
from ai_blocker.ui import AIBlockerApp

if CURRENT_OS == "Windows":
    from ai_blocker.tray import WindowsTrayIcon
