from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN,
    API_BASE_URL,
    CONF_API_KEY,
    DOOR_ACTION_OPEN,
    DOOR_ACTION_CLOSE,
    STATE_DOOR_OPEN,
    STATE_DOOR_CLOSED,
)
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Omlet Smart Coop switches."""
    api_key = entry.data.get(CONF_API_KEY)
    if not api_key:
        _LOGGER.error("API key not found in config entry")
        return

    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with session.get(
                f"{API_BASE_URL}/device", headers=headers, timeout=10
            ) as response:
                if response.status != 200:
                    _LOGGER.error(f"Failed to fetch devices: {response.status}")
                    return
                devices = await response.json()
    except Exception as e:
        _LOGGER.error(f"Error fetching devices: {e}")
        return

    entities = []
    for device in devices:
        ## OmletLight
        # Add light switch if light state is available
        if "light" in device["state"]:
            entities.append(OmletLightSwitch(device, api_key))
        ## OmletDoor
        # Add door switch if door state is available
        if "door" in device["state"]:
            entities.append(OmletDoorSwitch(device, api_key))

    async_add_entities(entities)


## OmletLight
class OmletLightSwitch(SwitchEntity):
    """Representation of a light switch for Omlet Smart Coop."""

    def __init__(self, device, api_key):
        self._device = device
        self._api_key = api_key
        self._attr_name = f"{device['name']} Light"
        self._attr_unique_id = f"{device['deviceId']}_light"
        self._attr_is_on = device["state"]["light"]["state"] == "on"

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._attr_is_on

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self._send_action("on")

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._send_action("off")

    async def _send_action(self, action):
        """Send an action to the API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self._api_key}"}
                async with session.post(
                    f"{API_BASE_URL}/device/{self._device['deviceId']}/action/{action}",
                    headers=headers,
                    timeout=10,
                ) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            f"Failed to send light action {action}: {response.status}"
                        )
                    else:
                        self._attr_is_on = action == "on"
        except Exception as e:
            _LOGGER.error(f"Error sending light action {action}: {e}")


## OmletDoor
class OmletDoorSwitch(SwitchEntity):
    """Representation of a door switch for Omlet Smart Coop."""

    def __init__(self, device, api_key):
        self._device = device
        self._api_key = api_key
        self._attr_name = f"{device['name']} Door"
        self._attr_unique_id = f"{device['deviceId']}_door"
        self._attr_is_on = device["state"]["door"]["state"] == STATE_DOOR_OPEN

    @property
    def is_on(self):
        """Return true if the door is open."""
        return self._attr_is_on

    async def async_turn_on(self, **kwargs):
        """Open the door."""
        await self._send_action(DOOR_ACTION_OPEN)

    async def async_turn_off(self, **kwargs):
        """Close the door."""
        await self._send_action(DOOR_ACTION_CLOSE)

    async def _send_action(self, action):
        """Send an action to the API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self._api_key}"}
                async with session.post(
                    f"{API_BASE_URL}/device/{self._device['deviceId']}/action/{action}",
                    headers=headers,
                    timeout=10,
                ) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            f"Failed to send door action {action}: {response.status}"
                        )
                    else:
                        self._attr_is_on = action == DOOR_ACTION_OPEN
        except Exception as e:
            _LOGGER.error(f"Error sending door action {action}: {e}")