# -*- coding: utf-8 -*-
__version__ = "1.2.1"
APP_VERSION = __version__

# Expose everything to maintain backwards compatibility and test stability
from ai_blocker.config import (
    SENSITIVE_CONFIG_KEYS, get_config_path,
    load_config, save_config, set_windows_autostart, get_windows_autostart
)

from ai_blocker.constants import (
    CURRENT_OS, BLOCKLIST, CATEGORY_ICONS, PROCESS_LIST, COMMENT_TAG, HOSTS_PATH,
    COL_BASE, COL_SURFACE0, COL_SURFACE1, COL_TEXT, COL_SUBTEXT, COL_RED,
    COL_GREEN, COL_YELLOW, COL_BLUE, COL_MAUVE, UI_FONT, _get_ui_font
)

from ai_blocker.i18n import (
    LANG_DISPLAY_MAP, LANG_CODE_MAP, CATEGORY_TRANSLATIONS, STRINGS,
    load_translations, detect_system_language
)

from ai_blocker.system_utils import (
    is_admin, relaunch_as_admin, _get_subprocess_kwargs, flush_dns,
    count_total_domains, get_hosts_status
)

from ai_blocker.block_actions import (
    force_close_processes, detect_running_ai_editors, activate_block, deactivate_block
)

from ai_blocker.gateway import GatewayHandler

from ai_blocker.ui import AIBlockerApp

if CURRENT_OS == "Windows":
    from ai_blocker.tray import WindowsTrayIcon
