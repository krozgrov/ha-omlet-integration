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
    "X-Omlet-Auth-Token",
    "X-Omlet-Auth",
    "X-Api-Key",
    "X-Auth-Token",
)
_TOKEN_QUERY_KEYS = ("token", "secret", "webhook_token")
_AUTH_SCHEMES = ("bearer", "token", "apikey", "api-key")


def _normalize_token(value: Any) -> str | None:
    """Normalize a token value by trimming whitespace and coercing to str."""
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def get_expected_webhook_token(entry: ConfigEntry) -> str | None:
    """Return the configured webhook token, if any."""
    for key in _TOKEN_OPTION_KEYS:
        token = _normalize_token(entry.options.get(key))
        if token:
            return token
    return None


def get_provided_webhook_token(request: Request, payload: dict[str, Any] | None) -> str | None:
    """Extract a webhook token from headers, payload, or query params."""
    auth_header = request.headers.get("Authorization")
    if auth_header:
        auth_value = auth_header.strip()
        if " " in auth_value:
            scheme, value = auth_value.split(" ", 1)
            if scheme.lower() in _AUTH_SCHEMES:
                auth_value = value.strip()
        token = _normalize_token(auth_value)
        if token:
            return token
    for header in _TOKEN_HEADER_KEYS:
        token = _normalize_token(request.headers.get(header))
        if token:
            return token
    if payload:
        payload_candidates = [payload]
        nested_payload = payload.get("payload")
        if isinstance(nested_payload, dict):
            payload_candidates.append(nested_payload)
        for candidate in payload_candidates:
            for key in ("token", "secret", "webhook_token", "webhookToken"):
                token = _normalize_token(candidate.get(key))
                if token:
                    return token
    for key in _TOKEN_QUERY_KEYS:
        token = _normalize_token(request.query.get(key))
        if token:
            return token
    return None
