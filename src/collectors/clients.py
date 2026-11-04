"""Individual live, VOD, and timeshift client metrics."""

import logging

try:
    from apps.proxy.live_proxy.constants import ChannelMetadataField
    _CHANNEL_KEY_PREFIX = "live"
except ImportError:
    from apps.proxy.ts_proxy.constants import ChannelMetadataField
    _CHANNEL_KEY_PREFIX = "ts_proxy"

logger = logging.getLogger(__name__)


def collect_client_metrics(context, writer) -> None:
    """Write client connection metrics when client metrics are enabled."""
    if not context.redis_client:
        return
    try:
        from apps.channels.models import Channel
        families = _families(writer)
        usernames = {}
        total = _collect_live(context, families, Channel, usernames)
        total += _collect_vod(context, families, usernames)
        total += _collect_timeshift(context, families, Channel)
        families["active"].add(total)
    except Exception as exc:
        logger.error("Error collecting client metrics: %s", exc)
    writer.separator()


def _families(writer):
    return {
        "active": writer.gauge("dispatcharr_active_clients", "Total number of active client connections (live, VOD, and timeshift)"),
        "info": writer.info("dispatcharr_client_info", "Client connection metadata (type: live/vod/timeshift)"),
        "duration": writer.gauge("dispatcharr_client_connection_duration_seconds", "Duration of client connection in seconds"),
        "bytes": writer.counter("dispatcharr_client_bytes_sent", "Total bytes sent to client"),
        "average": writer.gauge("dispatcharr_client_avg_transfer_rate_bps", "Average transfer rate to client in bits per second"),
        "current": writer.gauge("dispatcharr_client_current_transfer_rate_bps", "Current transfer rate to client in bits per second"),
    }


def _collect_live(context, families, Channel, usernames):
    total = 0
    cursor = 0
    while True:
        cursor, keys = context.redis_client.scan(cursor, match=f"{_CHANNEL_KEY_PREFIX}:channel:*:clients", count=100)
        for set_key in keys:
            try:
                parts = _text(set_key).split(":")
                if len(parts) < 4:
                    continue
                channel_uuid = parts[2]
                try:
                    channel = Channel.objects.get(uuid=channel_uuid)
                except Channel.DoesNotExist:
                    continue
                client_ids = context.redis_client.smembers(set_key)
                total += len(client_ids)
                for raw_client_id in client_ids:
                    try:
                        client_id = _text(raw_client_id)
                        data = context.redis_client.hgetall(f"{_CHANNEL_KEY_PREFIX}:channel:{channel_uuid}:clients:{client_id}") or {}
                        if not data:
                            continue
                        user_id = _field(data, "user_id", "0")
                        labels = [("type", "live"), ("client_id", client_id), ("channel_uuid", channel_uuid), ("channel_number", getattr(channel, "channel_number", "N/A"))]
                        _write_client(
                            families, labels,
                            [("ip_address", _field(data, "ip_address", "unknown")), ("user_agent", _agent(_field(data, "user_agent", "unknown"))), ("worker_id", _field(data, "worker_id", "unknown")), ("user_id", user_id), ("username", _username(user_id, usernames))],
                            _duration(context.timestamp, _field(data, "connected_at", "0")),
                            _integer(_field(data, "bytes_sent", "0")),
                            _rate(_field(data, "avg_rate_KBps", "0")),
                            _rate(_field(data, "current_rate_KBps", "0")),
                        )
                    except Exception as exc:
                        logger.debug("Error processing client %s: %s", raw_client_id, exc)
            except Exception as exc:
                logger.debug("Error processing client set %s: %s", set_key, exc)
        if cursor == 0:
            return total


