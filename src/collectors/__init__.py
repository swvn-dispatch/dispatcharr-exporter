"""Core Dispatcharr metric collectors and fixed scrape order."""

from .accounts import (
    collect_account_metrics,
    collect_m3u_account_metrics,
    collect_profile_metrics,
)
from .channels import collect_channel_metrics
from .clients import collect_client_metrics
from .epg import collect_epg_metrics
from .exporter import collect_exporter_metrics
from .plugins import collect_plugin_metrics
from .streams import collect_stream_metrics
from .users import collect_user_metrics


def collect_core_metrics(context, writer) -> None:
    """Run writer-based core collectors in their public exposition order."""
    collect_exporter_metrics(context, writer)
    if context.settings.get("include_m3u_stats", True):
        collect_m3u_account_metrics(context, writer)
    if context.settings.get("include_epg_stats", False):
        collect_epg_metrics(context, writer)
    collect_channel_metrics(context, writer)
    if context.settings.get("include_m3u_stats", True):
        collect_profile_metrics(context, writer)
        writer.separator()
    collect_stream_metrics(context, writer)
    if context.settings.get("include_client_stats", False):
        collect_client_metrics(context, writer)
    if context.settings.get("include_plugin_stats", False):
        collect_plugin_metrics(context, writer)
    if context.settings.get("include_user_stats", False):
        collect_user_metrics(context, writer)


__all__ = [
    "collect_account_metrics",
    "collect_m3u_account_metrics",
    "collect_profile_metrics",
    "collect_channel_metrics",
    "collect_client_metrics",
    "collect_core_metrics",
    "collect_epg_metrics",
    "collect_exporter_metrics",
    "collect_plugin_metrics",
    "collect_stream_metrics",
    "collect_user_metrics",
]
