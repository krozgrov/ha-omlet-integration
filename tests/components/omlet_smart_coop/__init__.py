"""Tests for Omlet Smart Coop integration."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def init_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the Omlet Smart Coop integration in Home Assistant."""
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
