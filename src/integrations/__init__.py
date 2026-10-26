"""Optional metrics collected from external plugins and services.

Each registered integration owns its producer contract and must fail without
affecting the core Dispatcharr metrics scrape.
"""

import logging
import re

from .packet_slapper import INTEGRATION as PACKET_SLAPPER_INTEGRATION

logger = logging.getLogger(__name__)

_INTEGRATIONS = (
    PACKET_SLAPPER_INTEGRATION,
)


def _validate_integrations() -> tuple:
    """Return integration fields after enforcing the opt-in contract."""
    fields = []
    field_ids = set()

    for integration in _INTEGRATIONS:
        if not isinstance(integration.name, str) or not integration.name.strip():
            raise ValueError("Integration name must be a non-empty string")
        if not isinstance(integration.description, str) or not integration.description.strip():
            raise ValueError(f"Integration {integration.name} must have a description")

        enabled_field_id = _enabled_field_id(integration)
        if enabled_field_id in field_ids:
            raise ValueError(f"Integration {integration.name} has a duplicate generated setting ID")

        field_ids.add(enabled_field_id)
        fields.append(
            {
                "id": enabled_field_id,
                "label": f"Include {integration.name} Statistics",
                "type": "boolean",
                "default": False,
                "description": integration.description,
            }
        )

        for field in integration.fields:
            if not isinstance(field, dict):
                raise ValueError(f"Integration {integration.name} has an invalid setting definition")
            field_id = field.get("id")
            if not field_id or field_id in field_ids:
                raise ValueError(f"Integration {integration.name} has an invalid or duplicate setting ID")
            if not all(key in field for key in ("label", "type", "default", "description")):
                raise ValueError(f"Integration {integration.name} has an incomplete setting definition")

            field_ids.add(field_id)
            fields.append(dict(field))

    return tuple(fields)


def _enabled_field_id(integration) -> str:
    """Return the generated disabled-by-default setting ID for an integration."""
    slug = re.sub(r"[^a-z0-9]+", "_", integration.name.lower()).strip("_")
    if not slug:
        raise ValueError("Integration name must contain letters or numbers")
    return f"include_{slug}_stats"


INTEGRATION_FIELDS = _validate_integrations()


def collect_enabled_metrics(context, writer) -> None:
    """Write metrics for enabled external integrations."""
    settings = context.settings
    for integration in _INTEGRATIONS:
        if not settings.get(_enabled_field_id(integration), False):
            continue
        try:
            integration.collect_metrics(context, writer)
        except Exception as exc:
            logger.warning("Error collecting %s integration metrics: %s", integration.name, exc)
