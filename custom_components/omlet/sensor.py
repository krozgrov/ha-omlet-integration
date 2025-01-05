"""Support for Omlet sensors."""

from datetime import datetime
from zoneinfo import ZoneInfo
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.typing import StateType
from .const import DOMAIN
from .entity import OmletEntity
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    # General Device Sensors
    "battery_level": SensorEntityDescription(
        key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery",
    ),
    # WiFi Sensors
    "wifi_ssid": SensorEntityDescription(
        key="wifi_ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi",
    ),
    "wifi_strength": SensorEntityDescription(
        key="wifi_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi-strength-3",
    ),
    # Door Sensors
    "door_state": SensorEntityDescription(
        key="door_state",
        icon="mdi:door",
    ),
    "door_fault": SensorEntityDescription(
        key="door_fault",
        icon="mdi:alert-circle",
    ),
    "door_light_level": SensorEntityDescription(
        key="door_light_level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:brightness-6",
    ),
    # Light Sensors
    "light_state": SensorEntityDescription(
        key="light_state",
        icon="mdi:lightbulb",
    ),
    "light_mode": SensorEntityDescription(
        key="light_mode",
        icon="mdi:lightbulb-cog",
    ),
    "light_minutes_before_close": SensorEntityDescription(
        key="light_minutes_before_close",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-outline",
    ),
    "light_max_on_time": SensorEntityDescription(
        key="light_max_on_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-off-outline",
    ),
    "light_equipped": SensorEntityDescription(
        key="light_equipped",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:lightbulb-outline",
    ),
    # Timestamp Sensors
    "last_open_time": SensorEntityDescription(
        key="last_open_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:door-open",
    ),
    "last_close_time": SensorEntityDescription(
        key="last_close_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:door-closed",
    ),
    # Configuration Sensors
    "door_open_time": SensorEntityDescription(
        key="door_open_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-start",
    ),
    "door_close_time": SensorEntityDescription(
        key="door_close_time",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:clock-end",
    ),
    "overnight_sleep_start": SensorEntityDescription(
        key="overnight_sleep_start",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-night",
    ),
    "overnight_sleep_end": SensorEntityDescription(
        key="overnight_sleep_end",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-sunny",
    ),
}


def parse_timestamp(timestamp_str: str) -> datetime | None:
    """Parse timestamp string to datetime with timezone."""
    if not timestamp_str:
        return None
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        return datetime.fromisoformat(timestamp_str).replace(tzinfo=ZoneInfo("UTC"))


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors from the config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up sensors for devices: %s", coordinator.data)

    sensors = []
    for device_id, device_data in coordinator.data.items():
        for key, description in SENSOR_TYPES.items():
            value = extract_sensor_value(key, device_data)
            if value is not None:
                sensors.append(
                    OmletSensor(
                        coordinator=coordinator,
                        device_id=device_id,
                        description=description,
                        device_name=device_data["name"],
                    )
                )

    async_add_entities(sensors)


def extract_sensor_value(sensor_key, device_data):
    """Extract the value for a given sensor key from device data."""
    state = device_data.get("state", {})
    config = device_data.get("configuration", {})

    # Log state and config only for debugging when needed
    #    if _LOGGER.isEnabledFor(logging.DEBUG):
    #        if sensor_key in [
    #            "door_close_time",
    #            "door_open_time",
    #            "last_close_time",
    #           "last_open_time",
    #           "overnight_sleep_start",
    #           "overnight_sleep_end",
    #       ]:
    #            _LOGGER.debug(
    #                "Processing %s: state=%s, config=%s", sensor_key, state, config
    #            )

    if sensor_key == "battery_level":
        return state.get("general", {}).get("batteryLevel")
    if sensor_key == "wifi_ssid":
        return state.get("connectivity", {}).get("ssid")
    if sensor_key == "wifi_strength":
        return state.get("connectivity", {}).get("wifiStrength")
    if sensor_key == "door_state":
        return state.get("door", {}).get("state")
    if sensor_key == "door_fault":
        return state.get("door", {}).get("fault")
    if sensor_key == "door_light_level":
        return state.get("door", {}).get("lightLevel")
    if sensor_key == "light_state":
        return state.get("light", {}).get("state")
    if sensor_key == "light_mode":
        return config.get("light", {}).get("mode")
    if sensor_key == "light_minutes_before_close":
        return config.get("light", {}).get("minutesBeforeClose")
    if sensor_key == "light_max_on_time":
        return config.get("light", {}).get("maxOnTime")
    if sensor_key == "light_equipped":
        return config.get("light", {}).get("equipped")

    # Handle timestamps
    if sensor_key == "last_open_time":
        timestamp_str = state.get("door", {}).get("lastOpenTime")
        return parse_timestamp(timestamp_str)
    if sensor_key == "last_close_time":
        timestamp_str = state.get("door", {}).get("lastCloseTime")
        return parse_timestamp(timestamp_str)

    # Handle door configuration times
    if sensor_key == "door_open_time":
        return config.get("door", {}).get("openTime")
    if sensor_key == "door_close_time":
        return config.get("door", {}).get("closeTime")

    # Handle overnight sleep times
    if sensor_key == "overnight_sleep_start":
        return config.get("general", {}).get("overnightSleepStart")
    if sensor_key == "overnight_sleep_end":
        return config.get("general", {}).get("overnightSleepEnd")

    return None


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
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_has_entity_name = True

    @property
    def native_value(self) -> StateType:
        """Return the current value of the sensor."""
        device_data = self.coordinator.data.get(self.device_id, {})
        return extract_sensor_value(self.entity_description.key, device_data)
