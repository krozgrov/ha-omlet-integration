from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from ipaddress import ip_address
import logging
import secrets
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from aiohttp.web_request import Request
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

_DOMAIN = "omlet_smart_coop"
_CONF_WEBHOOK_ID = "webhook_id"

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


@dataclass(frozen=True)
class WebhookTokenDetails:
    """Token value and redacted source metadata for diagnostics."""

    token: str | None
    source: str | None


@dataclass(frozen=True)
class WebhookUrlInfo:
    """Generated webhook URL and any reachability warning."""

    url: str
    warning: str | None = None

    @property
    def is_publicly_reachable(self) -> bool:
        """Return whether the URL looks usable by Omlet's cloud service."""
        return self.warning is None


def _normalize_token(value: Any) -> str | None:
    """Normalize a token value by trimming whitespace and coercing to str."""
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _get_mapping_value(mapping: Any, key: str) -> Any:
    """Return a value from a mapping-like object without assuming its type."""
    try:
        return mapping.get(key)
    except AttributeError:
        return None


def get_expected_webhook_token(entry: ConfigEntry) -> str | None:
    """Return the configured webhook token, if any."""
    options = getattr(entry, "options", {}) or {}
    for key in _TOKEN_OPTION_KEYS:
        token = _normalize_token(_get_mapping_value(options, key))
        if token:
            return token
    return None


def get_provided_webhook_token(request: Request, payload: dict[str, Any] | None) -> str | None:
    """Extract a webhook token from headers, payload, or query params."""
    return get_provided_webhook_token_details(request, payload).token


def get_provided_webhook_token_details(
    request: Request, payload: dict[str, Any] | None
) -> WebhookTokenDetails:
    """Extract a webhook token with redacted source metadata."""
    headers = getattr(request, "headers", {}) or {}
    query = getattr(request, "query", {}) or {}

    auth_header = _get_mapping_value(headers, "Authorization")
    if auth_header:
        auth_value = str(auth_header).strip()
        if " " in auth_value:
            scheme, value = auth_value.split(" ", 1)
            if scheme.lower() in _AUTH_SCHEMES:
                auth_value = value.strip()
        token = _normalize_token(auth_value)
        if token:
            return WebhookTokenDetails(token=token, source="header:Authorization")
    for header in _TOKEN_HEADER_KEYS:
        token = _normalize_token(_get_mapping_value(headers, header))
        if token:
            return WebhookTokenDetails(token=token, source=f"header:{header}")
    if isinstance(payload, dict):
        payload_candidates = [payload]
        nested_payload = payload.get("payload")
        if isinstance(nested_payload, dict):
            payload_candidates.append(nested_payload)
        for index, candidate in enumerate(payload_candidates):
            source_prefix = "payload" if index == 0 else "payload.payload"
            for key in ("token", "secret", "webhook_token", "webhookToken"):
                token = _normalize_token(candidate.get(key))
                if token:
                    return WebhookTokenDetails(
                        token=token,
                        source=f"{source_prefix}:{key}",
                    )
    for key in _TOKEN_QUERY_KEYS:
        token = _normalize_token(_get_mapping_value(query, key))
        if token:
            return WebhookTokenDetails(token=token, source=f"query:{key}")
    return WebhookTokenDetails(token=None, source=None)


def get_webhook_payload_shape(payload: Any) -> str:
    """Return a compact description of the incoming payload shape."""
    if payload is None:
        return "non-json-or-empty"
    if not isinstance(payload, dict):
        return type(payload).__name__
    if isinstance(payload.get("payload"), dict):
        return "nested-payload"
    return "top-level"


def extract_webhook_event(payload: Any) -> dict[str, Any]:
    """Return the Omlet event fields from either known payload shape."""
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("payload")
    if isinstance(nested, dict):
        return nested
    return payload


def webhook_id_suffix(webhook_id: str | None) -> str:
    """Return a short redacted webhook ID suffix for logs."""
    if not webhook_id:
        return "missing"
    return webhook_id[-6:]


