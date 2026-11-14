"""Unit tests for the Packet Slapper speedtest integration."""

import importlib.util
import json
import pathlib
import sys
import types
import unittest

from fakes import FakeRedis


def _load():
    root = pathlib.Path(__file__).resolve().parents[1] / "src"
    for name, path in (
        ("exporter", root),
        ("exporter.metrics", root / "metrics"),
        ("exporter.integrations", root / "integrations"),
    ):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        sys.modules[name] = package

    for name, path in (
        ("exporter.utils", root / "utils.py"),
        ("exporter.metrics.writer", root / "metrics" / "writer.py"),
        ("exporter.integrations.base", root / "integrations" / "base.py"),
        ("exporter.integrations.packet_slapper", root / "integrations" / "packet_slapper.py"),
    ):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

    return (
        sys.modules["exporter.metrics.writer"].MetricsWriter,
        sys.modules["exporter.integrations.packet_slapper"],
    )


MetricsWriter, packet_slapper = _load()


def _scrape(state):
    context = types.SimpleNamespace(
        redis_client=FakeRedis(values={packet_slapper.REDIS_KEY: json.dumps(state)}),
    )
    writer = MetricsWriter()
    packet_slapper.collect_metrics(context, writer)
    return "\n".join(writer.drain())


RESULT = {
    "download_mbps": 912.4,
    "upload_mbps": 41.8,
    "latency_ms": 9.1,
    "jitter_ms": 0.7,
    "packet_loss": 0.0,
    "download_latency_ms": 45.2,
    "upload_latency_ms": 120,
    "isp": "Example ISP",
    "server_name": "Example",
    "server_location": "Chicago, IL",
    "server_country": "United States",
    "server_host": "speedtest.example.net",
}


class PacketSlapperTests(unittest.TestCase):
    def test_loaded_latency_metrics(self):
        rendered = _scrape({
            "last_attempt_timestamp_seconds": 1761350400,
            "last_attempt_success": 1,
            "last_success_timestamp_seconds": 1761350400,
            "result": RESULT,
        })
        self.assertIn("# TYPE dispatcharr_speedtest_download_latency_ms gauge", rendered)
        self.assertIn("dispatcharr_speedtest_download_latency_ms 45.2", rendered)
        self.assertIn("dispatcharr_speedtest_upload_latency_ms 120", rendered)
        self.assertIn("dispatcharr_speedtest_download_mbps 912.4", rendered)

    def test_last_skip_timestamp(self):
        rendered = _scrape({
            "last_attempt_timestamp_seconds": 1761350400,
            "last_attempt_success": 1,
            "last_success_timestamp_seconds": 1761350400,
            "last_skip_timestamp_seconds": 1761354000,
            "result": RESULT,
        })
        self.assertIn("dispatcharr_speedtest_last_skip_timestamp_seconds 1761354000", rendered)

    def test_skip_before_any_attempt(self):
        rendered = _scrape({"last_skip_timestamp_seconds": 1761354000})
        self.assertIn("dispatcharr_speedtest_last_skip_timestamp_seconds 1761354000", rendered)
        self.assertNotIn("dispatcharr_speedtest_download_mbps", rendered)

    def test_older_payload_omits_new_metrics(self):
        old = {key: value for key, value in RESULT.items()
               if key not in ("download_latency_ms", "upload_latency_ms")}
        rendered = _scrape({
            "last_attempt_timestamp_seconds": 1761350400,
            "last_attempt_success": 1,
            "last_success_timestamp_seconds": 1761350400,
            "result": old,
        })
        self.assertIn("dispatcharr_speedtest_latency_ms 9.1", rendered)
        self.assertNotIn("download_latency_ms", rendered)
        self.assertNotIn("upload_latency_ms", rendered)
        self.assertNotIn("last_skip_timestamp_seconds", rendered)

    def test_unreported_loaded_latency_is_omitted(self):
        result = dict(RESULT, download_latency_ms=None, upload_latency_ms=None)
        rendered = _scrape({"last_attempt_success": 1, "result": result})
        self.assertNotIn("download_latency_ms", rendered)
        self.assertNotIn("upload_latency_ms", rendered)


if __name__ == "__main__":
    unittest.main()
