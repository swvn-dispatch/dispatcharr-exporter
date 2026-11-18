"""Shared utility functions used across all modules."""

import logging
import re

logger = logging.getLogger(__name__)


def escape_label(value) -> str:
    """Escape a string for use as a Prometheus label value.

    Order is critical: escape backslashes first, then double-quotes, then line
    breaks. Carriage returns are normalized to newlines because the Prometheus
    text format has no standalone carriage-return escape sequence.
    """
    if not value:
        return ""
    return str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\r', '\\n').replace('\n', '\\n')


def normalize_host(host, default: str) -> str:
    """Return a clean host string, falling back to *default* if empty/None."""
    if host is None or not str(host).strip():
        return default
    return str(host).strip()


def redis_decode(value, default: str = '') -> str:
    """Decode a Redis bytes value to str, returning *default* if None."""
    if value is None:
        return default
    return value.decode('utf-8') if isinstance(value, bytes) else str(value)


def get_dispatcharr_version():
    """Return ``(version, timestamp, full_version)`` for the running Dispatcharr instance."""
    import sys

    dispatcharr_version = "unknown"
    dispatcharr_timestamp = None

    try:
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')
        import version  # Dispatcharr's version module
        dispatcharr_version = getattr(version, '__version__', 'unknown')
        dispatcharr_timestamp = getattr(version, '__timestamp__', None)
    except Exception:
        try:
            with open('/app/version.py', 'r') as f:
                content = f.read()
            m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
            if m:
                dispatcharr_version = m.group(1)
            m = re.search(r"__timestamp__\s*=\s*['\"]([^'\"]+)['\"]", content)
            if m:
                dispatcharr_timestamp = m.group(1)
        except Exception:
            pass

    full_version = dispatcharr_version
    if dispatcharr_timestamp:
        full_version = f"v{dispatcharr_version}-{dispatcharr_timestamp}"

    return dispatcharr_version, dispatcharr_timestamp, full_version
