"""Prometheus metrics collector.

Queries Dispatcharr's Django models and Redis state on every scrape request
and returns the complete metrics output in Prometheus text format.
"""

import logging
import time

from .collectors import collect_core_metrics
from .integrations import collect_enabled_metrics
from .metrics import MetricsWriter, ScrapeContext

logger = logging.getLogger(__name__)

class PrometheusMetricsCollector:
    """Orchestrates all metric collection and formats output."""

    def __init__(self):
        self.redis_client = None  # lazy-loaded on first scrape

    def collect_metrics(self, settings: dict = None) -> str:
        """Collect all metrics and return Prometheus text format."""
        if self.redis_client is None:
            try:
                from core.utils import RedisClient
                self.redis_client = RedisClient.get_client()
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")

        settings = settings or {}

        # Fetch catch-up (timeshift) session data once per scrape and share it
        # between _collect_stream_metrics and _collect_client_metrics, rather
        # than each calling build_timeshift_stats_data() independently.
        timeshift_data = None
        try:
            from apps.timeshift.stats import build_timeshift_stats_data
            timeshift_data = build_timeshift_stats_data(self.redis_client)
        except ImportError:
            pass  # Older Dispatcharr builds without the timeshift app
        except Exception as e:
            logger.debug(f"Error building timeshift stats data: {e}")

        context = ScrapeContext(
            redis_client=self.redis_client,
            settings=settings,
            timeshift_data=timeshift_data,
            timestamp=time.time(),
        )
        writer = MetricsWriter()
        collect_core_metrics(context, writer)
        metrics = writer.drain()

        collect_enabled_metrics(context, writer)
        metrics.extend(writer.drain())

        return "\n".join(metrics)
