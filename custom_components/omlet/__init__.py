from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import OmletDataCoordinator
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_POLLING_INTERVAL,
    CONF_DEFAULT_POLLING_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omlet Smart Coop from a config entry.

    Args:
        hass: The Home Assistant instance
        entry: The config entry to setup

    Returns:
        bool: True if setup was successful

    Raises:
        ConfigEntryNotReady: If setup fails
    """
    _LOGGER.info(
        "Setting up Omlet Smart Coop integration for entry: %s", entry.entry_id
    )

    # Ensure hass.data for DOMAIN is initialized
    hass.data.setdefault(DOMAIN, {})

    # Initialize the data coordinator
    try:
        coordinator = OmletDataCoordinator(
            hass,
            entry.data["api_key"],
            entry,
        )
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.error("Failed to initialize Omlet Smart Coop: %s", ex)
        raise ConfigEntryNotReady from ex

    # Store the coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Forward the entry to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add an update listener for handling options changes
    entry.add_update_listener(update_listener)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: The Home Assistant instance
        entry: The config entry to unload

    Returns:
        bool: True if unload was successful
    """
    _LOGGER.info("Unloading Omlet Smart Coop integration for entry: %s", entry.entry_id)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove stored data and clean up resources
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        coordinator = entry_data.get("coordinator")
        if coordinator:
            await coordinator.async_shutdown()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options updates.

    Args:
        hass: The Home Assistant instance
        entry: The config entry being updated
    """
    _LOGGER.info("Updating options for entry: %s", entry.entry_id)

    # Retrieve the coordinator
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    # Extract the new polling interval from options
    new_interval = entry.options.get(
        CONF_POLLING_INTERVAL, CONF_DEFAULT_POLLING_INTERVAL
    )

    # Update the coordinator with the new polling interval
    try:
        await coordinator.update_polling_interval(new_interval)
        _LOGGER.info(
            "Polling interval successfully updated to %s seconds", new_interval
        )
    except ValueError as ex:
        _LOGGER.error("Failed to update polling interval: %s", ex)

    # Trigger a refresh of data after options update
    await coordinator.async_request_refresh()
