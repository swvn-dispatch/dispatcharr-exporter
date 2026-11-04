"""Per-scrape state shared by core collectors and integrations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapeContext:
    """Dependencies and cached state for one metrics scrape."""

    redis_client: object
    settings: dict
    timeshift_data: dict | None
    timestamp: float
