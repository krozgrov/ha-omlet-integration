import logging
from typing import Any

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .entity import OmletEntity

_LOGGER = logging.getLogger(__name__)


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

    entities: list[NumberEntity] = []
    for device_id, device_data in _fan_devices(coordinator):
        name = device_data.get("name") or device_id
        entities.append(OmletFanTempOn(coordinator, device_id, name))
        entities.append(OmletFanTempOff(coordinator, device_id, name))

    async_add_entities(entities)


class _OmletFanNumberBase(OmletEntity, NumberEntity):
    _CFG_KEY: str
    _LABEL: str

    def __init__(
        self,
        coordinator,
        device_id: str,
        device_name: str,
        *,
        native_min: float,
        native_max: float,
        native_step: float,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = f"{device_name} {self._LABEL}"
        self._attr_unique_id = f"{device_id}_{self._CFG_KEY}"
        self._attr_has_entity_name = True
        self._attr_native_min_value = native_min
        self._attr_native_max_value = native_max
        self._attr_native_step = native_step

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def native_value(self) -> float | None:
        raw = self._fan_cfg().get(self._CFG_KEY)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api_client.patch_device_configuration(
            self.device_id, {"fan": {self._CFG_KEY: int(value)}}
        )
        await self.coordinator.async_request_refresh()


class OmletFanTempOn(_OmletFanNumberBase):
    _CFG_KEY = "tempOn"
    _LABEL = "Fan Thermostatic Temp On"

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(
            coordinator,
            device_id,
            device_name,
            native_min=0,
            native_max=60,
            native_step=1,
        )


class OmletFanTempOff(_OmletFanNumberBase):
    _CFG_KEY = "tempOff"
    _LABEL = "Fan Thermostatic Temp Off"

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(
            coordinator,
            device_id,
            device_name,
            native_min=0,
            native_max=60,
            native_step=1,
        )


