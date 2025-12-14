import asyncio
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import OmletEntity

_LOGGER = logging.getLogger(__name__)


def _fan_is_on(device_data: dict[str, Any]) -> bool:
    state = ((device_data.get("state") or {}).get("fan") or {}).get("state") or ""
    return str(state).lower() in {"on", "onpending", "boost", "boostpending"}


async def _apply_fan_config(
    coordinator, device_id: str, fan_patch: dict[str, Any], cycle_if_on: bool = False
) -> None:
    """Patch fan configuration; optionally cycle off/on to apply changes."""
    await coordinator.api_client.patch_device_configuration(device_id, {"fan": fan_patch})

    if cycle_if_on:
        device_data = coordinator.data.get(device_id, {}) or {}
        if _fan_is_on(device_data):
            # Omlet applies some settings only after toggling off/on.
            try:
                await coordinator.api_client.execute_action(f"device/{device_id}/action/off")
                await asyncio.sleep(0.5)
                await coordinator.api_client.execute_action(f"device/{device_id}/action/on")
            except Exception as err:
                _LOGGER.debug("Failed to cycle fan for %s: %r", device_id, err)

    await coordinator.async_request_refresh()
    # Omlet can briefly report *pending* after config changes; do a quick follow-up refresh.
    if getattr(coordinator, "hass", None):
        async def _delayed(delay_s: float) -> None:
            await asyncio.sleep(delay_s)
            await coordinator.async_request_refresh()

        for delay in (1.5, 5.0):
            coordinator.hass.async_create_task(_delayed(delay))


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

    entities: list[SelectEntity] = []
    for device_id, device_data in _fan_devices(coordinator):
        name = device_data.get("name") or device_id
        fan_cfg = (device_data.get("configuration", {}) or {}).get("fan", {}) or {}
        entities.append(OmletFanModeSelect(coordinator, device_id, name))
        entities.append(OmletFanManualSpeedSelect(coordinator, device_id, name))
        entities.append(OmletFanTimeSpeed1Select(coordinator, device_id, name))
        entities.append(OmletFanThermostatSpeedSelect(coordinator, device_id, name))

        # Slots 2-4 only if configured (non-00:00 on/off)
        for slot in (2, 3, 4):
            on_key = f"timeOn{slot}"
            off_key = f"timeOff{slot}"
            if (fan_cfg.get(on_key) and fan_cfg.get(on_key) != "00:00") or (
                fan_cfg.get(off_key) and fan_cfg.get(off_key) != "00:00"
            ):
                if slot == 2:
                    entities.append(OmletFanTimeSpeed2Select(coordinator, device_id, name))
                elif slot == 3:
                    entities.append(OmletFanTimeSpeed3Select(coordinator, device_id, name))
                else:
                    entities.append(OmletFanTimeSpeed4Select(coordinator, device_id, name))

    async_add_entities(entities)


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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"mode": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanManualSpeedSelect(OmletEntity, SelectEntity):
    _OPTIONS = ["Low", "Medium", "High"]
    _MAP = {"Low": 60, "Medium": 80, "High": 100}

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Manual Speed"
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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"mode": "manual", "manualSpeed": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed1Select(OmletEntity, SelectEntity):
    _OPTIONS = ["Low", "Medium", "High"]
    _MAP = {"Low": 60, "Medium": 80, "High": 100}

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Time Speed (Slot 1)"
        self._attr_unique_id = f"{device_id}_fan_time_speed_1"
        self._attr_options = self._OPTIONS
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.CONFIG

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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"timeSpeed1": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed2Select(OmletFanTimeSpeed1Select):
    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = "Time Speed (Slot 2)"
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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"timeSpeed2": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed3Select(OmletFanTimeSpeed2Select):
    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = "Time Speed (Slot 3)"
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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"timeSpeed3": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanTimeSpeed4Select(OmletFanTimeSpeed2Select):
    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id, device_name)
        self._attr_name = "Time Speed (Slot 4)"
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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"timeSpeed4": self._MAP[option]},
            cycle_if_on=True,
        )


class OmletFanThermostatSpeedSelect(OmletEntity, SelectEntity):
    _OPTIONS = ["Low", "Medium", "High"]
    _MAP = {"Low": 60, "Medium": 80, "High": 100}

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Temp Speed"
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
        await _apply_fan_config(
            self.coordinator,
            self.device_id,
            {"tempSpeed": self._MAP[option]},
            cycle_if_on=True,
        )


