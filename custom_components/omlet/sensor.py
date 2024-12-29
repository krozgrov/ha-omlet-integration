from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import OmletDataCoordinator
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors for the Omlet Smart Coop."""
    coordinator: OmletDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = []
    _LOGGER.debug("Coordinator data: %s", coordinator.data)

    for device in coordinator.data:
        device_id = device.get("deviceId")
        device_name = device.get("name", "Unknown Device")
        manufacturer = "Omlet"
        model = device.get("deviceType", "Unknown Model")

        sensors.append(OmletSensor(coordinator, device_id, device, "batteryLevel", f"{device_name} Battery Level", "%", manufacturer, model))
        sensors.append(OmletSensor(coordinator, device_id, device, "wifiStrength", f"{device_name} WiFi Signal Strength", "dBm", manufacturer, model))
        sensors.append(OmletSensor(coordinator, device_id, device, "firmwareVersionCurrent", f"{device_name} Firmware Version", None, manufacturer, model))

    async_add_entities(sensors)


class OmletSensor(SensorEntity):
    """Representation of an Omlet sensor."""

    def __init__(self, coordinator, device_id, device_data, key, name, unit, manufacturer, model):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._device_id = device_id
        self._device_data = device_data
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_data.get("name", "Unknown Device"),
            "manufacturer": manufacturer,
            "model": model,
        }

    @property
    def native_value(self):
        """Return the current value of the sensor."""
        try:
            # Debug log to verify the coordinator data structure
            _LOGGER.debug("Sensor [%s]: Coordinator data: %s", self._key, self.coordinator.data)

            # Locate device in data
            device_data = next(
                (d for d in self.coordinator.data if d.get("deviceId") == self._device_id), None
            )

            if device_data:
                # Handle general and connectivity state separately
                if self._key == "wifiStrength":
                    return device_data.get("state", {}).get("connectivity", {}).get("wifiStrength")
                return device_data.get("state", {}).get("general", {}).get(self._key)

            _LOGGER.error("Device %s not found in coordinator data", self._device_id)
            return None
        except Exception as e:
            _LOGGER.error("Error retrieving data for sensor %s: %s", self._key, e)
            return None

    async def async_update(self):
        """Request an update from the coordinator."""
        await self.coordinator.async_request_refresh()