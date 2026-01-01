"""Test init of Omlet Smart Coop integration."""

from unittest.mock import AsyncMock, patch

import pytest

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration


async def test_async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    mock_fetch_devices,
) -> None:
    """Test a successful setup entry."""
    await init_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED


async def test_config_not_ready(hass: HomeAssistant, config_entry) -> None:
    """Test setup retry when the API is unavailable."""
    with patch(
        "custom_components.omlet_smart_coop.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(side_effect=ClientError("boom")),
    ):
        await init_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    config_entry,
    mock_fetch_devices,
) -> None:
    """Test successful unload of entry."""
    await init_integration(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert not hass.data.get("omlet_smart_coop")
