from __future__ import annotations

from typing import Any

from aiohttp.web_request import Request
from homeassistant.config_entries import ConfigEntry

_TOKEN_OPTION_KEYS = ("webhook_token", "token", "secret", "WEBHOOK_TOKEN")
_TOKEN_HEADER_KEYS = (
    "X-Omlet-Token",
    "X-Omlet-Webhook-Token",
    "X-Webhook-Token",
    "X-Webhook-Secret",
    "X-Omlet-Secret",
)
_TOKEN_QUERY_KEYS = ("token", "secret", "webhook_token")


def get_expected_webhook_token(entry: ConfigEntry) -> str | None:
    """Return the configured webhook token, if any."""
    for key in _TOKEN_OPTION_KEYS:
        val = entry.options.get(key)
        if val:
            return str(val)
    return None


def get_provided_webhook_token(request: Request, payload: dict[str, Any] | None) -> str | None:
    """Extract a webhook token from headers, payload, or query params."""
    for header in _TOKEN_HEADER_KEYS:
        val = request.headers.get(header)
        if val:
            return val
    if payload:
        for key in ("token", "secret", "webhook_token", "webhookToken"):
            val = payload.get(key)
            if val:
                return str(val)
    for key in _TOKEN_QUERY_KEYS:
        val = request.query.get(key)
        if val:
            return val
    return None