def _collect_vod(context, families, usernames):
    total = 0
    try:
        cursor = 0
        while True:
            cursor, keys = context.redis_client.scan(cursor, match="vod_persistent_connection:*", count=100)
            for key in keys:
                try:
                    data = context.redis_client.hgetall(key) or {}
                    if not data or _integer(_field(data, "active_streams", "0")) == 0:
                        continue
                    total += 1
                    session_id = _text(key).replace("vod_persistent_connection:", "")
                    parts = session_id.split("_")
                    channel_number = parts[1] if len(parts) >= 2 else session_id
                    user_id = _field(data, "user_id", "0")
                    duration = _duration(context.timestamp, _field(data, "created_at", "0"))
                    sent = _integer(_field(data, "bytes_sent", "0"))
                    average = round(sent * 8 / duration, 2) if duration > 0 and sent > 0 else 0
                    labels = [("type", "vod"), ("client_id", session_id), ("channel_uuid", session_id), ("channel_number", channel_number)]
                    _write_client(
                        families, labels,
                        [("content_uuid", _field(data, "content_uuid")), ("channel_name", _field(data, "content_name", "Unknown")), ("content_type", _field(data, "content_obj_type", "unknown")), ("ip_address", _field(data, "client_ip", "unknown")), ("user_agent", _agent(_field(data, "client_user_agent", "unknown"))), ("worker_id", _field(data, "worker_id", "unknown")), ("user_id", user_id), ("username", _username(user_id, usernames))],
                        duration, sent, average, average,
                    )
                except Exception as exc:
                    logger.debug("Error processing VOD connection for clients: %s", exc)
            if cursor == 0:
                break
    except Exception as exc:
        logger.debug("Error scanning VOD connections for clients: %s", exc)
    return total


def _collect_timeshift(context, families, Channel):
    total = 0
    cache = {}
    def channel_number(channel_id):
        if channel_id not in cache:
            try:
                cache[channel_id] = Channel.objects.get(id=channel_id).channel_number
            except Exception:
                cache[channel_id] = "N/A"
        return cache[channel_id]
    try:
        for session in (context.timeshift_data or {}).get("timeshift_sessions", []):
            for connection in session.get("connections", []):
                total += 1
                labels = [("type", "timeshift"), ("client_id", connection.get("client_id", "")), ("channel_uuid", session.get("stats_channel_id", "")), ("channel_number", channel_number(session.get("channel_id")))]
                _write_client(
                    families, labels,
                    [("channel_name", session.get("channel_name", "Catch-up")), ("real_channel_uuid", session.get("channel_uuid", "")), ("session_id", connection.get("session_id", "")), ("ip_address", connection.get("ip_address", "unknown")), ("user_agent", _agent(connection.get("user_agent", "unknown"))), ("worker_id", "unknown"), ("user_id", connection.get("user_id", "0")), ("username", connection.get("username", "unknown"))],
                    connection.get("duration", 0), connection.get("bytes_streamed", 0), (connection.get("avg_bitrate_kbps") or 0) * 1000, (connection.get("avg_bitrate_kbps") or 0) * 1000,
                )
    except Exception as exc:
        logger.debug("Error collecting timeshift clients: %s", exc)
    return total


def _write_client(families, labels, info_labels, duration, sent, average, current):
    families["info"].add(labels + info_labels)
    if duration > 0:
        families["duration"].add(duration, labels)
    if sent > 0:
        families["bytes"].add(sent, labels)
    if average > 0:
        families["average"].add(average, labels)
    if current > 0:
        families["current"].add(current, labels)


def _username(user_id, cache):
    try:
        user_id = int(user_id)
        if user_id <= 0:
            return "anonymous"
        if user_id not in cache:
            from apps.accounts.models import User
            cache[user_id] = User.objects.get(id=user_id).username
        return cache[user_id]
    except Exception:
        return "anonymous"


def _field(data, name, default=""):
    return _text(data.get(name, data.get(name.encode(), default)), default)


def _text(value, default=""):
    if value is None:
        return default
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def _integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _duration(now, started):
    try:
        return max(0, int(now - float(started))) if float(started) > 0 else 0
    except (TypeError, ValueError):
        return 0


def _rate(value):
    try:
        value = float(value)
        return value * 8 if value > 50000 else value * 8000
    except (TypeError, ValueError):
        return 0


def _agent(value):
    return str(value).replace("\n", " ").replace("\r", "")
