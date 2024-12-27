from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, API_BASE_URL, CONF_API_KEY
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up sensors for the Omlet Smart Coop."""
    api_key = entry.data.get(CONF_API_KEY)  # Retrieve API key from entry data
    if not api_key:
        _LOGGER.error("API key not found in config entry")
        return

    # Fetch devices from the API
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
        _LOGGER.error(f"Error fetching devices from API: {e}")
        return

    # Create sensors for each device
    sensors = []
    for device in devices:
        # Debug the device state for clarity
        _LOGGER.debug(f"Device data: {device}")

        # Check for a valid battery level in the response
        battery_level = device.get("state", {}).get("general", {}).get("batteryLevel")
        if battery_level is not None:
            sensors.append(
                OmletBatterySensor(
                    device=device, api_key=api_key, config_entry_id=entry.entry_id
                )
            )
        else:
            _LOGGER.warning(
                f"Device {device['name']} does not have a valid battery level."
            )
    async_add_entities(sensors)


class OmletBatterySensor(SensorEntity):
    """A battery level sensor for the Omlet Smart Coop."""

    def __init__(self, device, api_key, config_entry_id):
        self._device = device
        self._api_key = api_key
        self._config_entry_id = config_entry_id

        # Entity-specific attributes
        self._attr_name = f"{device['name']} Battery"
        self._attr_unique_id = f"{device['deviceId']}_battery"
        self._attr_native_unit_of_measurement = "%"
        self._attr_device_class = "battery"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Device linking
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device["deviceId"])},
            "name": device["name"],
            "manufacturer": "Omlet",
            "model": device["deviceType"],
            "entry_type": DeviceEntryType.SERVICE,
        }

        # Set initial state
        self._attr_state = device["state"]["general"].get("batteryLevel", "unknown")
        _LOGGER.debug(f"Initialized {self._attr_name} with state: {self._attr_state}")

    @property
    def native_value(self):
        """Return the current battery level."""
        return self._attr_state

    async def async_update(self):
        """Fetch updated data for the sensor."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self._api_key}"}
                async with session.get(
                    f"{API_BASE_URL}/device/{self._device['deviceId']}",
                    headers=headers,
                    timeout=10,
                ) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            f"Failed to fetch device state: {response.status}"
                        )
                        return

                    # Parse the device data
                    device_data = await response.json()
                    _LOGGER.debug(f"Fetched device data: {device_data}")

                    # Update battery level state
                    self._attr_state = (
                        device_data.get("state", {})
                        .get("general", {})
                        .get("batteryLevel", "unknown")
                    )
                    _LOGGER.debug(
                        f"Updated {self._attr_name} battery level to: {self._attr_state}"
                    )
        except Exception as e:
            _LOGGER.error(f"Error updating sensor {self._attr_name}: {e}")
