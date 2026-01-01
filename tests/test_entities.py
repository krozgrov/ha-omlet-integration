from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.omlet_smart_coop.const import CONF_API_KEY, DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_entity_setup_registers_device_and_entities(hass, omlet_devices):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        options={},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.omlet_smart_coop.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(return_value=omlet_devices),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    cover_entity_id = ent_reg.async_get_entity_id("cover", DOMAIN, "door-1_door")
    light_entity_id = ent_reg.async_get_entity_id("light", DOMAIN, "door-1_light")

    assert cover_entity_id is not None
    assert light_entity_id is not None

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, "SERIAL_DOOR_1")})
    assert device is not None
    assert device.manufacturer == "Omlet"
