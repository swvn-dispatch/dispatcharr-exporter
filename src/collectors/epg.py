"""Dispatcharr EPG source metric collection."""

import logging

logger = logging.getLogger(__name__)


def collect_epg_metrics(context, writer) -> None:
    """Write EPG source status and priority metrics."""
    from apps.epg.models import EPGSource

    include_urls = context.settings.get("include_source_urls", False)
    try:
        sources = EPGSource.objects.exclude(source_type="dummy")
        source_totals = writer.gauge("dispatcharr_epg_sources", "Total number of EPG sources")
        source_totals.add(sources.count(), [("status", "total")])
        source_totals.add(sources.filter(is_active=True).count(), [("status", "active")])

        status_metric = writer.gauge("dispatcharr_epg_source_status", "EPG source status breakdown")
        for status_choice in EPGSource.STATUS_CHOICES:
            status_value = status_choice[0]
            status_metric.add(sources.filter(status=status_value).count(), [("status", status_value)])

        priority_metric = writer.gauge(
            "dispatcharr_epg_source_priority",
            "Priority value for EPG source (lower is higher priority)",
        )
        for source in sources:
            labels = [
                ("source_id", source.id),
                ("source_name", source.name),
                ("source_type", source.source_type or "unknown"),
                ("status", source.status),
                ("is_active", str(source.is_active).lower()),
            ]
            if include_urls and source.url:
                labels.append(("url", source.url))
            priority_metric.add(source.priority, labels)
    except Exception as exc:
        logger.error("Error collecting EPG metrics: %s", exc)
    writer.separator()
