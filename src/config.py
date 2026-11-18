"""Plugin configuration and field definitions.

This module combines the core exporter settings with integration settings for:
  - PLUGIN_CONFIG: loaded from plugin.json
  - PLUGIN_FIELDS: the settings schema shared by the Plugin class and collector
"""

import json
import os

from .integrations import INTEGRATION_FIELDS


# ── Hard-coded defaults ─────────────────────────────────────────────────────
DEFAULT_PORT: int = 9192
DEFAULT_HOST: str = "0.0.0.0"

def _load_plugin_config() -> dict:
    """Load plugin configuration from plugin.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'plugin.json')
    with open(config_path, 'r') as f:
        return json.load(f)


PLUGIN_CONFIG = _load_plugin_config()

# ── Plugin field definitions ─────────────────────────────────────────────────
# Shared between the Plugin class (used by Dispatcharr UI) and the collector
# (used to build the dispatcharr_exporter_settings_info metric).
CORE_PLUGIN_FIELDS = [
    {"id": "server_settings", "label": "Server Settings", "type": "section", "collapsed": False, "description": "Save changes and reload the plugin to apply server settings."},
    {
        "id": "suppress_access_logs",
        "label": "Suppress Access Logs",
        "type": "boolean",
        "default": True,
        "description": "Suppress HTTP access logs for /metrics requests",
    },
    {
        "id": "port",
        "label": "Metrics Server Port",
        "type": "number",
        "default": DEFAULT_PORT,
        "description": "Port for the metrics HTTP server",
        "placeholder": "9192",
    },
    {
        "id": "host",
        "label": "Metrics Server Host",
        "type": "string",
        "default": DEFAULT_HOST,
        "description": "Host address to bind to (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)",
        "placeholder": "0.0.0.0",
    },
    {"id": "stats_settings", "label": "Metric Settings", "type": "section", "collapsed": False, "description": "Saved changes take effect on the next metrics scrape."},
    {
        "id": "base_url",
        "label": "Dispatcharr Base URL (Optional)",
        "type": "string",
        "default": "",
        "description": (
            "URL for Dispatcharr API (e.g., http://localhost:5656 or "
            "https://dispatcharr.example.com). If set, logo URLs will be "
            "absolute instead of relative paths. Leave empty to use relative paths."
        ),
        "placeholder": "http://localhost:5656",
    },
    {
        "id": "include_m3u_stats",
        "label": "Include M3U Account Statistics",
        "type": "boolean",
        "default": True,
        "description": "Include M3U account and profile metrics in the output",
    },
    {
        "id": "include_epg_stats",
        "label": "Include EPG Source Statistics",
        "type": "boolean",
        "default": False,
        "description": "Include EPG source and status metrics in the output",
    },
    {
        "id": "include_client_stats",
        "label": "Include Client Connection Statistics",
        "type": "boolean",
        "default": False,
        "description": "Include individual client connection information",
    },
    {
        "id": "include_source_urls",
        "label": "Include Provider/Source Information",
        "type": "boolean",
        "default": False,
        "description": (
            "Include server URLs & XC usernames in M3U account and EPG source metrics. "
            "Ensure this is DISABLED if sharing output in Discord for troubleshooting"
        ),
    },
    {
        "id": "include_user_stats",
        "label": "Include User Statistics",
        "type": "boolean",
        "default": False,
        "description": "Include user account metrics (user info, stream limits, active stream counts).",
    },
    {
        "id": "include_plugin_stats",
        "label": "Include Plugin Statistics",
        "type": "boolean",
        "default": False,
        "description": "Include installed plugin and plugin-repo health metrics",
    },
    {
        "id": "include_channel_info",
        "label": "Include Channel Info Statistics",
        "type": "boolean",
        "default": False,
        "description": "Include per-channel info (catch-up status, source/stream count, group) metrics",
    },
]

# The integrations registry generates a disabled-by-default include_* control
# for every integration before its fields reach the UI.
for field in CORE_PLUGIN_FIELDS:
    if field["type"] != "section":
        field["section"] = (
            "server_settings" if field["id"] in {"host", "port", "suppress_access_logs"}
            else "stats_settings"
        )

PLUGIN_FIELDS = CORE_PLUGIN_FIELDS + list(INTEGRATION_FIELDS)
