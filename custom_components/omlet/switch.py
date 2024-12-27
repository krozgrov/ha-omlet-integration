import aiohttp
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, BASE_URL, CONF_API_KEY


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Omlet Smart Coop switches."""
    api_key = hass.data[DOMAIN][entry.entry_id][CONF_API_KEY]
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/device", headers=headers, timeout=10
            ) as response:
                if response.status == 200:
                    devices = await response.json()
                else:
                    hass.logger.error(f"Failed to fetch devices: {response.status}")
                    return
    except Exception as e:
        hass.logger.error(f"Error fetching devices for switches: {e}")
        return

    entities = []
    for device in devices:
        if "light" in device.get("state", {}):  # Check for light-related devices
            entities.append(OmletLightSwitch(device, headers))
    async_add_entities(entities)


class OmletLightSwitch(SwitchEntity):
    """Representation of a light switch."""

    def __init__(self, device, headers):
        self._device = device
        self._headers = headers
        self._attr_name = f"{device['name']} Light"
        self._attr_unique_id = f"{device['deviceId']}_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device["deviceId"])},
            "name": device["name"],
            "manufacturer": "Omlet",
            "model": device["deviceType"],
        }

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._device["state"]["light"]["state"] == "on"

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self._perform_action("on")

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._perform_action("off")

    async def _perform_action(self, action_name):
        """Perform the specified action on the device."""
        action_url = f"{BASE_URL}/device/{self._device['deviceId']}/action/{action_name}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    action_url, headers=self._headers, timeout=10
                ) as response:
                    if response.status not in (200, 204):
                        self.hass.logger.error(
                            f"Failed to perform {action_name} action: {response.status}"
                        )
        except Exception as e:
            self.hass.logger.error(f"Error performing {action_name} action: {e}")