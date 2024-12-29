from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switches from the config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    switches = []
    for device_id, device_data in coordinator.devices.items():
        # Door Switch
        if "door" in device_data:
            switches.append(
                OmletSwitch(
                    coordinator,
                    device_id,
                    "door",
                    f"{device_data['name']} Door",
                )
            )

        # Light Switch
        if "light" in device_data:
            switches.append(
                OmletSwitch(
                    coordinator,
                    device_id,
                    "light",
                    f"{device_data['name']} Light",
                )
            )

    async_add_entities(switches)


class OmletSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a switch for Omlet devices."""

    def __init__(self, coordinator, device_id, key, name):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def is_on(self):
        """Return whether the switch is on."""
        device_data = self.coordinator.devices.get(self._device_id, {})
        if self._key == "door":
            return device_data["door"]["state"] == "open"
        if self._key == "light":
            return device_data["light"]["state"] == "on"
        return False

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._execute_action("on" if self._key == "light" else "open")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._execute_action("off" if self._key == "light" else "close")

    async def _execute_action(self, action):
        """Execute an action on the device."""
        device_data = self.coordinator.devices.get(self._device_id, {})
        action_url = next(
            (
                action["url"]
                for action in device_data.get("actions", [])
                if action["actionValue"] == action
            ),
            None,
        )
        if action_url:
            await self.coordinator.api_client.execute_action(action_url)
            await self.coordinator.async_request_refresh()
