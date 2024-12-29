from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
from .entity import OmletEntity
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    # Set up the switches from the config entry.
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up switches for devices: %s", coordinator.data)

    switches = []
    for device_id, device_data in coordinator.data.items():
        # Door Switch
        if "state" in device_data and "door" in device_data["state"]:
            switches.append(
                OmletSwitch(
                    coordinator,
                    device_id,
                    "door",
                    device_data["name"],
                )
            )

        # Light Switch
        if "state" in device_data and "light" in device_data["state"]:
            switches.append(
                OmletSwitch(
                    coordinator,
                    device_id,
                    "light",
                    device_data["name"],
                )
            )

    async_add_entities(switches)


class OmletSwitch(OmletEntity, SwitchEntity):
    # Representation of a switch for Omlet devices.

    def __init__(self, coordinator, device_id, key, device_name):
        # Initialize the switch.
        super().__init__(coordinator, device_id)
        self._key = key
        self._attr_name = key.title()
        sanitized_name = device_name.lower().replace(" ", "_")
        self.entity_id = f"switch.{sanitized_name}_{key}"
        self._attr_unique_id = f"{device_id}_{sanitized_name}_{key}"

    @property
    def available(self):
        # Return if entity is available.
        device_data = self.coordinator.data.get(self.device_id, {})
        if self._key == "door":
            state = device_data["state"]["door"]["state"]
            # Only unavailable during "stopping"
            return state != "stopping"
        if self._key == "light":
            state = device_data["state"]["light"]["state"]
            # Always available, even during pending states
            return True
        return True

    @property
    def is_on(self):
        # Return whether the switch is on.
        device_data = self.coordinator.data.get(self.device_id, {})
        if self._key == "door":
            state = device_data["state"]["door"]["state"]
            return state in ["open", "openpending"]
        if self._key == "light":
            state = device_data["state"]["light"]["state"]
            return state in ["on", "onpending"]
        return False

    async def async_turn_on(self, **kwargs):
        # Turn the switch on.
        action_value = "on" if self._key == "light" else "open"
        await self._execute_action(action_value)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        # Turn the switch off.
        action_value = "off" if self._key == "light" else "close"
        await self._execute_action(action_value)
        await self.coordinator.async_request_refresh()

    async def _execute_action(self, action):
        # Execute an action on the device.
        device_data = self.coordinator.data.get(self.device_id, {})
        action_url = next(
            (a["url"] for a in device_data["actions"] if a["actionValue"] == action),
            None,
        )
        if action_url:
            await self.coordinator.api_client.execute_action(action_url)
