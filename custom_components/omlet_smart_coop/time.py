import logging
from datetime import time as dt_time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import OmletEntity
from .fan_helpers import iter_fan_devices, parse_hhmm, format_hhmm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities: list[TimeEntity] = []
    for device_id, device_data in iter_fan_devices(coordinator):
        name = device_data.get("name") or device_id
        entities.append(OmletFanTimeOn1(coordinator, device_id, name))
        entities.append(OmletFanTimeOff1(coordinator, device_id, name))
        for cls in (
            OmletFanTimeOn2,
            OmletFanTimeOff2,
            OmletFanTimeOn3,
            OmletFanTimeOff3,
            OmletFanTimeOn4,
            OmletFanTimeOff4,
        ):
            entities.append(cls(coordinator, device_id, name))

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
    _LABEL = "03: Time On 1"


class OmletFanTimeOff1(_OmletFanTimeBase):
    _CFG_KEY = "timeOff1"
    _LABEL = "03: Time Off 1"


class OmletFanTimeOn2(_OmletFanTimeBase):
    _CFG_KEY = "timeOn2"
    _LABEL = "03: Time On 2"


class OmletFanTimeOff2(_OmletFanTimeBase):
    _CFG_KEY = "timeOff2"
    _LABEL = "03: Time Off 2"


class OmletFanTimeOn3(_OmletFanTimeBase):
    _CFG_KEY = "timeOn3"
    _LABEL = "03: Time On 3"


class OmletFanTimeOff3(_OmletFanTimeBase):
    _CFG_KEY = "timeOff3"
    _LABEL = "03: Time Off 3"


class OmletFanTimeOn4(_OmletFanTimeBase):
    _CFG_KEY = "timeOn4"
    _LABEL = "03: Time On 4"


class OmletFanTimeOff4(_OmletFanTimeBase):
    _CFG_KEY = "timeOff4"
    _LABEL = "03: Time Off 4"
