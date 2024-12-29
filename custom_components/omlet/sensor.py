from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from .const import DOMAIN
from .coordinator import OmletDataCoordinator
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up sensors for the Omlet Smart Coop."""
    coordinator: OmletDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = []
    for device in coordinator.data:
        device_id = device.get("deviceId")
        device_name = device.get("name", "Unknown Device")
        manufacturer = "Omlet"
        model = device.get("deviceType", "Unknown Model")

        # Register the device in Home Assistant
        device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer=manufacturer,
            model=model,
            entry_type=DeviceEntryType.SERVICE,
        )

        # Add battery level sensor
        sensors.append(
            OmletBatterySensor(
                coordinator,
                device_id,
                "batteryLevel",
                device_info,
            )
        )

        # Add WiFi signal strength sensor
        sensors.append(
            OmletWiFiSensor(
                coordinator,
                device_id,
                "wifiStrength",
                device_info,
            )
        )

        # Add firmware version sensor
        sensors.append(
            OmletFirmwareSensor(
                coordinator,
                device_id,
                "firmwareVersionCurrent",
                device_info,
            )
        )

    async_add_entities(sensors)


class OmletBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of the battery level sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id, key, device_info):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key
        self._attr_name = "Battery Level"
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the current battery level."""
        device_data = next(
            (d for d in self.coordinator.data if d.get("deviceId") == self._device_id),
            {},
        )
        return device_data.get("state", {}).get("general", {}).get(self._key)


class OmletWiFiSensor(CoordinatorEntity, SensorEntity):
    """Representation of the WiFi signal strength sensor."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_id, key, device_info):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key
        self._attr_name = "WiFi Signal Strength"
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the current WiFi signal strength."""
        device_data = next(
            (d for d in self.coordinator.data if d.get("deviceId") == self._device_id),
            {},
        )
        return device_data.get("state", {}).get("connectivity", {}).get(self._key)


class OmletFirmwareSensor(CoordinatorEntity, SensorEntity):
    """Representation of the firmware version sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_id, key, device_info):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key
        self._attr_name = "Firmware Version"
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        """Return the current firmware version."""
        device_data = next(
            (d for d in self.coordinator.data if d.get("deviceId") == self._device_id),
            {},
        )
        return device_data.get("state", {}).get("general", {}).get(self._key)
