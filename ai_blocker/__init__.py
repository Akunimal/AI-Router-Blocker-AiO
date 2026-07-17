# -*- coding: utf-8 -*-
# ruff: noqa: F401
__version__ = "1.6.0"
APP_VERSION = __version__
import logging

# Expose everything to maintain backwards compatibility and test stability
from ai_blocker.audit_log import AuditEntry, AuditLog
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
from ai_blocker.context_anonymizer import CodeAnonymizer
from ai_blocker.dlp_engine import DLPAction, DLPEngine, DLPFinding, DLPPolicy, DLPPolicyManager, FindingType
from ai_blocker.domain_matcher import BLOCKLIST_PATTERNS, is_domain_blocked, matches_any_pattern

# Phase 2+3 modules (always available — pure stdlib)
from ai_blocker.dpi_rules import DEFAULT_DPI_RULES, DPIAction, DPIRule, DPIRuleEngine
from ai_blocker.gateway import GatewayHandler
from ai_blocker.guardrails import GuardrailResult, PromptGuardrail, ThreatCategory
from ai_blocker.i18n import (
    CATEGORY_TRANSLATIONS,
    LANG_CODE_MAP,
    LANG_DISPLAY_MAP,
    STRINGS,
    detect_system_language,
    load_translations,
)
from ai_blocker.network_backends import (
    BackendInfo,
    BackendResult,
    FirewallRedirectBackend,
    HostsBackend,
    NetworkBackend,
    get_backend_info,
    get_network_backend,
    list_network_backends,
    plan_backend_activation,
    plan_backend_deactivation,
)

# tls_manager requires the `cryptography` package (optional dependency)
from ai_blocker.semantic_dlp import SemanticDLPClient, SemanticResult
from ai_blocker.system_utils import (
    _get_subprocess_kwargs,
    count_total_domains,
    flush_dns,
    get_hosts_status,
    is_admin,
    relaunch_as_admin,
)
from ai_blocker.token_monitor import TokenMonitor

try:
    from ai_blocker.tls_manager import (
        clear_leaf_cache,
        generate_leaf_cert,
        generate_root_ca,
        get_or_create_root_ca,
        get_or_generate_leaf_cert,
        is_root_ca_installed,
        uninstall_root_ca,
    )
except ImportError:
    logging.warning('tls_manager not available: install cryptography for TLS/DPI support')

from ai_blocker.ui import AIBlockerApp

if CURRENT_OS == "Windows":
    from ai_blocker.tray import WindowsTrayIcon
