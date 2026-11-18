"""gevent WSGI metrics server.

Binds to a configurable host:port and serves:
  GET /          Landing page with links
  GET /metrics   Prometheus text-format metrics
  GET /health    Simple health check
"""

import logging

from .config import PLUGIN_CONFIG, DEFAULT_PORT, DEFAULT_HOST
from .utils import normalize_host

logger = logging.getLogger(__name__)


class MetricsServer:
    """WSGI metrics listener owned by Dispatcharr's managed service."""

    def __init__(self, collector, port=None, host=None, settings=None, get_settings=None):
        self.collector = collector
        self.port = port if port is not None else DEFAULT_PORT
        self.host = normalize_host(host, DEFAULT_HOST)
        self.settings = settings or {}
        self.get_settings = get_settings

    def wsgi_app(self, environ, start_response):
        """Handle a single HTTP request."""
        path = environ.get('PATH_INFO', '/')

        if path == '/metrics':
            try:
                settings = self.get_settings() if self.get_settings else self.settings
                # Server settings describe the running listener until reload.
                settings = dict(settings or {})
                settings.update({
                    "host": self.host,
                    "port": self.port,
                    "suppress_access_logs": self.settings.get("suppress_access_logs", True),
                })
                metrics_text = self.collector.collect_metrics(settings=settings)
                start_response('200 OK', [('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')])
                return [metrics_text.encode('utf-8')]
            except Exception as e:
                logger.error(f"Error generating metrics: {e}", exc_info=True)
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                return [f"# Error: {str(e)}\n".encode('utf-8')]
            finally:
                # This WSGI server runs outside Django's normal request cycle,
                # so the request_finished signal that would normally close/reset
                # DB connections never fires. Without this, connections opened
                # by collect_metrics() (and any left mid-transaction by an
                # exception) accumulate until the DB's connection limit is
                # exhausted, hanging the whole Dispatcharr app until restart.
                try:
                    from django.db import close_old_connections
                    close_old_connections()
                except Exception as e:
                    logger.warning(f"Error closing DB connections after /metrics: {e}")

        elif path == '/health':
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [b"OK\n"]

        elif path == '/':
            plugin_name = PLUGIN_CONFIG.get('name', 'Dispatcharr Exporter')
            plugin_version = PLUGIN_CONFIG.get('version', 'unknown version').lstrip('-')
            plugin_description = PLUGIN_CONFIG.get('description', 'This exporter provides Prometheus metrics for Dispatcharr.')
            repo_url = PLUGIN_CONFIG.get('repo_url', 'https://github.com/sethwv/dispatcharr-exporter')
            releases_url = f"{repo_url}/releases"

            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{plugin_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            max-width: 600px;
            margin: 100px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ margin-top: 0; color: #333; }}
        .version {{ color: #999; font-size: 14px; margin-top: -10px; margin-bottom: 20px; }}
        p {{ color: #666; line-height: 1.6; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .links {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
        .links a {{ display: inline-block; margin-right: 20px; font-weight: 500; }}
        .external-links {{ margin-top: 20px; font-size: 14px; }}
        .external-links a {{ margin-right: 15px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{plugin_name}</h1>
        <div class="version">{plugin_version}</div>
        <p>{plugin_description.split('. ')[0]}.</p>
        <div class="external-links">
            <a href="{repo_url}" target="_blank">GitHub Repository</a>
            <a href="{releases_url}" target="_blank">Releases</a>
        </div>
        <div class="links">
            <a href="/metrics">View Metrics</a>
            <a href="/health">Health Check</a>
        </div>
    </div>
</body>
</html>"""
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            return [html.encode('utf-8')]

        else:
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b"Not Found\n"]

    def run(self, stop_event):
        """Serve until leadership is lost, closing the socket before returning."""
        from gevent import sleep
        from gevent.pywsgi import WSGIServer

        kwargs = {"listener": (self.host, self.port), "application": self.wsgi_app}
        if self.settings.get("suppress_access_logs", True):
            kwargs["log"] = None
        server = WSGIServer(**kwargs)
        try:
            if stop_event.is_set():
                return
            server.start()
            logger.info("Metrics server listening on %s:%s", self.host, self.port)
            while not stop_event.is_set():
                sleep(0.1)
        finally:
            server.stop(timeout=1)
