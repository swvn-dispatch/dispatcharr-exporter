"""Tests for the complete metrics collection path."""

import importlib.util
import json
import pathlib
import sys
import types
import unittest
from fakes import FakeRedis


def _load_collector():
    root = pathlib.Path(__file__).resolve().parents[1] / "src"
    package = types.ModuleType("collector_test_exporter")
    package.__path__ = [str(root)]
    collectors = types.ModuleType("collector_test_exporter.collectors")
    collectors.collect_core_metrics = lambda context, writer: writer.gauge(
        "core_example", "Core example"
    ).add(1)
    sys.modules[package.__name__] = package
    sys.modules[collectors.__name__] = collectors
    spec = importlib.util.spec_from_file_location("collector_test_exporter.collector", root / "collector.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PrometheusMetricsCollector


PrometheusMetricsCollector = _load_collector()


class CollectorTests(unittest.TestCase):
    def test_scrape_with_packet_slapper_enabled_and_disabled(self):
        collector = PrometheusMetricsCollector()
        collector.redis_client = FakeRedis(values={
            "packet_slapper:prometheus:latest": json.dumps({"result": {"download_latency_ms": 45.2}}),
        })

        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                rendered = collector.collect_metrics({"include_packet_slapper_stats": enabled})
                self.assertIn("core_example 1", rendered)
                self.assertEqual(rendered.count("dispatcharr_speedtest_download_latency_ms 45.2"), int(enabled))


if __name__ == "__main__":
    unittest.main()
