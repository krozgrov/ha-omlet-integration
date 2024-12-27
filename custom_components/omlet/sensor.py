import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE
from .const import DOMAIN, API_BASE_URL, CONF_API_KEY


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for the Omlet Smart Coop integration."""
    api_key = hass.data[DOMAIN][entry.entry_id][CONF_API_KEY]
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/device", headers=headers, timeout=10
            ) as response:
                if response.status == 200:
                    devices = await response.json()
                else:
                    raise ValueError(f"Failed to fetch devices: {response.status}")
    except Exception as e:
        hass.logger.error(f"Error fetching devices for sensors: {e}")
        return

    # Create battery sensors for all devices
    sensors = [
        OmletBatterySensor(device) for device in devices if "general" in device["state"]
    ]
    async_add_entities(sensors)


class OmletBatterySensor(SensorEntity):
    """A sensor for monitoring battery levels of the Omlet Smart Coop."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device['name']} Battery"
        self._attr_unique_id = f"{device['deviceId']}_battery"
        self._attr_unit_of_measurement = PERCENTAGE
        self._attr_state = device["state"]["general"]["batteryLevel"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device["deviceId"])},
            "name": device["name"],
            "manufacturer": "Omlet",
            "model": device["deviceType"],
        }

    async def async_update(self):
        """Fetch the latest data for the sensor."""
        api_key = self.hass.data[DOMAIN][CONF_API_KEY]
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE_URL}/device/{self._device['deviceId']}",
                    headers=headers,
                    timeout=10,
                ) as response:
                    if response.status == 200:
                        device_data = await response.json()
                        self._attr_state = device_data["state"]["general"][
                            "batteryLevel"
                        ]
                    else:
                        self.hass.logger.error(
                            f"Failed to update battery sensor: {response.status}"
                        )
        except Exception as e:
            self.hass.logger.error(f"Error updating battery sensor: {e}")