def _make_response(
    response_factory: Callable[..., Any] | None,
    *,
    status: int = 200,
    text: str = "ok",
) -> Any:
    """Create an aiohttp response, allowing tests to inject a tiny stand-in."""
    if response_factory is not None:
        return response_factory(status=status, text=text)

    from aiohttp.web import Response

    return Response(status=status, text=text)


def create_omlet_webhook_handler(
    entry: ConfigEntry,
    coordinator: Any,
    *,
    response_factory: Callable[..., Any] | None = None,
    logger: logging.Logger | None = None,
) -> Callable[[HomeAssistant, str, Request], Any]:
    """Create the shared Omlet webhook handler."""
    log = logger or _LOGGER

    async def _handle_webhook(hass: HomeAssistant, webhook_id_recv: str, request: Request):
        payload: Any = None
        token_details = WebhookTokenDetails(token=None, source=None)
        hook_suffix = webhook_id_suffix(webhook_id_recv)

        try:
            try:
                payload = await request.json()
            except Exception as err:
                log.debug(
                    "Omlet webhook %s received non-JSON payload; accepting for refresh: %s",
                    hook_suffix,
                    type(err).__name__,
                )

            payload_shape = get_webhook_payload_shape(payload)
            expected = get_expected_webhook_token(entry)
            if expected:
                token_details = get_provided_webhook_token_details(request, payload)
                if token_details.token != expected:
                    log.warning(
                        "Rejected Omlet webhook %s: invalid token "
                        "(payload_shape=%s, token_source=%s)",
                        hook_suffix,
                        payload_shape,
                        token_details.source or "missing",
                    )
                    return _make_response(
                        response_factory,
                        status=401,
                        text="invalid token",
                    )

            event = extract_webhook_event(payload)
            log.debug(
                "Accepted Omlet webhook %s: payload_shape=%s token_source=%s "
                "device=%s param=%s old=%s new=%s",
                hook_suffix,
                payload_shape,
                token_details.source if expected else "not-required",
                event.get("deviceId"),
                event.get("parameterName"),
                event.get("oldValue"),
                event.get("newValue"),
            )
        except Exception:
            log.exception(
                "Error validating Omlet webhook %s; accepting request to avoid retries",
                hook_suffix,
            )
            return _make_response(response_factory, text="ok")

        if coordinator is None:
            log.warning(
                "Accepted Omlet webhook %s but no coordinator is loaded; skipping refresh",
                hook_suffix,
            )
            return _make_response(response_factory, text="ok")

        refresh_task = None
        try:
            refresh_task = coordinator.async_request_refresh()
            hass.async_create_task(refresh_task)
            log.debug("Scheduled Omlet webhook refresh for webhook %s", hook_suffix)
        except Exception as err:
            if hasattr(refresh_task, "close"):
                refresh_task.close()
            log.debug(
                "Failed to schedule Omlet webhook refresh for webhook %s: %r",
                hook_suffix,
                err,
            )
        return _make_response(response_factory, text="ok")

    return _handle_webhook


def unregister_omlet_webhook(hass: HomeAssistant, webhook_id: str | None) -> None:
    """Unregister an Omlet webhook ID if present."""
    if not webhook_id:
        return

    from homeassistant.components import webhook as hass_webhook

    hass_webhook.async_unregister(hass, webhook_id)


def ensure_omlet_webhook_id(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Return a stable random webhook ID, migrating away from the legacy fixed ID."""
    webhook_id = (getattr(entry, "data", {}) or {}).get(_CONF_WEBHOOK_ID)
    if webhook_id == _DOMAIN:
        try:
            unregister_omlet_webhook(hass, _DOMAIN)
        except Exception:
            pass
        webhook_id = None

    if webhook_id:
        return webhook_id

    webhook_id = secrets.token_hex(16)
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, _CONF_WEBHOOK_ID: webhook_id},
    )
    return webhook_id


def rotate_omlet_webhook_id(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Rotate the random Omlet webhook ID and unregister the previous value."""
    old_id = (getattr(entry, "data", {}) or {}).get(_CONF_WEBHOOK_ID)
    try:
        unregister_omlet_webhook(hass, old_id)
    except Exception:
        pass

    new_id = secrets.token_hex(16)
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, _CONF_WEBHOOK_ID: new_id},
    )
    return new_id


