from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, API_BASE_URL, CONF_API_KEY
import aiohttp


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up sensors for the Omlet Smart Coop."""
    api_key = entry.data.get(CONF_API_KEY)  # Retrieve API key from entry data
    if not api_key:
        raise ValueError("API key not found in config entry")

    # Fetch devices from the API
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {api_key}"}
        async with session.get(
            f"{API_BASE_URL}/device", headers=headers, timeout=10
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to fetch devices: {response.status}")
            devices = await response.json()

    sensors = [OmletBatterySensor(device, api_key) for device in devices]
    async_add_entities(sensors)


class OmletBatterySensor(SensorEntity):
    """A battery level sensor for the Omlet Smart Coop."""

    def __init__(self, device, api_key):
        self._device = device
        self._api_key = api_key
        self._attr_name = f"{device['name']} Battery"
        self._attr_unique_id = f"{device['deviceId']}_battery"
        self._attr_state = device["state"]["general"]["batteryLevel"]

    async def async_update(self):
        """Fetch new data for the sensor."""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            async with session.get(
                f"{API_BASE_URL}/device/{self._device['deviceId']}",
                headers=headers,
                timeout=10,
            ) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"Failed to fetch device state: {response.status}"
                    )
                device_data = await response.json()
                self._attr_state = device_data["state"]["general"]["batteryLevel"]
