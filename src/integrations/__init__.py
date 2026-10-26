"""Optional metrics collected from external plugins and services.

Each registered integration owns its producer contract and must fail without
affecting the core Dispatcharr metrics scrape.
"""

import logging

from .packet_slapper import SETTING_ID as PACKET_SLAPPER_SETTING_ID
from .packet_slapper import collect_metrics as collect_packet_slapper_metrics

logger = logging.getLogger(__name__)

_INTEGRATIONS = (
    (PACKET_SLAPPER_SETTING_ID, "Packet Slapper", collect_packet_slapper_metrics),
)


def collect_enabled_metrics(redis_client, settings: dict) -> list:
    """Collect metrics for enabled external integrations."""
    metrics = []
    for setting_id, name, collect_metrics in _INTEGRATIONS:
        if not settings.get(setting_id, False):
            continue
        try:
            metrics.extend(collect_metrics(redis_client))
        except Exception as exc:
            logger.warning("Error collecting %s integration metrics: %s", name, exc)
    return metrics
