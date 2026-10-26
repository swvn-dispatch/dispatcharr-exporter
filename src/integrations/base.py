"""Types shared by external metrics integrations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Integration:
    """An external metrics producer and its exporter settings."""

    name: str
    description: str
    collect_metrics: object
    fields: tuple[dict, ...] = ()
