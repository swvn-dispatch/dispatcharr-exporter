"""Prometheus metrics published by the Stream Usage plugin."""
import json
import logging

from .base import Integration

REDIS_KEY = 'stream_usage:prometheus:latest'
MAX_PAYLOAD_BYTES = 64 * 1024
logger = logging.getLogger(__name__)


def collect_metrics(context, writer):
    if context.redis_client is None:
        return
    try:
        raw = context.redis_client.get(REDIS_KEY)
        if not raw or not isinstance(raw, (bytes, str)) or len(raw) > MAX_PAYLOAD_BYTES:
            return
        state = json.loads(raw)
        if not isinstance(state, dict) or state.get('v') != 1:
            return
        totals = state['totals']
        periods = state['periods']
        users = state['users']
        channels = state['channels']
        timestamp = state['last_poll']
        if not isinstance(totals, dict) or not isinstance(periods, dict) or not isinstance(users, dict) or not isinstance(channels, dict):
            return
        if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
            return
        for direction in ('out', 'in'):
            value = totals.get(direction)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                return
            for period in ('hour', 'today', 'week', 'month'):
                val = periods.get(period, {}).get(direction)
                if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                    return
            for group, label in ((users, 'username'), (channels, 'channel')):
                entries = group.get(direction, [])
                if not isinstance(entries, list) or len(entries) > 101:
                    return
                for entry in entries:
                    if (not isinstance(entry, dict) or not isinstance(entry.get(label), str)
                            or not isinstance(entry.get('bytes'), int) or entry['bytes'] < 0):
                        return
    except Exception as exc:
        logger.warning('Error reading Stream Usage metrics: %s', exc)
        return

    total_metric = writer.counter('dispatcharr_usage_bytes_total', 'Lifetime sampled stream bytes')
    user_metric = writer.counter('dispatcharr_usage_user_bytes_total', 'Lifetime sampled bytes by user')
    channel_metric = writer.counter('dispatcharr_usage_channel_bytes_total', 'Lifetime sampled bytes by channel')
    period_metric = writer.gauge('dispatcharr_usage_period_bytes', 'Sampled bytes in period')
    for direction in ('out', 'in'):
        total_metric.add(totals[direction], [('direction', direction)])
        for entry in users.get(direction, []):
            user_metric.add(entry['bytes'], [('username', entry['username']), ('direction', direction)])
        for entry in channels.get(direction, []):
            channel_metric.add(entry['bytes'], [('channel', entry['channel']), ('direction', direction)])
        for period in ('hour', 'today', 'week', 'month'):
            period_metric.add(periods[period][direction], [('period', period), ('direction', direction)])
    writer.gauge('dispatcharr_usage_last_poll_timestamp_seconds', 'Last Stream Usage poll Unix timestamp').add(timestamp)
    writer.separator()


INTEGRATION = Integration(
    name='Stream Usage',
    description='Include lifetime and period streaming byte totals from the Stream Usage plugin.',
    collect_metrics=collect_metrics,
)
