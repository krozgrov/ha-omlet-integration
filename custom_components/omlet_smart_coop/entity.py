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
        self._device_data = coordinator.data.get(device_id, {})

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information"""
        state = self._device_data.get("state", {}).get("general", {})
        serial = self._device_data.get("deviceSerial")
        identifier_value = serial or self._device_data.get("deviceId") or self.device_id
        # Determine a friendly device name
        device_name = self._device_data.get("name")
        if not device_name or str(device_name).strip() == "":
            tail = str(identifier_value)[-6:] if identifier_value else "device"
            device_name = f"Omlet Coop {tail}"
        return DeviceInfo(
            identifiers={(DOMAIN, identifier_value)},
            name=device_name,
            manufacturer="Omlet",
            model=self._device_data.get("deviceType"),
            model_id=self._device_data.get("deviceTypeId"),
            sw_version=state.get("firmwareVersionCurrent"),
            hw_version=self.device_id,
            serial_number=serial,
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes specific to the device."""
        connectivity = self._device_data.get("state", {}).get("connectivity", {})
        config = self._device_data.get("configuration", {})
        attributes = {
            "device_id": self._device_data.get("deviceId"),
            "device_serial": self._device_data.get("deviceSerial"),
            "firmware_version_current": self._device_data.get("state", {})
            .get("general", {})
            .get("firmwareVersionCurrent"),
            "firmware_version_previous": self._device_data.get("state", {})
            .get("general", {})
            .get("firmwareVersionPrevious"),
            "firmware_last_check": self._device_data.get("state", {})
            .get("general", {})
            .get("firmwareLastCheck"),
            "device_type_id": self._device_data.get("deviceTypeId"),
            "door_type": config.get("door", {}).get("doorType"),
            "group_id": self._device_data.get("groupId"),
            "delete_pending": self._device_data.get("deletePending"),
            "battery_count": self._device_data.get("batteryCount"),
            "battery_warned": self._device_data.get("batteryWarned"),
            "ble_only": self._device_data.get("bleOnly"),
            "wifi_state": config.get("connectivity", {}).get("wifiState"),
            "wifi_ssid": connectivity.get("ssid"),
            "wifi_strength": connectivity.get("wifiStrength"),
            "wifi_connection_status": connectivity.get("connected"),
            "overdue_connection": self._device_data.get("overdueConnection"),
            "power_source": self._device_data.get("state", {})
            .get("general", {})
            .get("powerSource"),
            "door_open_mode": config.get("door", {}).get("openMode"),
            "door_close_mode": config.get("door", {}).get("closeMode"),
            "door_colour": config.get("door", {}).get("colour"),
            "timezone": config.get("general", {}).get("timezone"),
            "language": config.get("general", {}).get("language"),
            "uptime": self._device_data.get("state", {})
            .get("general", {})
            .get("uptime"),
            "last_connected": self._device_data.get("lastConnected"),
        }
        return {k: v for k, v in attributes.items() if v is not None}
