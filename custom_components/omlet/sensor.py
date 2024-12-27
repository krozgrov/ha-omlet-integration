from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, ATTR_BATTERY_LEVEL, ATTR_SIGNAL_STRENGTH, STATE_DOOR_OPEN, STATE_DOOR_CLOSED


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Omlet sensors from a config entry."""
    client = hass.data[DOMAIN][entry.entry_id]  # Get the API client
    devices = await hass.async_add_executor_job(client.get_devices)  # Fetch devices

    entities = []

    for device in devices:
        # Add sensors for each device
        entities.append(OmletBatterySensor(device))
        entities.append(OmletWiFiSensor(device))
        entities.append(OmletDoorStateSensor(device))

    async_add_entities(entities)


class OmletBatterySensor(SensorEntity):
    """Representation of the battery level sensor."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device['name']} Battery"
        self._attr_unique_id = f"{device['deviceId']}_battery"
        self._attr_device_class = "battery"
        self._attr_native_unit_of_measurement = "%"
        self._state = None

    @property
    def state(self):
        """Return the current battery level."""
        return self._device['state']['general'][ATTR_BATTERY_LEVEL]

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await self._device.refresh()


class OmletWiFiSensor(SensorEntity):
    """Representation of the Wi-Fi signal strength sensor."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device['name']} Wi-Fi Signal"
        self._attr_unique_id = f"{device['deviceId']}_wifi"
        self._attr_native_unit_of_measurement = "dBm"
        self._state = None

    @property
    def state(self):
        """Return the Wi-Fi signal strength."""
        return self._device['state']['connectivity'][ATTR_SIGNAL_STRENGTH]

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await self._device.refresh()


class OmletDoorStateSensor(SensorEntity):
    """Representation of the door state sensor."""

    def __init__(self, device):
        self._device = device
        self._attr_name = f"{device['name']} Door State"
        self._attr_unique_id = f"{device['deviceId']}_door_state"
        self._state = None

    @property
    def state(self):
        """Return the door state."""
        door_state = self._device['state']['door']['state']
        return STATE_DOOR_OPEN if door_state == "open" else STATE_DOOR_CLOSED

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await self._device.refresh()