from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from omlet_sdk import OmletClient

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Omlet integration using YAML (not supported)."""
    # This integration uses UI-based configuration only
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omlet integration from a config entry."""
    # Ensure the domain key exists in the shared data store
    hass.data.setdefault(DOMAIN, {})

    # Get API key from the config entry
    api_key = entry.data["api_key"]

    # Initialize the OmletClient and store it in hass.data
    client = OmletClient(api_key=api_key)
    hass.data[DOMAIN][entry.entry_id] = client

    # Forward the setup to supported platforms (e.g., sensor, switch)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms associated with the entry
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Remove the client from the shared data store
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok