from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Omlet switches from a config entry."""
    omlet = hass.data[DOMAIN][entry.entry_id]

    # Example: Fetch devices and create switch entities
    devices = await hass.async_add_executor_job(omlet.get_devices)
    entities = []

    for device in devices:
        if "light" in device["state"]:  # Example: If the device has a light
            entities.append(OmletLightSwitch(device, omlet))

    async_add_entities(entities)


class OmletLightSwitch(SwitchEntity):
    """Representation of an Omlet light switch."""

    def __init__(self, device, omlet):
        """Initialize the light switch."""
        self._device = device
        self._omlet = omlet
        self._attr_name = f"{device['name']} Light"
        self._attr_unique_id = f"{device['deviceId']}_light"

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._device["state"]["light"]["state"] == "on"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._omlet.turn_on_light(self._device["deviceId"])
        self._device["state"]["light"]["state"] = "on"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._omlet.turn_off_light(self._device["deviceId"])
        self._device["state"]["light"]["state"] = "off"
        self.async_write_ha_state()