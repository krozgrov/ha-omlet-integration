import pytest

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.omlet_smart_coop.const import DOMAIN

from . import init_integration


@pytest.mark.asyncio
async def test_entity_setup_registers_device_and_entities(hass, config_entry, mock_fetch_devices):
    await init_integration(hass, config_entry)

    ent_reg = er.async_get(hass)
    cover_entity_id = ent_reg.async_get_entity_id("cover", DOMAIN, "door-1_door")
    light_entity_id = ent_reg.async_get_entity_id("light", DOMAIN, "door-1_light")

    assert cover_entity_id is not None
    assert light_entity_id is not None

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, "SERIAL_DOOR_1")})
    assert device is not None
    assert device.manufacturer == "Omlet"
