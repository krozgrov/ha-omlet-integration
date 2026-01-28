import logging
from datetime import time as dt_time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import OmletEntity, should_add_entity
from .fan_helpers import iter_fan_devices, parse_hhmm, format_hhmm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities: list[TimeEntity] = []
    for device_id, device_data in iter_fan_devices(coordinator):
        name = device_data.get("name") or device_id
        if should_add_entity(hass, "time", f"{device_id}_timeOn1"):
            entities.append(OmletFanTimeOn1(coordinator, device_id, name))
        if should_add_entity(hass, "time", f"{device_id}_timeOff1"):
            entities.append(OmletFanTimeOff1(coordinator, device_id, name))
        for cls in (
            OmletFanTimeOn2,
            OmletFanTimeOff2,
            OmletFanTimeOn3,
            OmletFanTimeOff3,
            OmletFanTimeOn4,
            OmletFanTimeOff4,
        ):
            cfg_key = cls._CFG_KEY
            if should_add_entity(hass, "time", f"{device_id}_{cfg_key}"):
                entities.append(cls(coordinator, device_id, name))

    async_add_entities(entities)


class _OmletFanTimeBase(OmletEntity, TimeEntity):
    _CFG_KEY: str
    _TRANSLATION_KEY: str

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_translation_key = self._TRANSLATION_KEY
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

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.hass or not self.entity_id:
            return
        ent_reg = async_get_entity_registry(self.hass)
        reg_entry = ent_reg.async_get(self.entity_id)
        if reg_entry and reg_entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
            ent_reg.async_update_entity(self.entity_id, hidden_by=None)


class OmletFanTimeOn1(_OmletFanTimeBase):
    _CFG_KEY = "timeOn1"
    _TRANSLATION_KEY = "fan_time_on_1"


class OmletFanTimeOff1(_OmletFanTimeBase):
    _CFG_KEY = "timeOff1"
    _TRANSLATION_KEY = "fan_time_off_1"


class OmletFanTimeOn2(_OmletFanTimeBase):
    _CFG_KEY = "timeOn2"
    _TRANSLATION_KEY = "fan_time_on_2"


class OmletFanTimeOff2(_OmletFanTimeBase):
    _CFG_KEY = "timeOff2"
    _TRANSLATION_KEY = "fan_time_off_2"


class OmletFanTimeOn3(_OmletFanTimeBase):
    _CFG_KEY = "timeOn3"
    _TRANSLATION_KEY = "fan_time_on_3"


class OmletFanTimeOff3(_OmletFanTimeBase):
    _CFG_KEY = "timeOff3"
    _TRANSLATION_KEY = "fan_time_off_3"


class OmletFanTimeOn4(_OmletFanTimeBase):
    _CFG_KEY = "timeOn4"
    _TRANSLATION_KEY = "fan_time_on_4"


class OmletFanTimeOff4(_OmletFanTimeBase):
    _CFG_KEY = "timeOff4"
    _TRANSLATION_KEY = "fan_time_off_4"
