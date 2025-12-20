import logging
from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from .entity import OmletEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    # Set up the lights from the config entry.
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up lights for devices: %s", coordinator.data)

    lights = []
    for device_id, device_data in coordinator.data.items():
        # Light Entity
        light_state = device_data.get("state", {}).get("light")
        if light_state:
            lights.append(
                OmletLight(
                    coordinator,
                    device_id,
                    device_data["name"],
                )
            )

    async_add_entities(lights)


class OmletLight(OmletEntity, LightEntity):
    # Representation of a light for Omlet devices.

    def __init__(self, coordinator, device_id, device_name):
        # Initialize the light entity.
        super().__init__(coordinator, device_id)
        self._attr_translation_key = "light"
        # Keep existing unique_id scheme for backward compatibility
        # Stable unique_id not tied to names
        self._attr_unique_id = f"{device_id}_light"
        self._attr_has_entity_name = True
        self._attr_supported_color_modes = {
            ColorMode.ONOFF
        }  # Assuming only ON/OFF is supported
        self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self):
        # Return whether the light is on.
        device_data = self.coordinator.data.get(self.device_id, {})
        state = device_data.get("state", {}).get("light", {}).get("state")
        return state in ["on", "onpending"]

    async def async_turn_on(self, **kwargs):
        # Turn the light on.
        await self._execute_action("on")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        # Turn the light off.
        await self._execute_action("off")
        await self.coordinator.async_request_refresh()

    async def _execute_action(self, action):
        # Execute an action on the device.
        device_data = self.coordinator.data.get(self.device_id, {})
        action_url = next(
            (a["url"] for a in device_data.get("actions", []) if a["actionValue"] == action),
            None,
        )
        if action_url:
            await self.coordinator.api_client.execute_action(action_url)
