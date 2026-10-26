"""Dispatcharr and exporter identity and configuration metrics."""

from ..config import DEFAULT_PORT, PLUGIN_CONFIG, PLUGIN_FIELDS
from ..utils import get_dispatcharr_version


def collect_exporter_metrics(context, writer) -> None:
    """Write the core Dispatcharr and exporter metric families."""
    _version, _timestamp, full_version = get_dispatcharr_version()
    writer.info(
        "dispatcharr_info",
        "Dispatcharr version and instance information",
    ).add([("version", full_version)])
    writer.separator()

    exporter_version = PLUGIN_CONFIG["version"].lstrip("-")
    settings_labels = []
    port_value = DEFAULT_PORT

    for field in PLUGIN_FIELDS:
        field_id = field["id"]
        field_value = context.settings.get(field_id, field["default"])
        if field_id == "port":
            port_value = field_value
        if isinstance(field_value, bool):
            field_value = str(field_value).lower()
        settings_labels.append((field_id, field_value))

    writer.info(
        "dispatcharr_exporter_info",
        "Dispatcharr Exporter plugin version information",
    ).add([("version", exporter_version)])
    writer.info(
        "dispatcharr_exporter_settings_info",
        "Dispatcharr Exporter plugin settings (for debugging/support)",
    ).add(settings_labels)
    writer.gauge(
        "dispatcharr_exporter_port",
        "Configured port number for the metrics server",
    ).add(port_value)
    writer.separator()
