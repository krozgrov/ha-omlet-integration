from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant
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
        self._stable_identity = get_stable_device_identity(
            coordinator.data.get(device_id),
            device_id,
        )

    @property
    def _device_data(self) -> dict:
        """Always return the latest device data from the coordinator.

        Avoid caching device data at init-time; coordinator updates should be reflected
        immediately in device_info and attributes.
        """
        data = self.coordinator.data.get(self.device_id, {}) or {}
        if data:
            return data

        for candidate_device_id, candidate_data in (self.coordinator.data or {}).items():
            if get_stable_device_identity(candidate_data, candidate_device_id) != self._stable_identity:
                continue
            current_device_id = candidate_data.get("deviceId") or candidate_device_id
            if current_device_id and current_device_id != self.device_id:
                self.device_id = current_device_id
            return candidate_data or {}

        return {}

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

    @property
    def current_device_id(self) -> str:
        """Return the latest runtime deviceId for API actions."""
        data = self._device_data
        return str(data.get("deviceId") or self.device_id)


def should_add_entity(hass: HomeAssistant, entity_domain: str, unique_id: str) -> bool:
    """Return True if an entity with unique_id is not already loaded."""
    ent_reg = er.async_get(hass)
    existing = ent_reg.async_get_entity_id(entity_domain, DOMAIN, unique_id)
    if existing and hass.states.get(existing) is not None:
        _LOGGER.debug(
            "Skipping add for %s %s; entity already loaded as %s",
            entity_domain,
            unique_id,
            existing,
        )
        return False
    return True


def normalize_device_serial(serial: Any) -> str | None:
    """Return a usable serial string, or None if not available."""
    if serial is None:
        return None
    normalized = str(serial).strip()
    if not normalized or normalized.lower() == "unknown":
        return None
    return normalized


def get_stable_device_identity(
    device_data: Mapping[str, Any] | None,
    fallback_device_id: str | None,
) -> str:
    """Return the stable identity for a device."""
    data = device_data or {}
    serial = normalize_device_serial(data.get("deviceSerial"))
    if serial:
        return serial
    device_id = data.get("deviceId") or fallback_device_id
    return str(device_id)


def build_entity_unique_id(
    device_data: Mapping[str, Any] | None,
    fallback_device_id: str | None,
    suffix: str,
) -> str:
    """Build a unique_id from the stable device identity and entity suffix."""
    clean_suffix = str(suffix).lstrip("_")
    return f"{get_stable_device_identity(device_data, fallback_device_id)}_{clean_suffix}"


def extract_known_suffix(unique_id: str, known_suffixes: Iterable[str]) -> str | None:
    """Return the matching entity suffix from a known suffix allowlist."""
    for suffix in sorted(known_suffixes, key=len, reverse=True):
        if unique_id.endswith(f"_{suffix}"):
            return suffix
    return None
