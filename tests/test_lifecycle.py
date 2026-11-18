"""Manifest, settings, and managed service regression tests."""

import json
import pathlib
import sys
import threading
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
collector_stub = types.ModuleType("src.collector")
collector_stub.PrometheusMetricsCollector = type("PrometheusMetricsCollector", (), {})
with patch.dict(sys.modules, {"src.collector": collector_stub}):
    from src import Plugin
    from src.config import PLUGIN_FIELDS
    from src.server import MetricsServer


class LifecycleTests(unittest.TestCase):
    def test_manifest_and_sections(self):
        manifest = json.loads((pathlib.Path(__file__).resolve().parents[1] / "src/plugin.json").read_text())
        self.assertEqual(manifest["manifest_version"], 2)
        self.assertEqual(manifest["actions"], [])
        self.assertIn("persistent_service", manifest["capabilities"])
        self.assertIn("network_listener", manifest["capabilities"])
        fields = {field["id"]: field for field in PLUGIN_FIELDS}
        self.assertNotIn("auto_start", fields)
        self.assertEqual(fields["port"]["section"], "server_settings")
        self.assertEqual(fields["include_m3u_stats"]["section"], "stats_settings")
        for name in ("packet_slapper", "stream_usage"):
            section = f"include_{name}_stats_section"
            self.assertTrue(fields[section]["collapsed"])
            self.assertEqual(fields[f"include_{name}_stats"]["section"], section)

    def test_leadership_and_current_settings(self):
        plugin = Plugin()
        self.assertIsNone(plugin.server)
        calls = []
        context = {"settings": {"port": 1111}, "get_settings": lambda: {"port": 2222, "auto_start": False},
                   "start_service": lambda target, name: calls.append((target, name))}
        plugin.on_leader_acquired(context)
        self.assertEqual(plugin.server.port, 2222)
        plugin.on_leader_acquired(context)
        self.assertEqual(len(calls), 1)
        plugin.on_leader_lost(context)
        plugin.on_leader_acquired(context)
        self.assertEqual(len(calls), 2)
        plugin.stop(context)
        self.assertIsNone(plugin.server)

    def test_registration_failure_and_snapshot_fallback(self):
        plugin = Plugin()
        def fail(*args, **kwargs):
            raise RuntimeError("failed")
        with self.assertRaises(RuntimeError):
            plugin.on_leader_acquired({"settings": {"port": 1234}, "start_service": fail})
        self.assertIsNone(plugin.server)
        plugin.on_leader_acquired({"settings": {"port": 1234}, "start_service": lambda *a, **k: None})
        self.assertEqual(plugin.server.port, 1234)

    def test_service_stops_and_propagates_bind_failure(self):
        event = threading.Event()
        servers = []
        class FakeServer:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.stopped = False
                servers.append(self)
            def start(self):
                if self.kwargs["listener"][1] == 1:
                    raise OSError("in use")
            def stop(self, timeout):
                self.stopped = True
        gevent = types.ModuleType("gevent")
        gevent.sleep = lambda _: event.set()
        pywsgi = types.ModuleType("gevent.pywsgi")
        pywsgi.WSGIServer = FakeServer
        with patch.dict(sys.modules, {"gevent": gevent, "gevent.pywsgi": pywsgi}):
            MetricsServer(None, port=1234).run(event)
            self.assertTrue(servers[-1].stopped)
            self.assertIsNone(servers[-1].kwargs["log"])
            event.clear()
            with self.assertRaises(OSError):
                MetricsServer(None, port=1, settings={"suppress_access_logs": False}).run(event)
            self.assertTrue(servers[-1].stopped)
            self.assertNotIn("log", servers[-1].kwargs)


if __name__ == "__main__":
    unittest.main()
