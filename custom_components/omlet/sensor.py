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
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:battery",
    ),
    # Door Sensors
    "door_state": SensorEntityDescription(
        key="door_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:door",
    ),
    "door_fault": SensorEntityDescription(
        key="door_fault",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle",
    ),
    "door_light_level": SensorEntityDescription(
        key="door_light_level",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:brightness-6",
    ),
    # Light Sensors
    "light_state": SensorEntityDescription(
        key="light_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:lightbulb",
    ),
    "light_mode": SensorEntityDescription(
        key="light_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
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


def parse_timestamp(timestamp_str: str) -> datetime:
    # Parse timestamp string to datetime with timezone.
    try:
        # If timestamp already has timezone info, parse it directly
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        # If no timezone, assume UTC
        return datetime.fromisoformat(timestamp_str).replace(tzinfo=ZoneInfo("UTC"))


async def async_setup_entry(hass, config_entry, async_add_entities):
    # Set up the sensors from the config entry.
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up sensors for devices: %s", coordinator.data)

    sensors = []
    for device_id, device_data in coordinator.data.items():
        # State Sensors
        state = device_data.get("state", {})
        general_state = state.get("general", {})
        door_state = state.get("door", {})
        light_state = state.get("light", {})

        # Configuration
        config = device_data.get("configuration", {})
        door_config = config.get("door", {})
        general_config = config.get("general", {})
        light_config = config.get("light", {})

        # General Device Sensors
        if general_state.get("batteryLevel") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["battery_level"],
                    device_data["name"],
                )
            )

        # Door Sensors
        if door_state.get("state"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["door_state"],
                    device_data["name"],
                )
            )

        if door_state.get("fault"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["door_fault"],
                    device_data["name"],
                )
            )

        if door_state.get("lightLevel") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["door_light_level"],
                    device_data["name"],
                )
            )

        # Light Sensors
        if light_state.get("state"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["light_state"],
                    device_data["name"],
                )
            )

        if light_config.get("mode"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["light_mode"],
                    device_data["name"],
                )
            )

        if light_config.get("minutesBeforeClose") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["light_minutes_before_close"],
                    device_data["name"],
                )
            )

        if light_config.get("maxOnTime") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["light_max_on_time"],
                    device_data["name"],
                )
            )

        if light_config.get("equipped") is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["light_equipped"],
                    device_data["name"],
                )
            )

        # Timestamp Sensors
        if door_state.get("lastOpenTime"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["last_open_time"],
                    device_data["name"],
                )
            )

        if door_state.get("lastCloseTime"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["last_close_time"],
                    device_data["name"],
                )
            )

        # Configuration Sensors
        if door_config.get("openTime"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["door_open_time"],
                    device_data["name"],
                )
            )

        if door_config.get("closeTime"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["door_close_time"],
                    device_data["name"],
                )
            )

        if general_config.get("overnightSleepStart"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["overnight_sleep_start"],
                    device_data["name"],
                )
            )

        if general_config.get("overnightSleepEnd"):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    SENSOR_TYPES["overnight_sleep_end"],
                    device_data["name"],
                )
            )

    custom_order = [
        "battery_level",
        "door_state",
        "door_fault",
        "door_light_level",
        "door_open_time",
        "door_close_time",
        "last_open_time",
        "last_close_time",
        "light_state",
        "light_mode",
        "light_minutes_before_close",
        "light_max_on_time",
        "light_equipped",
        "overnight_sleep_start",
        "overnight_sleep_end",
    ]

    # Sort the sensors list based on the custom order
    sensors.sort(key=lambda sensor: custom_order.index(sensor.entity_description.key))

    async_add_entities(sensors)


class OmletSensor(OmletEntity, SensorEntity):
    # Representation of a sensor for Omlet devices.

    def __init__(
        self,
        coordinator,
        device_id,
        description: SensorEntityDescription,
        device_name: str,
    ):
        # Initialize the sensor.
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
    def native_value(self) -> StateType:
        # Return the current value of the sensor.
        device_data = self.coordinator.data.get(self.device_id, {})
        state = device_data.get("state", {})
        config = device_data.get("configuration", {})

        # General Device Sensors
        if self.entity_description.key == "battery_level":
            return state.get("general", {}).get("batteryLevel")

        # Door Sensors
        if self.entity_description.key == "door_state":
            return state.get("door", {}).get("state")

        if self.entity_description.key == "door_fault":
            return state.get("door", {}).get("fault")

        if self.entity_description.key == "door_light_level":
            return state.get("door", {}).get("lightLevel")

        if self.entity_description.key == "door_open_time":
            return config.get("door", {}).get("openTime")

        if self.entity_description.key == "door_close_time":
            return config.get("door", {}).get("closeTime")

        # Light Sensors
        if self.entity_description.key == "light_state":
            return state.get("light", {}).get("state")

        if self.entity_description.key == "light_mode":
            return config.get("light", {}).get("mode")

        if self.entity_description.key == "light_minutes_before_close":
            return config.get("light", {}).get("minutesBeforeClose")

        if self.entity_description.key == "light_max_on_time":
            return config.get("light", {}).get("maxOnTime")

        if self.entity_description.key == "light_equipped":
            return config.get("light", {}).get("equipped")

        # Timestamp Sensors
        if self.entity_description.key == "last_open_time":
            timestamp_str = state.get("door", {}).get("lastOpenTime")
            return parse_timestamp(timestamp_str) if timestamp_str else None

        if self.entity_description.key == "last_close_time":
            timestamp_str = state.get("door", {}).get("lastCloseTime")
            return parse_timestamp(timestamp_str) if timestamp_str else None

        # Configuration Sensors
        if self.entity_description.key == "overnight_sleep_start":
            return config.get("general", {}).get("overnightSleepStart")

        if self.entity_description.key == "overnight_sleep_end":
            return config.get("general", {}).get("overnightSleepEnd")

        return None
