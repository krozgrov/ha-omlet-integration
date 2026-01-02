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
        device_id = data.get("deviceId") or self.device_id
        identifier_value = serial or device_id
        identifiers = {(DOMAIN, identifier_value)}
        if serial and device_id:
            identifiers.add((DOMAIN, device_id))
        # Determine a friendly device name
        device_name = data.get("name")
        if not device_name or str(device_name).strip() == "":
            tail = str(identifier_value)[-6:] if identifier_value else "device"
            device_name = f"Omlet Coop {tail}"
        return DeviceInfo(
            identifiers=identifiers,
            name=device_name,
            manufacturer="Omlet",
            model=data.get("deviceType"),
            model_id=data.get("deviceTypeId"),
            sw_version=state.get("firmwareVersionCurrent"),
            serial_number=serial,
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes specific to the device."""
        data = self._device_data
        attributes = {
            "device_id": data.get("deviceId"),
            "device_serial": data.get("deviceSerial"),
        }
        return {key: value for key, value in attributes.items() if value is not None}
