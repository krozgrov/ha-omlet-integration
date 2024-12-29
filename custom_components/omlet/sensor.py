from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors from the config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = []
    for device_id, device_data in coordinator.devices.items():
        # Battery Sensor
        if "battery" in device_data and device_data["battery"]["level"] is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    "battery_level",
                    f"{device_data['name']} Battery Level",
                    PERCENTAGE,
                    "battery",
                )
            )

        # Wi-Fi Signal Strength Sensor
        if (
            "connectivity" in device_data
            and device_data["connectivity"]["wifi_strength"] is not None
        ):
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    "wifi_strength",
                    f"{device_data['name']} Wi-Fi Strength",
                    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                    "wifi",
                )
            )

        # Firmware Version Sensor
        if "firmware" in device_data and device_data["firmware"]["current"] is not None:
            sensors.append(
                OmletSensor(
                    coordinator,
                    device_id,
                    "firmware_version",
                    f"{device_data['name']} Firmware Version",
                    None,
                    "firmware",
                )
            )

    async_add_entities(sensors)


class OmletSensor(CoordinatorEntity, SensorEntity):
    """Representation of a sensor for Omlet devices."""

    def __init__(self, coordinator, device_id, key, name, unit, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._key = key
        self._attr_name = name
        self._attr_unit_of_measurement = unit
        self._attr_icon = f"mdi:{icon}" if icon else None
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def native_value(self):
        """Return the current value of the sensor."""
        device_data = self.coordinator.devices.get(self._device_id, {})
        if self._key == "battery_level":
            return device_data["battery"]["level"]
        if self._key == "wifi_strength":
            return device_data["connectivity"]["wifi_strength"]
        if self._key == "firmware_version":
            return device_data["firmware"]["current"]
        return None
