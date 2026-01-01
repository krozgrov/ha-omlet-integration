from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.omlet_smart_coop.coordinator import OmletDataCoordinator


@pytest.mark.asyncio
async def test_coordinator_refresh_success(hass, omlet_devices, config_entry):
    with patch(
        "custom_components.omlet_smart_coop.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(return_value=omlet_devices),
    ):
        coordinator = OmletDataCoordinator(hass, "test-api-key", config_entry)
        await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert "door-1" in coordinator.data
    assert coordinator.data["door-1"]["deviceId"] == "door-1"


@pytest.mark.asyncio
async def test_coordinator_refresh_invalid_payload(hass, config_entry):
    with patch(
        "custom_components.omlet_smart_coop.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(return_value={}),
    ):
        coordinator = OmletDataCoordinator(hass, "test-api-key", config_entry)
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
