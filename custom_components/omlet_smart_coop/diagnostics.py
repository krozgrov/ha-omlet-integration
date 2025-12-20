from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN, CONF_API_KEY, CONF_WEBHOOK_ID, CONF_WEBHOOK_TOKEN

_REDACT_KEYS = {
    CONF_API_KEY,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_TOKEN,
    "api_key",
    "token",
    "secret",
    "webhook_token",
    "webhook_id",
}


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    return async_redact_data(data, _REDACT_KEYS)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id, {}) or {}
    coordinator = entry_data.get("coordinator")

    diag: dict[str, Any] = {
        "entry": {
            "title": config_entry.title,
            "data": dict(config_entry.data),
            "options": dict(config_entry.options),
        },
        "coordinator": {
            "last_update_success": getattr(coordinator, "last_update_success", None),
            "last_update_time": getattr(coordinator, "last_update_time", None),
            "devices": getattr(coordinator, "devices", {}),
            "data": getattr(coordinator, "data", {}),
        },
    }

    return _redact(diag)


async def async_get_device_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry, device
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    entry_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id, {}) or {}
    coordinator = entry_data.get("coordinator")

    device_registry = async_get_device_registry(hass)
    ha_device = device_registry.async_get(device.id)
    identifier = None
    if ha_device:
        identifier = next(
            (value for domain, value in ha_device.identifiers if domain == DOMAIN),
            None,
        )

    device_data: dict[str, Any] = {}
    if identifier and coordinator:
        device_data = coordinator.data.get(identifier) or {}
        if not device_data:
            for data in (coordinator.data or {}).values():
                if data.get("deviceSerial") == identifier:
                    device_data = data
                    break

    diag = {
        "device": {
            "id": device.id,
            "name": device.name,
            "identifiers": list(device.identifiers),
        },
        "device_data": device_data,
    }
    return _redact(diag)
