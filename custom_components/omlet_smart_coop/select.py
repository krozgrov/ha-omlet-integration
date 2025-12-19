import asyncio
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import OmletEntity
from .fan_helpers import FAN_SPEED_MAP, iter_fan_devices, patch_fan_config_and_refresh

_LOGGER = logging.getLogger(__name__)


def _fan_is_on(device_data: dict[str, Any]) -> bool:
    state = ((device_data.get("state") or {}).get("fan") or {}).get("state") or ""
    return str(state).lower() in {"on", "onpending", "boost", "boostpending"}


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities: list[SelectEntity] = []
    dynamic_entities: list[OmletFanTimeSpeed1Select] = []
    for device_id, device_data in iter_fan_devices(coordinator):
        name = device_data.get("name") or device_id
        entities.append(OmletFanModeSelect(coordinator, device_id, name))
        entities.append(OmletFanManualSpeedSelect(coordinator, device_id, name))
        entities.append(OmletFanTimeSpeed1Select(coordinator, device_id, name))
        for cls in (OmletFanTimeSpeed2Select, OmletFanTimeSpeed3Select, OmletFanTimeSpeed4Select):
            entity = cls(coordinator, device_id, name)
            entities.append(entity)
            dynamic_entities.append(entity)
        entities.append(OmletFanThermostatSpeedSelect(coordinator, device_id, name))

    async_add_entities(entities)
    _sync_time_speed_visibility(hass, coordinator, dynamic_entities)


class OmletFanModeSelect(OmletEntity, SelectEntity):
    _OPTIONS = ["Manual", "Time", "Thermostatic"]
    # Omlet uses mode="temperature" for thermostatic operation.
    _MAP = {"Manual": "manual", "Time": "time", "Thermostatic": "temperature"}

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Mode"
        self._attr_unique_id = f"{device_id}_fan_mode"
        self._attr_options = self._OPTIONS
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def current_option(self) -> str | None:
        mode = (self._fan_cfg().get("mode") or "").lower()
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(mode)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"mode": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanManualSpeedSelect(OmletEntity, SelectEntity):
    _OPTIONS = ["Low", "Medium", "High"]
    _MAP = {"Low": FAN_SPEED_MAP["low"], "Medium": FAN_SPEED_MAP["medium"], "High": FAN_SPEED_MAP["high"]}

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Manual Spd"
        self._attr_unique_id = f"{device_id}_fan_manual_speed"
        self._attr_options = self._OPTIONS
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def current_option(self) -> str | None:
        cfg = self._fan_cfg()
        if (cfg.get("mode") or "").lower() != "manual":
            return None
        raw = cfg.get("manualSpeed")
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        nearest = min(self._MAP.values(), key=lambda s: abs(s - speed))
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(nearest)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"mode": "manual", "manualSpeed": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed1Select(OmletEntity, SelectEntity):
    _OPTIONS = ["Low", "Medium", "High"]
    _MAP = {"Low": FAN_SPEED_MAP["low"], "Medium": FAN_SPEED_MAP["medium"], "High": FAN_SPEED_MAP["high"]}
    _SLOT_INDEX = 1

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Time Spd 1"
        self._attr_unique_id = f"{device_id}_fan_time_speed_1"
        self._attr_options = self._OPTIONS
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG
        self._slot_index = self._SLOT_INDEX
        self._dynamic_slot = self._slot_index >= 2

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def current_option(self) -> str | None:
        raw = self._fan_cfg().get("timeSpeed1")
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        nearest = min(self._MAP.values(), key=lambda s: abs(s - speed))
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(nearest)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"timeSpeed1": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed2Select(OmletFanTimeSpeed1Select):
    _SLOT_INDEX = 2

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = "Time Spd 2"
        self._attr_unique_id = f"{device_id}_fan_time_speed_2"

    @property
    def current_option(self) -> str | None:
        raw = self._fan_cfg().get("timeSpeed2")
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        nearest = min(self._MAP.values(), key=lambda s: abs(s - speed))
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(nearest)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"timeSpeed2": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed3Select(OmletFanTimeSpeed2Select):
    _SLOT_INDEX = 3

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = "Time Spd 3"
        self._attr_unique_id = f"{device_id}_fan_time_speed_3"

    @property
    def current_option(self) -> str | None:
        raw = self._fan_cfg().get("timeSpeed3")
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        nearest = min(self._MAP.values(), key=lambda s: abs(s - speed))
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(nearest)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"timeSpeed3": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed4Select(OmletFanTimeSpeed2Select):
    _SLOT_INDEX = 4

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = "Time Spd 4"
        self._attr_unique_id = f"{device_id}_fan_time_speed_4"

    @property
    def current_option(self) -> str | None:
        raw = self._fan_cfg().get("timeSpeed4")
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        nearest = min(self._MAP.values(), key=lambda s: abs(s - speed))
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(nearest)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"timeSpeed4": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanThermostatSpeedSelect(OmletEntity, SelectEntity):
    _OPTIONS = ["Low", "Medium", "High"]
    _MAP = {"Low": FAN_SPEED_MAP["low"], "Medium": FAN_SPEED_MAP["medium"], "High": FAN_SPEED_MAP["high"]}

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Tstat Spd"
        self._attr_unique_id = f"{device_id}_fan_thermostat_speed"
        self._attr_options = self._OPTIONS
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def current_option(self) -> str | None:
        raw = self._fan_cfg().get("tempSpeed")
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        nearest = min(self._MAP.values(), key=lambda s: abs(s - speed))
        inv = {v: k for k, v in self._MAP.items()}
        return inv.get(nearest)

    async def async_select_option(self, option: str) -> None:
        if option not in self._OPTIONS:
            raise ValueError(f"Unsupported option: {option}")
        await patch_fan_config_and_refresh(
            self.hass,
            self.coordinator,
            self.device_id,
            {"tempSpeed": self._MAP[option]},
            cycle_if_on=True,
        )


def _slot_is_configured(fan_cfg: dict[str, Any], slot: int) -> bool:
    """Return True if the slot has a real on/off time set."""
    on_val = fan_cfg.get(f"timeOn{slot}")
    off_val = fan_cfg.get(f"timeOff{slot}")
    return (on_val and on_val != "00:00") or (off_val and off_val != "00:00")


def _sync_time_speed_visibility(hass, coordinator, entities: list[OmletFanTimeSpeed1Select]) -> None:
    """Hide/show time speed slots 2-4 based on current config."""
    ent_reg = async_get_entity_registry(hass)

    def _update_for_device(device_id: str, fan_cfg: dict[str, Any]) -> None:
        for entity in entities:
            if entity.device_id != device_id or not getattr(entity, "_dynamic_slot", False):
                continue
            if not entity.entity_id:
                continue
            hide = not _slot_is_configured(fan_cfg, entity._slot_index)
            reg_entry = ent_reg.async_get(entity.entity_id)
            if not reg_entry:
                continue
            if hide:
                if reg_entry.hidden_by != er.RegistryEntryHider.USER:
                    ent_reg.async_update_entity(
                        entity.entity_id,
                        hidden_by=er.RegistryEntryHider.INTEGRATION,
                    )
            else:
                if reg_entry.hidden_by == er.RegistryEntryHider.INTEGRATION:
                    ent_reg.async_update_entity(entity.entity_id, hidden_by=None)

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
