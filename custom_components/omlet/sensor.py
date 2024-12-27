from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Omlet sensors from a config entry."""
    omlet = hass.data[DOMAIN][entry.entry_id]  # Directly retrieve the Omlet object
    devices = await hass.async_add_executor_job(omlet.get_devices)  # Fetch devices

    entities = []

    for device in devices:
        entities.append(OmletBatterySensor(device))
        entities.append(OmletWiFiSensor(device))  # Ensure this class exists
        entities.append(OmletDoorStateSensor(device))

    async_add_entities(entities)


class OmletBatterySensor(SensorEntity):
    """Representation of the battery level sensor."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device.name} Battery"
        self._attr_unique_id = f"{device.deviceId}_battery"
        self._attr_device_class = "battery"
        self._attr_native_unit_of_measurement = "%"
        self._state = None

    @property
    def state(self):
        """Return the current battery level."""
        return self._device.state.general.batteryLevel

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await self._device.refresh()


class OmletWiFiSensor(SensorEntity):
    """Representation of the Wi-Fi strength sensor."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device.name} Wi-Fi Strength"
        self._attr_unique_id = f"{device.deviceId}_wifi_strength"
        self._attr_device_class = "signal_strength"
        self._attr_native_unit_of_measurement = "dBm"
        self._state = None

    @property
    def state(self):
        """Return the current Wi-Fi strength."""
        return self._device.state.connectivity.wifiStrength

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await self._device.refresh()
