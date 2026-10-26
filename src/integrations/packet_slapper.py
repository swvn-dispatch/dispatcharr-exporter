"""Prometheus metrics published by the Packet Slapper plugin."""

import json
import logging
from .base import Integration

REDIS_KEY = "packet_slapper:prometheus:latest"
MAX_PAYLOAD_BYTES = 64 * 1024
logger = logging.getLogger(__name__)


def collect_metrics(context, writer) -> None:
    """Write the latest Packet Slapper speedtest metrics.

    Packet Slapper owns the Redis payload. A missing or unreadable payload is
    treated as unavailable integration data and emits no metrics.
    """
    if context.redis_client is None:
        return

    try:
        raw = context.redis_client.get(REDIS_KEY)
        if not raw:
            return
        if not isinstance(raw, (bytes, str)):
            logger.warning("Ignoring Packet Slapper speedtest payload with unsupported type %s", type(raw).__name__)
            return
        if len(raw) > MAX_PAYLOAD_BYTES:
            logger.warning("Ignoring oversized Packet Slapper speedtest payload")
            return
        state = json.loads(raw)
        if not isinstance(state, dict):
            return
    except Exception as exc:
        logger.warning("Error reading Packet Slapper speedtest metrics: %s", exc)
        return

    writer.gauge(
        "dispatcharr_speedtest_last_attempt_timestamp_seconds",
        "Unix timestamp of the latest attempted speedtest",
    ).add(state.get("last_attempt_timestamp_seconds"))
    writer.gauge(
        "dispatcharr_speedtest_last_attempt_success",
        "Whether the latest speedtest succeeded (1 success, 0 failure)",
    ).add(state.get("last_attempt_success"))
    writer.gauge(
        "dispatcharr_speedtest_last_success_timestamp_seconds",
        "Unix timestamp of the latest successful speedtest",
    ).add(state.get("last_success_timestamp_seconds"))

    result = state.get("result")
    if isinstance(result, dict) and result:
        for field, suffix, help_text in (
            ("download_mbps", "download_mbps", "Latest successful download speed in megabits per second"),
            ("upload_mbps", "upload_mbps", "Latest successful upload speed in megabits per second"),
            ("latency_ms", "latency_ms", "Latest successful idle ping latency in milliseconds"),
            ("jitter_ms", "jitter_ms", "Latest successful idle ping jitter in milliseconds"),
            ("packet_loss", "packet_loss_percent", "Latest successful packet loss percentage"),
        ):
            writer.gauge(f"dispatcharr_speedtest_{suffix}", help_text).add(result.get(field))

        writer.info(
            "dispatcharr_speedtest_server_info",
            "ISP and Ookla server of the latest successful speedtest",
        ).add([
            (field, result.get(field))
            for field in ("isp", "server_name", "server_location", "server_country", "server_host")
        ])

    writer.separator()


INTEGRATION = Integration(
    name="Speedtest",
    description=(
        "Include the latest internet speedtest from the Packet Slapper plugin "
        "(requires its 'Publish results for Prometheus' setting)"
    ),
    collect_metrics=collect_metrics,
)
