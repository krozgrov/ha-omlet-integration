from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


class OmletEntity(CoordinatorEntity):
    """Base class for Omlet entities"""

    def __init__(self, coordinator, device_id):
        """Initialize the entity"""
        super().__init__(coordinator)
        self.device_id = device_id

    @property
    def _device_data(self) -> dict:
        """Always return the latest device data from the coordinator.

        Avoid caching device data at init-time; coordinator updates should be reflected
        immediately in device_info and attributes.
        """
        return self.coordinator.data.get(self.device_id, {}) or {}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information"""
        data = self._device_data
        state = data.get("state", {}).get("general", {})
        serial = data.get("deviceSerial")
        identifier_value = serial or data.get("deviceId") or self.device_id
        # Determine a friendly device name
        device_name = data.get("name")
        if not device_name or str(device_name).strip() == "":
            tail = str(identifier_value)[-6:] if identifier_value else "device"
            device_name = f"Omlet Coop {tail}"
        return DeviceInfo(
            identifiers={(DOMAIN, identifier_value)},
            name=device_name,
            manufacturer="Omlet",
            model=data.get("deviceType"),
            model_id=data.get("deviceTypeId"),
            sw_version=state.get("firmwareVersionCurrent"),
            hw_version=self.device_id,
            serial_number=serial,
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes specific to the device."""
        data = self._device_data
        connectivity = data.get("state", {}).get("connectivity", {})
        config = data.get("configuration", {})
        fan_state = self._device_data.get("state", {}).get("fan", {})
        fan_config = config.get("fan", {})
        attributes = {
            "device_id": data.get("deviceId"),
            "device_serial": data.get("deviceSerial"),
            "firmware_version_current": data.get("state", {})
            .get("general", {})
            .get("firmwareVersionCurrent"),
            "firmware_version_previous": data.get("state", {})
            .get("general", {})
            .get("firmwareVersionPrevious"),
            "firmware_last_check": data.get("state", {})
            .get("general", {})
            .get("firmwareLastCheck"),
            "device_type_id": data.get("deviceTypeId"),
            "door_type": config.get("door", {}).get("doorType"),
            "group_id": data.get("groupId"),
            "delete_pending": data.get("deletePending"),
            "battery_count": data.get("batteryCount"),
            "battery_warned": data.get("batteryWarned"),
            "ble_only": data.get("bleOnly"),
            "wifi_state": config.get("connectivity", {}).get("wifiState"),
            "wifi_ssid": connectivity.get("ssid"),
            "wifi_strength": connectivity.get("wifiStrength"),
            "wifi_connection_status": connectivity.get("connected"),
            "overdue_connection": data.get("overdueConnection"),
            "power_source": data.get("state", {})
            .get("general", {})
            .get("powerSource"),
            "door_open_mode": config.get("door", {}).get("openMode"),
            "door_close_mode": config.get("door", {}).get("closeMode"),
            "door_colour": config.get("door", {}).get("colour"),
            "fan_state": fan_state.get("state"),
            "fan_temperature": fan_state.get("temperature"),
            "fan_humidity": fan_state.get("humidity"),
            "fan_mode": fan_config.get("mode"),
            "fan_manual_speed": fan_config.get("manualSpeed"),
            "timezone": config.get("general", {}).get("timezone"),
            "language": config.get("general", {}).get("language"),
            "uptime": data.get("state", {})
            .get("general", {})
            .get("uptime"),
            "last_connected": data.get("lastConnected"),
        }
        return {k: v for k, v in attributes.items() if v is not None}
