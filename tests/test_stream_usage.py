"""Stream Usage integration payload and metric rendering tests."""
import json
import pathlib
import sys
import unittest
from types import SimpleNamespace

import types
root = pathlib.Path(__file__).resolve().parents[1] / 'src'
for name, directory in (('exporter', root), ('exporter.integrations', root / 'integrations'),
                        ('exporter.metrics', root / 'metrics')):
    package = types.ModuleType(name)
    package.__path__ = [str(directory)]
    sys.modules[name] = package
import importlib.util
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
load('exporter.utils', root / 'utils.py')
writer_module = load('exporter.metrics.writer', root / 'metrics/writer.py')
load('exporter.integrations.base', root / 'integrations/base.py')
usage_module = load('exporter.integrations.stream_usage', root / 'integrations/stream_usage.py')
collect_metrics, REDIS_KEY = usage_module.collect_metrics, usage_module.REDIS_KEY
MetricsWriter = writer_module.MetricsWriter


class Redis:
    def __init__(self, raw):
        self.raw = raw

    def get(self, key):
        assert key == REDIS_KEY
        return self.raw


class IntegrationTests(unittest.TestCase):
    def test_metrics_and_bad_payload(self):
        state = {'v': 1, 'last_poll': 100, 'totals': {'out': 80, 'in': 30},
                 'periods': {p: {'out': 80, 'in': 30} for p in ('hour', 'today', 'week', 'month')},
                 'users': {'out': [{'username': 'viewer', 'bytes': 80}], 'in': []},
                 'channels': {'out': [{'channel': 'News', 'bytes': 80}], 'in': []}}
        writer = MetricsWriter()
        collect_metrics(SimpleNamespace(redis_client=Redis(json.dumps(state).encode())), writer)
        rendered = '\n'.join(writer.drain())
        self.assertIn('dispatcharr_usage_bytes_total{direction="out"} 80', rendered)
        self.assertIn('dispatcharr_usage_user_bytes_total{username="viewer",direction="out"} 80', rendered)
        self.assertIn('dispatcharr_usage_channel_bytes_total{channel="News",direction="out"} 80', rendered)
        self.assertIn('dispatcharr_usage_period_bytes{period="month",direction="in"} 30', rendered)
        self.assertIn('dispatcharr_usage_last_poll_timestamp_seconds 100', rendered)
        for raw in (None, b'{bad', b'x'*65537, json.dumps({**state, 'v': 2}).encode()):
            writer = MetricsWriter()
            collect_metrics(SimpleNamespace(redis_client=Redis(raw)), writer)
            self.assertEqual(writer.drain(), [])


if __name__ == '__main__':
    unittest.main()
