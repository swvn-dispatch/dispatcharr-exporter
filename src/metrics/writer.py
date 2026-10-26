"""Safe, deterministic Prometheus text-format metric rendering."""

import math
import re

from ..utils import escape_label

_METRIC_NAME = re.compile(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$")
_LABEL_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class MetricsWriter:
    """Build Prometheus metric families while enforcing their declarations."""

    def __init__(self):
        self._families = {}
        self._lines = []

    def gauge(self, name: str, help_text: str):
        """Return a gauge family builder."""
        return self._family(name, help_text, "gauge")

    def counter(self, name: str, help_text: str):
        """Return a counter family builder."""
        return self._family(name, help_text, "counter")

    def info(self, name: str, help_text: str):
        """Return an info-style gauge family builder."""
        return self._family(name, help_text, "gauge", info=True)

    def histogram(self, name: str, help_text: str):
        """Return a histogram family builder."""
        return _HistogramFamily(self, name, help_text)

    def summary(self, name: str, help_text: str):
        """Return a summary family builder."""
        return _SummaryFamily(self, name, help_text)

    def separator(self):
        """Separate logical metric groups without producing repeated blanks."""
        if self._lines and self._lines[-1] != "":
            self._lines.append("")

    def drain(self) -> list:
        """Return rendered lines emitted since the previous drain."""
        lines = self._lines
        self._lines = []
        return lines

    def _family(self, name: str, help_text: str, metric_type: str, info=False):
        return _MetricFamily(self, name, help_text, metric_type, info=info)

    def _declare(self, name: str, help_text: str, metric_type: str):
        if not _METRIC_NAME.match(name):
            raise ValueError(f"Invalid Prometheus metric name: {name!r}")
        if not isinstance(help_text, str) or not help_text:
            raise ValueError(f"Metric {name} must have help text")

        existing = self._families.get(name)
        declaration = (help_text, metric_type)
        if existing:
            if existing != declaration:
                raise ValueError(f"Conflicting declaration for metric {name}")
        else:
            self._families[name] = declaration
            self._lines.append(f"# HELP {name} {help_text}")
            self._lines.append(f"# TYPE {name} {metric_type}")
        return _FamilyEmitter(self, name)


class _FamilyEmitter:
    def __init__(self, writer: MetricsWriter, name: str):
        self.writer = writer
        self.name = name

    def emit(self, value, labels=None, suffix="") -> bool:
        value_text = _format_value(value)
        if value_text is None:
            return False
        labels_text = _format_labels(labels)
        self.writer._lines.append(f"{self.name}{suffix}{labels_text} {value_text}")
        return True


class _MetricFamily:
    def __init__(self, writer: MetricsWriter, name: str, help_text: str, metric_type: str, info=False):
        self._writer = writer
        self._name = name
        self._help_text = help_text
        self._metric_type = metric_type
        self._info = info

    def add(self, value=1, labels=None) -> bool:
        """Add one numeric sample, or an info sample with value one."""
        if self._info:
            if labels is None:
                labels = value
            value = 1
        if _format_value(value) is None:
            return False
        _format_labels(labels)
        return self._writer._declare(self._name, self._help_text, self._metric_type).emit(value, labels)


class _HistogramFamily:
    def __init__(self, writer: MetricsWriter, name: str, help_text: str):
        self._writer = writer
        self._name = name
        self._help_text = help_text

    def _emitter(self):
        return self._writer._declare(self._name, self._help_text, "histogram")

    def bucket(self, upper_bound, count, labels=None) -> bool:
        if _format_value(count) is None:
            return False
        labels = _append_label(labels, "le", upper_bound)
        _format_labels(labels)
        return self._emitter().emit(count, labels, "_bucket")

    def count(self, value, labels=None) -> bool:
        if _format_value(value) is None:
            return False
        _format_labels(labels)
        return self._emitter().emit(value, labels, "_count")

    def sum(self, value, labels=None) -> bool:
        if _format_value(value) is None:
            return False
        _format_labels(labels)
        return self._emitter().emit(value, labels, "_sum")


class _SummaryFamily:
    def __init__(self, writer: MetricsWriter, name: str, help_text: str):
        self._writer = writer
        self._name = name
        self._help_text = help_text

    def _emitter(self):
        return self._writer._declare(self._name, self._help_text, "summary")

    def quantile(self, quantile, value, labels=None) -> bool:
        if _format_value(value) is None:
            return False
        labels = _append_label(labels, "quantile", quantile)
        _format_labels(labels)
        return self._emitter().emit(value, labels)

    def count(self, value, labels=None) -> bool:
        if _format_value(value) is None:
            return False
        _format_labels(labels)
        return self._emitter().emit(value, labels, "_count")

    def sum(self, value, labels=None) -> bool:
        if _format_value(value) is None:
            return False
        _format_labels(labels)
        return self._emitter().emit(value, labels, "_sum")


def _format_value(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return str(int(number)) if number.is_integer() else repr(number)


def _format_labels(labels) -> str:
    if not labels:
        return ""
    items = sorted(labels.items()) if isinstance(labels, dict) else labels
    rendered = []
    for name, value in items:
        if not _LABEL_NAME.match(name):
            raise ValueError(f"Invalid Prometheus label name: {name!r}")
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        rendered.append(f'{name}="{escape_label(value)}"')
    return "{" + ",".join(rendered) + "}"


def _append_label(labels, name, value):
    items = list(labels.items()) if isinstance(labels, dict) else list(labels or ())
    items.append((name, value))
    return items
