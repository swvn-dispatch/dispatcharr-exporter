"""Unit tests for dependency-free Prometheus metric rendering."""

import importlib.util
import pathlib
import sys
import types
import unittest


def _load_writer():
    root = pathlib.Path(__file__).resolve().parents[1] / "src"
    package = types.ModuleType("exporter")
    package.__path__ = [str(root)]
    sys.modules["exporter"] = package
    metrics_package = types.ModuleType("exporter.metrics")
    metrics_package.__path__ = [str(root / "metrics")]
    sys.modules["exporter.metrics"] = metrics_package

    for name, path in (
        ("exporter.utils", root / "utils.py"),
        ("exporter.metrics.writer", root / "metrics" / "writer.py"),
    ):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

    return sys.modules["exporter.metrics.writer"].MetricsWriter


MetricsWriter = _load_writer()


class MetricsWriterTests(unittest.TestCase):
    def test_gauge_declares_once_and_preserves_ordered_labels(self):
        writer = MetricsWriter()
        gauge = writer.gauge("example_gauge", "Example gauge")
        gauge.add(1, [("second", "two"), ("first", "one")])
        gauge.add(2, [("second", "four"), ("first", "three")])

        self.assertEqual(
            writer.drain(),
            [
                "# HELP example_gauge Example gauge",
                "# TYPE example_gauge gauge",
                'example_gauge{second="two",first="one"} 1',
                'example_gauge{second="four",first="three"} 2',
            ],
        )

    def test_declarations_precede_all_samples_in_a_group(self):
        writer = MetricsWriter()
        first = writer.gauge("first", "First")
        second = writer.gauge("second", "Second")
        first.add(1)
        second.add(2)
        first.add(3)
        self.assertEqual(
            writer.drain(),
            [
                "# HELP first First",
                "# TYPE first gauge",
                "# HELP second Second",
                "# TYPE second gauge",
                "first 1",
                "second 2",
                "first 3",
            ],
        )

    def test_invalid_values_do_not_declare_a_metric(self):
        writer = MetricsWriter()
        self.assertFalse(writer.counter("example_total", "Example counter").add(float("nan")))
        self.assertEqual(writer.drain(), [])

    def test_invalid_labels_do_not_declare_a_metric(self):
        writer = MetricsWriter()
        with self.assertRaises(ValueError):
            writer.gauge("example_gauge", "Example gauge").add(1, [("bad-label", "x")])
        self.assertEqual(writer.drain(), [])

    def test_mapping_labels_are_deterministic_and_bytes_are_supported(self):
        writer = MetricsWriter()
        writer.gauge("example_gauge", "Example gauge").add(1, {"z": b"last", "a": b"first"})
        self.assertEqual(
            writer.drain()[-1],
            'example_gauge{a="first",z="last"} 1',
        )

    def test_invalid_metric_name_and_separator_behavior(self):
        writer = MetricsWriter()
        with self.assertRaises(ValueError):
            writer.gauge("invalid-name", "Example gauge").add(1)
        self.assertEqual(writer.drain(), [])

        writer.gauge("example_gauge", "Example gauge").add(-1)
        writer.separator()
        writer.separator()
        self.assertEqual(writer.drain()[-1], "")

    def test_histogram_and_summary_reject_invalid_values(self):
        writer = MetricsWriter()
        self.assertFalse(writer.histogram("latency_seconds", "Latency").bucket(1, float("inf")))
        self.assertFalse(writer.summary("request_seconds", "Duration").quantile(0.5, float("nan")))
        self.assertEqual(writer.drain(), [])

    def test_escaping_and_family_conflicts(self):
        writer = MetricsWriter()
        writer.info("example_info", "Example info").add({"label": 'quote"\\\r\n'})
        rendered = "\n".join(writer.drain())
        self.assertIn('label="quote\\"\\\\\\n\\n"', rendered)

        writer.gauge("example", "Gauge").add(1)
        with self.assertRaises(ValueError):
            writer.counter("example", "Counter").add(1)

    def test_histogram_and_summary_helpers(self):
        writer = MetricsWriter()
        histogram = writer.histogram("latency_seconds", "Latency")
        histogram.bucket(1, 2)
        histogram.count(2)
        histogram.sum(0.5)
        summary = writer.summary("request_seconds", "Request duration")
        summary.quantile(0.95, 0.2)
        summary.count(1)
        summary.sum(0.2)

        rendered = "\n".join(writer.drain())
        self.assertIn("# TYPE latency_seconds histogram", rendered)
        self.assertIn("latency_seconds_bucket{le=\"1\"} 2", rendered)
        self.assertIn("# TYPE request_seconds summary", rendered)
        self.assertIn("request_seconds{quantile=\"0.95\"} 0.2", rendered)


if __name__ == "__main__":
    unittest.main()
