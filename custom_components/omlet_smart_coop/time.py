import logging
from datetime import time as dt_time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import OmletEntity
from .fan_helpers import iter_fan_devices, fan_config, parse_hhmm, format_hhmm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities: list[TimeEntity] = []
    for device_id, device_data in iter_fan_devices(coordinator):
        name = device_data.get("name") or device_id
        fan_cfg = fan_config(device_data)

        # Slot 1 always visible
        entities.append(OmletFanTimeOn1(coordinator, device_id, name))
        entities.append(OmletFanTimeOff1(coordinator, device_id, name))

        # Slots 2-4 only if configured (non-00:00 on/off)
        for slot in (2, 3, 4):
            on_key = f"timeOn{slot}"
            off_key = f"timeOff{slot}"
            if (fan_cfg.get(on_key) and fan_cfg.get(on_key) != "00:00") or (
                fan_cfg.get(off_key) and fan_cfg.get(off_key) != "00:00"
            ):
                if slot == 2:
                    entities.append(OmletFanTimeOn2(coordinator, device_id, name))
                    entities.append(OmletFanTimeOff2(coordinator, device_id, name))
                elif slot == 3:
                    entities.append(OmletFanTimeOn3(coordinator, device_id, name))
                    entities.append(OmletFanTimeOff3(coordinator, device_id, name))
                else:
                    entities.append(OmletFanTimeOn4(coordinator, device_id, name))
                    entities.append(OmletFanTimeOff4(coordinator, device_id, name))

    async_add_entities(entities)


class _OmletFanTimeBase(OmletEntity, TimeEntity):
    _CFG_KEY: str
    _LABEL: str

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = self._LABEL
        self._attr_unique_id = f"{device_id}_{self._CFG_KEY}"
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def native_value(self) -> dt_time | None:
        return parse_hhmm(self._fan_cfg().get(self._CFG_KEY))

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.api_client.patch_device_configuration(
            self.device_id, {"fan": {self._CFG_KEY: format_hhmm(value)}}
        )
        await self.coordinator.async_request_refresh()


class OmletFanTimeOn1(_OmletFanTimeBase):
    _CFG_KEY = "timeOn1"
    _LABEL = "Time On (Slot 1)"


class OmletFanTimeOff1(_OmletFanTimeBase):
    _CFG_KEY = "timeOff1"
    _LABEL = "Time Off (Slot 1)"


class OmletFanTimeOn2(_OmletFanTimeBase):
    _CFG_KEY = "timeOn2"
    _LABEL = "Time On (Slot 2)"


class OmletFanTimeOff2(_OmletFanTimeBase):
    _CFG_KEY = "timeOff2"
    _LABEL = "Time Off (Slot 2)"


class OmletFanTimeOn3(_OmletFanTimeBase):
    _CFG_KEY = "timeOn3"
    _LABEL = "Time On (Slot 3)"


class OmletFanTimeOff3(_OmletFanTimeBase):
    _CFG_KEY = "timeOff3"
    _LABEL = "Time Off (Slot 3)"


class OmletFanTimeOn4(_OmletFanTimeBase):
    _CFG_KEY = "timeOn4"
    _LABEL = "Time On (Slot 4)"


class OmletFanTimeOff4(_OmletFanTimeBase):
    _CFG_KEY = "timeOff4"
    _LABEL = "Time Off (Slot 4)"


