"""Prometheus metrics published by the Packet Slapper plugin."""

import json
import logging
import math

from ..utils import escape_label
from .base import Integration

REDIS_KEY = "packet_slapper:prometheus:latest"
MAX_PAYLOAD_BYTES = 64 * 1024
logger = logging.getLogger(__name__)


def collect_metrics(redis_client) -> list:
    """Return the latest Packet Slapper speedtest metrics.

    Packet Slapper owns the Redis payload. A missing or unreadable payload is
    treated as unavailable integration data and emits no metrics.
    """
    if redis_client is None:
        return []

    try:
        raw = redis_client.get(REDIS_KEY)
        if not raw:
            return []
        if not isinstance(raw, (bytes, str)):
            logger.warning("Ignoring Packet Slapper speedtest payload with unsupported type %s", type(raw).__name__)
            return []
        if len(raw) > MAX_PAYLOAD_BYTES:
            logger.warning("Ignoring oversized Packet Slapper speedtest payload")
            return []
        state = json.loads(raw)
        if not isinstance(state, dict):
            return []
    except Exception as exc:
        logger.warning("Error reading Packet Slapper speedtest metrics: %s", exc)
        return []

    metrics = []

    def gauge(name, help_text, value):
        """Append a finite numeric gauge, preserving timestamp precision."""
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return
        if not math.isfinite(number):
            return

        value_str = str(int(number)) if number.is_integer() else repr(number)
        metrics.append(f"# HELP {name} {help_text}")
        metrics.append(f"# TYPE {name} gauge")
        metrics.append(f"{name} {value_str}")

    gauge(
        "dispatcharr_speedtest_last_attempt_timestamp_seconds",
        "Unix timestamp of the latest attempted speedtest",
        state.get("last_attempt_timestamp_seconds"),
    )
    gauge(
        "dispatcharr_speedtest_last_attempt_success",
        "Whether the latest speedtest succeeded (1 success, 0 failure)",
        state.get("last_attempt_success"),
    )
    gauge(
        "dispatcharr_speedtest_last_success_timestamp_seconds",
        "Unix timestamp of the latest successful speedtest",
        state.get("last_success_timestamp_seconds"),
    )

    result = state.get("result")
    if isinstance(result, dict) and result:
        for field, suffix, help_text in (
            ("download_mbps", "download_mbps", "Latest successful download speed in megabits per second"),
            ("upload_mbps", "upload_mbps", "Latest successful upload speed in megabits per second"),
            ("latency_ms", "latency_ms", "Latest successful idle ping latency in milliseconds"),
            ("jitter_ms", "jitter_ms", "Latest successful idle ping jitter in milliseconds"),
            ("packet_loss", "packet_loss_percent", "Latest successful packet loss percentage"),
        ):
            gauge(f"dispatcharr_speedtest_{suffix}", help_text, result.get(field))

        labels = ",".join(
            f'{field}="{escape_label(result.get(field))}"'
            for field in ("isp", "server_name", "server_location", "server_country", "server_host")
        )
        metrics.append("# HELP dispatcharr_speedtest_server_info ISP and Ookla server of the latest successful speedtest")
        metrics.append("# TYPE dispatcharr_speedtest_server_info gauge")
        metrics.append(f"dispatcharr_speedtest_server_info{{{labels}}} 1")

    if metrics:
        metrics.append("")
    return metrics


INTEGRATION = Integration(
    name="Speedtest",
    description=(
        "Include the latest internet speedtest from the Packet Slapper plugin "
        "(requires its 'Publish results for Prometheus' setting)"
    ),
    collect_metrics=collect_metrics,
)
