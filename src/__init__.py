"""Dispatcharr Prometheus exporter plugin."""

from .collector import PrometheusMetricsCollector
from .config import DEFAULT_HOST, DEFAULT_PORT, PLUGIN_CONFIG, PLUGIN_FIELDS
from .server import MetricsServer
from .utils import normalize_host


class Plugin:
    name = PLUGIN_CONFIG["name"]
    description = PLUGIN_CONFIG["description"]
    version = PLUGIN_CONFIG["version"]
    author = PLUGIN_CONFIG["author"]
    fields = PLUGIN_FIELDS
    actions = []

    def __init__(self):
        self.server = None

    def on_leader_acquired(self, context):
        if self.server is not None:
            return
        getter = context.get("get_settings")
        settings = (getter() if getter else context.get("settings")) or {}
        server = MetricsServer(
            PrometheusMetricsCollector(),
            host=normalize_host(settings.get("host"), DEFAULT_HOST),
            port=int(settings.get("port") or DEFAULT_PORT),
            settings=settings,
        )
        context["start_service"](server.run, name="metrics")
        self.server = server

    def on_leader_lost(self, context):
        self.server = None

    def stop(self, context):
        self.server = None


__version__ = PLUGIN_CONFIG["version"]
