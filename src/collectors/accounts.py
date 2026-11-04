"""M3U account and profile connection metrics."""

import logging
from datetime import datetime, timezone

try:
    from apps.proxy.live_proxy.constants import ChannelMetadataField
    _CHANNEL_KEY_PREFIX = "live"
except ImportError:
    from apps.proxy.ts_proxy.constants import ChannelMetadataField
    _CHANNEL_KEY_PREFIX = "ts_proxy"

logger = logging.getLogger(__name__)


def collect_account_metrics(context, writer) -> None:
    """Write M3U account and profile metrics."""
    collect_m3u_account_metrics(context, writer)
    collect_profile_metrics(context, writer)
    writer.separator()


def collect_m3u_account_metrics(context, writer) -> None:
    from apps.m3u.models import M3UAccount

    accounts = writer.gauge("dispatcharr_m3u_accounts", "Total number of M3U accounts")
    statuses = writer.gauge("dispatcharr_m3u_account_status", "M3U account status breakdown")
    account_info = writer.info("dispatcharr_m3u_account_info", "M3U account configuration")
    stream_count_metric = writer.gauge(
        "dispatcharr_m3u_account_stream_count",
        "Number of streams configured for this M3U account",
    )
    include_urls = context.settings.get("include_source_urls", False)
    try:
        all_accounts = M3UAccount.objects.exclude(name__iexact="custom")
        accounts.add(all_accounts.count(), [("status", "total")])
        accounts.add(all_accounts.filter(is_active=True).count(), [("status", "active")])
        for status_value, _label in M3UAccount.Status.choices:
            statuses.add(all_accounts.filter(status=status_value).count(), [("status", status_value)])
        for account in all_accounts:
            account_type = account.account_type or "unknown"
            labels = [
                ("account_id", account.id),
                ("account_name", account.name),
                ("account_type", account_type),
                ("status", account.status),
                ("is_active", str(account.is_active).lower()),
            ]
            if include_urls and account_type == "XC" and getattr(account, "username", None):
                labels.append(("username", account.username))
            if include_urls and account.server_url:
                labels.append(("server_url", account.server_url))
            account_info.add(labels)
            stream_count_metric.add(account.streams.count() if hasattr(account, "streams") else 0, labels)
    except Exception as exc:
        logger.error("Error collecting M3U account metrics: %s", exc)


def collect_profile_metrics(context, writer) -> None:
    from apps.m3u.models import M3UAccountProfile

    if not context.redis_client:
        return
    connections = writer.gauge("dispatcharr_profile_connections", "Current connections per M3U profile")
    maximum = writer.gauge("dispatcharr_profile_max_connections", "Maximum allowed connections per M3U profile")
    usage_metric = writer.gauge("dispatcharr_profile_connection_usage", "Connection usage ratio per M3U profile")
    expiry_metric = writer.gauge(
        "dispatcharr_profile_days_to_expiry",
        "Days remaining until XC profile expiry (0 if expired, -1 if no expiry set)",
    )
    try:
        actual_connections = _profile_connection_counts(context.redis_client)
        for profile in M3UAccountProfile.objects.all():
            try:
                if profile.m3u_account.name.lower() == "custom":
                    continue
                labels = [
                    ("profile_id", profile.id),
                    ("profile_name", profile.name),
                    ("account_name", profile.m3u_account.name),
                ]
                current = actual_connections.get(profile.id, 0)
                max_connections = profile.max_streams
                connections.add(current, labels)
                maximum.add(max_connections, labels)
                if max_connections > 0:
                    usage_metric.add(current / max_connections, labels)
                if profile.m3u_account.account_type == "XC":
                    remaining = -1
                    expiry = (profile.custom_properties or {}).get("user_info", {}).get("exp_date")
                    if expiry:
                        try:
                            expiry_at = datetime.fromtimestamp(float(expiry), tz=timezone.utc)
                            remaining = max(0, (expiry_at - datetime.fromtimestamp(context.timestamp, tz=timezone.utc)).days)
                        except (TypeError, ValueError) as exc:
                            logger.debug("Error calculating expiry for profile %s: %s", profile.id, exc)
                    expiry_metric.add(remaining, labels)
            except Exception as exc:
                logger.debug("Error getting connections for profile %s: %s", profile.id, exc)
    except Exception as exc:
        logger.error("Error collecting profile metrics: %s", exc)


def _profile_connection_counts(redis_client):
    counts = {}
    try:
        from apps.channels.models import Channel
        for key in redis_client.scan_iter(match="channel_stream:*"):
            try:
                channel_id = _text(key).split(":", 1)[1]
                channel = Channel.objects.get(id=int(channel_id))
                metadata = redis_client.hgetall(f"{_CHANNEL_KEY_PREFIX}:channel:{channel.uuid}:metadata") or {}
                profile = metadata.get(ChannelMetadataField.M3U_PROFILE)
                if profile and _text(profile) != "0":
                    profile_id = int(profile)
                    counts[profile_id] = counts.get(profile_id, 0) + 1
            except Exception as exc:
                logger.debug("Error processing stream key for profile counting: %s", exc)
    except Exception as exc:
        logger.debug("Error calculating live channel profile connections: %s", exc)
    try:
        for key in redis_client.scan_iter(match="vod_persistent_connection:*"):
            try:
                data = redis_client.hgetall(key) or {}
                profile = _field(data, "m3u_profile_id")
                if profile and int(_field(data, "active_streams", "0")) > 0:
                    profile_id = int(profile)
                    counts[profile_id] = counts.get(profile_id, 0) + 1
            except Exception as exc:
                logger.debug("Error processing VOD connection key for profile counting: %s", exc)
    except Exception as exc:
        logger.debug("Error calculating VOD profile connections: %s", exc)
    return counts


def _field(data, name, default=""):
    return _text(data.get(name, data.get(name.encode(), default)), default)


def _text(value, default=""):
    if value is None:
        return default
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)
