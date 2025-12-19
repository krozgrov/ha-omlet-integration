import logging
from typing import Any

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import DOMAIN
from .entity import OmletEntity
from .fan_helpers import iter_fan_devices

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities: list[NumberEntity] = []
    for device_id, device_data in iter_fan_devices(coordinator):
        name = device_data.get("name") or device_id
        entities.append(OmletFanTempOn(coordinator, device_id, name))
        entities.append(OmletFanTempOff(coordinator, device_id, name))

    async_add_entities(entities)


class _OmletFanNumberBase(OmletEntity, NumberEntity):
    _CFG_KEY: str
    _TRANSLATION_KEY: str

    def __init__(
        self,
        coordinator,
        device_id: str,
        _device_name: str,
        *,
        native_min_c: float,
        native_max_c: float,
        native_step: float,
    ) -> None:
        super().__init__(coordinator, device_id)
        # With has_entity_name=True, HA will prefix the device name automatically.
        # Keep the entity name short for mobile UI.
        self._attr_translation_key = self._TRANSLATION_KEY
        self._attr_unique_id = f"{device_id}_{self._CFG_KEY}"
        self._attr_has_entity_name = True
        self._attr_native_step = native_step
        self._attr_mode = NumberMode.BOX
        self._attr_device_class = NumberDeviceClass.TEMPERATURE
        self._attr_entity_category = EntityCategory.CONFIG

        # API values appear to be Celsius; expose in user's HA temperature unit.
        self._api_unit = UnitOfTemperature.CELSIUS
        self._display_unit = (
            self.hass.config.units.temperature_unit
            if getattr(self, "hass", None) is not None
            else UnitOfTemperature.CELSIUS
        )
        self._attr_native_unit_of_measurement = self._display_unit

        # Set min/max in the displayed unit.
        min_v = TemperatureConverter.convert(native_min_c, self._api_unit, self._display_unit)
        max_v = TemperatureConverter.convert(native_max_c, self._api_unit, self._display_unit)
        self._attr_native_min_value = float(round(min_v))
        self._attr_native_max_value = float(round(max_v))

    def _fan_cfg(self) -> dict[str, Any]:
        return (self.coordinator.data.get(self.device_id, {}) or {}).get("configuration", {}).get("fan", {}) or {}

    @property
    def native_value(self) -> float | None:
        raw = self._fan_cfg().get(self._CFG_KEY)
        try:
            api_val = float(raw)
        except (TypeError, ValueError):
            return None
        return float(
            TemperatureConverter.convert(api_val, self._api_unit, self._display_unit)
        )

    async def async_set_native_value(self, value: float) -> None:
        api_val = TemperatureConverter.convert(value, self._display_unit, self._api_unit)
        await self.coordinator.api_client.patch_device_configuration(
            self.device_id, {"fan": {self._CFG_KEY: int(round(api_val))}}
        )
        await self.coordinator.async_request_refresh()


class OmletFanTempOn(_OmletFanNumberBase):
    _CFG_KEY = "tempOn"
    _TRANSLATION_KEY = "fan_temp_on"

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(
            coordinator,
            device_id,
            device_name,
            native_min_c=0,
            native_max_c=60,
            native_step=1,
        )


class OmletFanTempOff(_OmletFanNumberBase):
    _CFG_KEY = "tempOff"
    _TRANSLATION_KEY = "fan_temp_off"

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(
            coordinator,
            device_id,
            device_name,
            native_min_c=0,
            native_max_c=60,
            native_step=1,
        )
