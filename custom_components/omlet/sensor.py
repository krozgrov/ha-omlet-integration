from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .entity import OmletEntity
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "battery_level": SensorEntityDescription(
        key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery",
    ),
    "wifi_strength": SensorEntityDescription(
        key="wifi_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi",
    ),
    "firmware_version": SensorEntityDescription(
        key="firmware_version",
        # Remove device_class for firmware version as it's not a standard class
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:new-box",
    ),
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors from the config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up sensors for devices: %s", coordinator.data)

    sensors = []
    for device_id, device_data in coordinator.data.items():
        # Battery Sensor
        if device_data["state"]["general"].get("batteryLevel") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["battery_level"],
                    device_data["name"],
                )
            )

        # Wi-Fi Signal Strength Sensor
        if device_data["state"]["connectivity"].get("wifiStrength") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["wifi_strength"],
                    device_data["name"],
                )
            )

        # Firmware Version Sensor
        if device_data["state"]["general"].get("firmwareVersionCurrent") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["firmware_version"],
                    device_data["name"],
                )
            )

    async_add_entities(sensors)


class OmletSensor(OmletEntity, SensorEntity):
    """Representation of a sensor for Omlet devices."""

    def __init__(
        self,
        coordinator,
        device_id,
        description: SensorEntityDescription,
        device_name: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_name = description.key.replace("_", " ").title()
        self._attr_unique_id = f"{device_id}_{description.key}"
        if hasattr(description, "device_class"):
            self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_has_entity_name = True

    @property
    def native_value(self):
        """Return the current value of the sensor."""
        device_data = self.coordinator.data.get(self.device_id, {})
        if self.entity_description.key == "battery_level":
            return device_data["state"]["general"]["batteryLevel"]
        if self.entity_description.key == "wifi_strength":
            return device_data["state"]["connectivity"]["wifiStrength"]
        if self.entity_description.key == "firmware_version":
            return device_data["state"]["general"]["firmwareVersionCurrent"]
        return None
