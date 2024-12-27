from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Omlet switches from a config entry."""
    omlet = hass.data[DOMAIN][entry.entry_id]  # Directly retrieve the Omlet object
    devices = await hass.async_add_executor_job(omlet.get_devices)  # Fetch devices

    entities = []

    for device in devices:
        if device.state.light:  # Check if the light state exists
            entities.append(OmletLightSwitch(device))

    async_add_entities(entities)


class OmletLightSwitch(SwitchEntity):
    """Representation of a light switch."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device.name} Light"
        self._attr_unique_id = f"{device.deviceId}_light"
        self._state = None

    @property
    def is_on(self):
        """Return the current state of the light."""
        return self._device.state.light.state == "on"

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        action = next((a for a in self._device.actions if a.name == "on"), None)
        if action:
            await self._device.omlet.perform_action(action)

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        action = next((a for a in self._device.actions if a.name == "off"), None)
        if action:
            await self._device.omlet.perform_action(action)
