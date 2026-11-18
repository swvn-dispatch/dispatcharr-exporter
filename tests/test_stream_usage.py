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


def valid_state():
    return {'v': 1, 'last_poll': 100, 'totals': {'out': 80, 'in': 30},
            'periods': {p: {'out': 80, 'in': 30} for p in ('hour', 'today', 'week', 'month')},
            'users': {'out': [{'username': 'viewer', 'bytes': 80}], 'in': []},
            'channels': {'out': [{'channel': 'News', 'bytes': 80}], 'in': []}}


def render(raw, redis=True):
    writer = MetricsWriter()
    collect_metrics(SimpleNamespace(redis_client=Redis(raw) if redis else None), writer)
    return writer.drain()


class IntegrationTests(unittest.TestCase):
    def test_metrics_and_bad_payload(self):
        state = valid_state()
        rendered = '\n'.join(render(json.dumps(state).encode()))
        self.assertIn('dispatcharr_usage_bytes_total{direction="out"} 80', rendered)
        self.assertIn('dispatcharr_usage_user_bytes_total{username="viewer",direction="out"} 80', rendered)
        self.assertIn('dispatcharr_usage_channel_bytes_total{channel="News",direction="out"} 80', rendered)
        self.assertIn('dispatcharr_usage_period_bytes{period="month",direction="in"} 30', rendered)
        self.assertIn('dispatcharr_usage_last_poll_timestamp_seconds 100', rendered)
        for raw in (None, b'{bad', b'x'*65537, json.dumps({**state, 'v': 2}).encode()):
            self.assertEqual(render(raw), [])

    def test_malformed_field_drops_whole_snapshot(self):
        # One bad value anywhere, including after valid entries, must not leave partial series behind.
        for mutate in (lambda s: s['totals'].update(out=-1),
                       lambda s: s['totals'].update(out=True),
                       lambda s: s['periods']['month'].update({'in': '30'}),
                       lambda s: s['users']['out'].append({'username': 'second', 'bytes': -5}),
                       lambda s: s['channels']['out'].append({'bytes': 10}),
                       lambda s: s['channels'].update({'in': [{'channel': f'c{i}', 'bytes': 1} for i in range(102)]}),
                       lambda s: s.update(last_poll='100')):
            state = valid_state()
            mutate(state)
            self.assertEqual(render(json.dumps(state).encode()), [])

    def test_missing_section_or_redis(self):
        for section in ('totals', 'periods', 'users', 'channels', 'last_poll'):
            state = valid_state()
            del state[section]
            with self.assertLogs(usage_module.logger, 'WARNING'):
                self.assertEqual(render(json.dumps(state).encode()), [])
        self.assertEqual(render(json.dumps(valid_state()).encode(), redis=False), [])

    def test_decoded_redis_string(self):
        rendered = '\n'.join(render(json.dumps(valid_state())))
        self.assertIn('dispatcharr_usage_bytes_total{direction="in"} 30', rendered)


if __name__ == '__main__':
    unittest.main()
