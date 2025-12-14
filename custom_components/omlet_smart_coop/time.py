import logging
from datetime import time as dt_time
from typing import Any

from homeassistant.components.time import TimeEntity

from .const import DOMAIN
from .entity import OmletEntity

_LOGGER = logging.getLogger(__name__)


def _parse_hhmm(value: Any) -> dt_time | None:
    if not value:
        return None
    if isinstance(value, dt_time):
        return value
    s = str(value)
    if ":" not in s:
        return None
    try:
        hh, mm = s.split(":", 1)
        return dt_time(hour=int(hh), minute=int(mm))
    except Exception:
        return None


def _fmt_hhmm(value: dt_time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


def _fan_devices(coordinator) -> list[tuple[str, dict[str, Any]]]:
    devices = coordinator.data or {}
    out: list[tuple[str, dict[str, Any]]] = []
    for device_id, device_data in devices.items():
        state = device_data.get("state", {}) or {}
        config = device_data.get("configuration", {}) or {}
        if state.get("fan") or config.get("fan"):
            out.append((device_id, device_data))
    return out


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities: list[TimeEntity] = []
    for device_id, device_data in _fan_devices(coordinator):
        name = device_data.get("name") or device_id
        entities.append(OmletFanTimeOn1(coordinator, device_id, name))
        entities.append(OmletFanTimeOff1(coordinator, device_id, name))

    async_add_entities(entities)


class _OmletFanTimeBase(OmletEntity, TimeEntity):
    _CFG_KEY: str
    _LABEL: str

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = f"{device_name} {self._LABEL}"
        self._attr_unique_id = f"{device_id}_{self._CFG_KEY}"
        self._attr_has_entity_name = True

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def native_value(self) -> dt_time | None:
        return _parse_hhmm(self._fan_cfg().get(self._CFG_KEY))

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.api_client.patch_device_configuration(
            self.device_id, {"fan": {self._CFG_KEY: _fmt_hhmm(value)}}
        )
        await self.coordinator.async_request_refresh()


class OmletFanTimeOn1(_OmletFanTimeBase):
    _CFG_KEY = "timeOn1"
    _LABEL = "Fan Time On (Slot 1)"


class OmletFanTimeOff1(_OmletFanTimeBase):
    _CFG_KEY = "timeOff1"
    _LABEL = "Fan Time Off (Slot 1)"


