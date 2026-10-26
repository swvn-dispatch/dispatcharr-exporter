"""Dispatcharr user metric collection."""

import logging

logger = logging.getLogger(__name__)


def collect_user_metrics(context, writer) -> None:
    """Write active user metadata, limits, and active stream counts."""
    from apps.accounts.models import User

    active_streams_by_user = _active_streams_by_user(context.redis_client)
    user_info = writer.info("dispatcharr_user_info", "Dispatcharr user information")
    joined = writer.gauge("dispatcharr_user_date_joined_timestamp", "Unix timestamp of when the user account was created")
    stream_limit = writer.gauge("dispatcharr_user_stream_limit", "Configured concurrent stream limit for user (0 = unlimited)")
    active_streams = writer.gauge("dispatcharr_user_active_streams", "Current number of active streams for user")

    try:
        for user in User.objects.filter(is_active=True).order_by("id"):
            if not (user.custom_properties or {}).get("xc_password"):
                continue
            user_level = "admin" if user.user_level >= 10 else "standard" if user.user_level >= 1 else "streamer"
            info_labels = [
                ("user_id", user.id),
                ("username", user.username),
                ("user_level", user_level),
                ("is_staff", str(user.is_staff).lower()),
            ]
            identity_labels = [("user_id", user.id), ("username", user.username)]
            user_info.add(info_labels)
            joined.add(int(user.date_joined.timestamp()) if user.date_joined else 0, identity_labels)
            stream_limit.add(user.stream_limit, identity_labels)
            active_streams.add(active_streams_by_user.get(user.id, 0), identity_labels)
    except Exception as exc:
        logger.error("Error collecting user metrics: %s", exc)
    writer.separator()


def _active_streams_by_user(redis_client) -> dict:
    """Return the number of live and VOD streams attributed to each user."""
    if not redis_client:
        return {}

    active_streams = {}
    try:
        from apps.proxy.live_proxy.constants import ChannelMetadataField  # noqa: F401
        redis_key_prefix = "live"
    except ImportError:
        redis_key_prefix = "ts_proxy"

    try:
        for key in redis_client.scan_iter(match=f"{redis_key_prefix}:channel:*:clients:*", count=1000):
            user_id = redis_client.hget(key, "user_id")
            if user_id:
                try:
                    user_id = int(user_id)
                    active_streams[user_id] = active_streams.get(user_id, 0) + 1
                except (ValueError, TypeError):
                    pass
        for key in redis_client.scan_iter(match="vod_persistent_connection:*", count=1000):
            user_id = redis_client.hget(key, "user_id")
            active = redis_client.hget(key, "active_streams")
            try:
                if user_id and int(active or 0) > 0:
                    user_id = int(user_id)
                    active_streams[user_id] = active_streams.get(user_id, 0) + 1
            except (ValueError, TypeError):
                pass
    except Exception as exc:
        logger.error("Error counting active streams per user: %s", exc, exc_info=True)
    return active_streams
