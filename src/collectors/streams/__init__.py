"""Active stream metrics split by live, VOD, and timeshift sources."""

from . import live, timeshift, vod
from .shared import stream_families


def collect_stream_metrics(context, writer) -> None:
    """Write stream families in their established source and sample order."""
    families = stream_families(writer)
    totals = {"all": 0, "live": 0, "vod": 0, "timeshift": 0}
    if context.redis_client:
        live.collect(context, families, totals)
        vod.collect(context, families, totals)
        timeshift.collect(context, families, totals)
        active = families["dispatcharr_active_streams"]
        active.add(totals["all"])
        for source in ("live", "vod", "timeshift"):
            active.add(totals[source], [("type", source)])
    writer.separator()


__all__ = ["collect_stream_metrics"]
