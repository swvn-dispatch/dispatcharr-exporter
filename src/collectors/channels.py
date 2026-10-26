"""Dispatcharr channel metric collection."""

import logging

logger = logging.getLogger(__name__)


def collect_channel_metrics(context, writer) -> None:
    """Write channel totals and optionally per-channel configuration."""
    from apps.channels.models import Channel, ChannelGroup

    channels = writer.gauge("dispatcharr_channels", "Total number of channels")
    channel_groups = writer.gauge("dispatcharr_channel_groups", "Total number of channel groups")
    try:
        channels.add(Channel.objects.count(), [("status", "total")])
        channel_groups.add(ChannelGroup.objects.count())
    except Exception as exc:
        logger.error("Error collecting channel metrics: %s", exc)

    if context.settings.get("include_channel_info", False):
        _collect_channel_info_metrics(Channel, writer)
    writer.separator()


def _collect_channel_info_metrics(Channel, writer) -> None:
    """Write per-channel group, source, output, and catch-up information."""
    from django.db.models import Count

    try:
        channels = Channel.objects.select_related("channel_group").annotate(
            source_count=Count("streams"),
        ).order_by("channel_number")
        if not channels.exists():
            return

        channel_info = writer.info(
            "dispatcharr_channel_info",
            "Per-channel static configuration (group, catch-up, output visibility)",
        )
        source_count = writer.gauge(
            "dispatcharr_channel_source_count",
            "Number of streams/sources configured for this channel",
        )
        catchup_days_metric = writer.gauge(
            "dispatcharr_channel_catchup_days",
            "Number of days of catch-up buffer configured for this channel (0 if catch-up is disabled or unsupported)",
        )

        for channel in channels:
            channel_group_name = channel.channel_group.name if channel.channel_group else ""
            catchup_enabled = getattr(channel, "is_catchup", False)
            catchup_days = getattr(channel, "catchup_days", 0) or 0
            base_labels = [
                ("channel_id", channel.id),
                ("channel_number", channel.channel_number),
                ("channel_name", channel.name),
            ]
            channel_info.add(base_labels + [
                ("uuid", channel.uuid),
                ("channel_group", channel_group_name),
                ("tvg_id", channel.tvg_id),
                ("catchup_enabled", str(bool(catchup_enabled)).lower()),
                ("hidden_from_output", str(bool(getattr(channel, "hidden_from_output", False))).lower()),
            ])
            source_count.add(channel.source_count, base_labels)
            catchup_days_metric.add(catchup_days, base_labels)
    except Exception as exc:
        logger.error("Error collecting channel info metrics: %s", exc)
