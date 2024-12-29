from homeassistant.components.cover import CoverEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import OmletDataCoordinator
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up switches and covers for the Omlet Smart Coop."""
    coordinator: OmletDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    _LOGGER.debug("Coordinator data for switches: %s", coordinator.data)

    for device in coordinator.data:
        device_id = device.get("deviceId")
        device_name = device.get("name", "Unknown Device")

        # Add light switch
        if "light" in device.get("state", {}):
            entities.append(
                OmletLightSwitch(coordinator, device_id, device_name, device)
            )

        # Add door cover
        if "door" in device.get("state", {}):
            entities.append(OmletDoorCover(coordinator, device_id, device_name, device))

    async_add_entities(entities)


class OmletLightSwitch(SwitchEntity):
    """Representation of the Omlet light switch."""

    def __init__(self, coordinator, device_id, device_name, device):
        self.coordinator = coordinator
        self._device_id = device_id
        self._device_name = device_name
        self._device = device
        self._attr_name = f"{device_name} Light"
        self._attr_unique_id = f"{device_id}_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
        }

    @property
    def is_on(self):
        """Return the state of the light."""
        return self._device["state"]["light"]["state"] == "on"

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self.coordinator.perform_action(self._device_id, "on")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self.coordinator.perform_action(self._device_id, "off")
        self.async_write_ha_state()

    async def async_update(self):
        """Request an update from the coordinator."""
        await self.coordinator.async_request_refresh()


class OmletDoorCover(CoverEntity):
    """Representation of the automatic chicken door."""

    def __init__(self, coordinator, device_id, device_name, device):
        """Initialize the door cover."""
        self.coordinator = coordinator
        self._device_id = device_id
        self._device_name = device_name
        self._device = device
        self._attr_name = f"{device_name} Door"
        self._attr_unique_id = f"{device_id}_door"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_name,
        }

    @property
    def is_closed(self) -> bool:
        """Return if the door is closed."""
        return self._device["state"]["door"]["state"] == "closed"

    async def async_open_cover(self, **kwargs):
        """Open the door."""
        await self.coordinator.perform_action(self._device_id, "open")
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close the door."""
        await self.coordinator.perform_action(self._device_id, "close")
        self.async_write_ha_state()

    async def async_update(self):
        """Request an update from the coordinator."""
        await self.coordinator.async_request_refresh()