def describe_webhook_url(url: str) -> str | None:
    """Return a warning if a webhook URL does not look internet-reachable."""
    if not url:
        return "No webhook URL could be generated."
    if url.startswith("/"):
        return "Generated URL is path-only; Omlet needs a full public HTTPS URL."

    parsed = urlparse(url)
    host = parsed.hostname
    if not parsed.scheme or not host:
        return "Generated URL is missing a scheme or hostname."

    normalized_host = host.lower().rstrip(".")
    if normalized_host in {"localhost", "0.0.0.0"}:
        return "Generated URL points to localhost; Omlet cannot reach it."
    if normalized_host.endswith(".local"):
        return "Generated URL uses a .local hostname; Omlet cannot resolve it."

    try:
        address = ip_address(normalized_host)
    except ValueError:
        return None

    if address.is_loopback:
        return "Generated URL points to a loopback address; Omlet cannot reach it."
    if address.is_private or address.is_link_local:
        return "Generated URL points to a private LAN address; Omlet cannot reach it."
    return None


def build_webhook_url_info(hass: HomeAssistant, webhook_id: str) -> WebhookUrlInfo:
    """Build a webhook URL, preferring Home Assistant's external URL."""
    url: str | None = None
    generation_errors: list[Exception] = []

    try:
        from homeassistant.components import webhook as hass_webhook

        try:
            url = hass_webhook.async_generate_url(
                hass,
                webhook_id,
                allow_internal=False,
                allow_external=True,
                prefer_external=True,
            )
        except TypeError:
            url = hass_webhook.async_generate_url(hass, webhook_id)
    except Exception as err:
        generation_errors.append(err)

    if not url:
        try:
            from homeassistant.helpers.network import get_url

            try:
                base = get_url(
                    hass,
                    allow_internal=False,
                    allow_external=True,
                    prefer_external=True,
                )
            except TypeError:
                base = get_url(hass)
            url = f"{base}/api/webhook/{webhook_id}"
        except Exception as err:
            generation_errors.append(err)
            url = f"/api/webhook/{webhook_id}"

    warning = describe_webhook_url(url)
    if generation_errors:
        _LOGGER.debug(
            "Webhook URL generation fallback used for webhook %s: %r",
            webhook_id_suffix(webhook_id),
            generation_errors,
        )
    return WebhookUrlInfo(url=url, warning=warning)


def format_webhook_url_message(prefix: str, url_info: WebhookUrlInfo) -> str:
    """Format a user-facing webhook URL notification."""
    msg = (
        f"{prefix} {url_info.url}. "
        "Use a publicly reachable external URL in Omlet Developer Portal > Manage Webhooks."
    )
    if url_info.warning:
        msg = f"{msg} Warning: {url_info.warning}"
    return msg


def register_omlet_webhook(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: Any,
    webhook_id: str,
    *,
    source: str,
) -> WebhookUrlInfo:
    """Register the shared Omlet webhook handler and return the URL info."""
    from homeassistant.components import webhook as hass_webhook

    try:
        unregister_omlet_webhook(hass, webhook_id)
    except Exception:
        pass

    handler = create_omlet_webhook_handler(entry, coordinator)
    try:
        hass_webhook.async_register(
            hass,
            _DOMAIN,
            "Omlet Smart Coop",
            webhook_id,
            handler,
            local_only=False,
        )
    except TypeError:
        hass_webhook.async_register(
            hass,
            _DOMAIN,
            "Omlet Smart Coop",
            webhook_id,
            handler,
        )

    url_info = build_webhook_url_info(hass, webhook_id)
    _LOGGER.info(
        "Omlet Smart Coop webhook enabled from %s (id suffix=%s). URL: %s",
        source,
        webhook_id_suffix(webhook_id),
        url_info.url,
    )
    if url_info.warning:
        _LOGGER.warning(
            "Omlet Smart Coop webhook URL may fail from Omlet: %s", url_info.warning
        )
    return url_info
