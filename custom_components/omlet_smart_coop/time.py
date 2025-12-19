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
    dynamic_entities: list[_OmletFanTimeBase] = []
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
            entity = cls(coordinator, device_id, name)
            entities.append(entity)
            dynamic_entities.append(entity)

    async_add_entities(entities)
    _sync_time_slot_visibility(hass, coordinator, dynamic_entities)


class _OmletFanTimeBase(OmletEntity, TimeEntity):
    _CFG_KEY: str
    _LABEL: str

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = self._LABEL
        self._attr_unique_id = f"{device_id}_{self._CFG_KEY}"
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG
        # Slots 2-4 are dynamically hidden when cleared (00:00/None).
        self._dynamic_slot = False
        self._slot_index = 0
        if self._CFG_KEY.startswith("timeOn"):
            self._dynamic_slot = True
            self._slot_index = int(self._CFG_KEY.replace("timeOn", ""))
        elif self._CFG_KEY.startswith("timeOff"):
            self._dynamic_slot = True
            self._slot_index = int(self._CFG_KEY.replace("timeOff", ""))

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
        if not self._dynamic_slot or self._slot_index <= 1:
            return
        if not self.hass or not self.entity_id:
            return
        device_data = self.coordinator.data.get(self.device_id, {}) or {}
        fan_cfg = (device_data.get("configuration", {}) or {}).get("fan", {}) or {}
        ent_reg = async_get_entity_registry(self.hass)
        _update_registry_visibility(
            ent_reg,
            self.entity_id,
            hide=not _slot_is_configured(fan_cfg, self._slot_index),
        )


def _slot_is_configured(fan_cfg: dict[str, Any], slot: int) -> bool:
    """Return True if the slot has a real on/off time set."""
    on_val = fan_cfg.get(f"timeOn{slot}")
    off_val = fan_cfg.get(f"timeOff{slot}")
    return (on_val and on_val != "00:00") or (off_val and off_val != "00:00")


def _update_registry_visibility(ent_reg, entity_id: str, *, hide: bool) -> None:
    reg_entry = ent_reg.async_get(entity_id)
    if not reg_entry:
        return
    if hide:
        if reg_entry.hidden_by != er.RegistryEntryHider.USER:
            if reg_entry.hidden_by != er.RegistryEntryHider.INTEGRATION:
                ent_reg.async_update_entity(
                    entity_id,
                    hidden_by=er.RegistryEntryHider.INTEGRATION,
                )
    else:
        if reg_entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
            ent_reg.async_update_entity(entity_id, hidden_by=None)


def _sync_time_slot_visibility(hass, coordinator, entities: list[_OmletFanTimeBase]) -> None:
    """Hide/show time slot 2-4 entities based on current config."""
    ent_reg = async_get_entity_registry(hass)

    def _update_for_device(device_id: str, fan_cfg: dict[str, Any]) -> None:
        for entity in entities:
            if entity.device_id != device_id or not entity._dynamic_slot:
                continue
            if entity._slot_index <= 1:
                continue
            if not entity.entity_id:
                continue
            _update_registry_visibility(
                ent_reg,
                entity.entity_id,
                hide=not _slot_is_configured(fan_cfg, entity._slot_index),
            )

    # Initial sync
    for device_id in {e.device_id for e in entities}:
        device_data = coordinator.data.get(device_id, {}) or {}
        fan_cfg = (device_data.get("configuration", {}) or {}).get("fan", {}) or {}
        _update_for_device(device_id, fan_cfg)

    # Listen for future updates
    def _handle_update() -> None:
        for device_id in {e.device_id for e in entities}:
            device_data = coordinator.data.get(device_id, {}) or {}
            fan_cfg = (device_data.get("configuration", {}) or {}).get("fan", {}) or {}
            _update_for_device(device_id, fan_cfg)

    coordinator.async_add_listener(_handle_update)


class OmletFanTimeOn1(_OmletFanTimeBase):
    _CFG_KEY = "timeOn1"
    _LABEL = "Time On 1"


class OmletFanTimeOff1(_OmletFanTimeBase):
    _CFG_KEY = "timeOff1"
    _LABEL = "Time Off 1"


class OmletFanTimeOn2(_OmletFanTimeBase):
    _CFG_KEY = "timeOn2"
    _LABEL = "Time On 2"


class OmletFanTimeOff2(_OmletFanTimeBase):
    _CFG_KEY = "timeOff2"
    _LABEL = "Time Off 2"


class OmletFanTimeOn3(_OmletFanTimeBase):
    _CFG_KEY = "timeOn3"
    _LABEL = "Time On 3"


class OmletFanTimeOff3(_OmletFanTimeBase):
    _CFG_KEY = "timeOff3"
    _LABEL = "Time Off 3"


class OmletFanTimeOn4(_OmletFanTimeBase):
    _CFG_KEY = "timeOn4"
    _LABEL = "Time On 4"


class OmletFanTimeOff4(_OmletFanTimeBase):
    _CFG_KEY = "timeOff4"
    _LABEL = "Time Off 4"
