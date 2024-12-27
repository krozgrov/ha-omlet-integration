from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from smartcoop.client import SmartCoopClient
from smartcoop.api.omlet import Omlet


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Omlet integration using YAML (not supported)."""
    # This integration uses UI-based configuration only
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omlet integration from a config entry."""
    # Ensure the domain key exists in the shared data store
    hass.data.setdefault(DOMAIN, {})

    # Get client secret from the config entry
    client_secret = entry.data["client_secret"]

    try:
        # Initialize the SmartCoopClient and Omlet API
        client = SmartCoopClient(client_secret=client_secret)
        omlet = Omlet(client)
        hass.data[DOMAIN][entry.entry_id] = omlet  # Store the Omlet API instance
    except Exception as e:
        hass.logger.error(f"Error initializing SmartCoopClient: {e}")
        return False

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