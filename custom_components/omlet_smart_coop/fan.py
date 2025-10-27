import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature

from .const import DOMAIN
from .entity import OmletEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up fan platforms from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up fans for devices: %s", coordinator.data)

    fans = []
    for device_id, device_data in coordinator.data.items():
        fan_state = device_data.get("state", {}).get("fan")
        if fan_state:
            fans.append(OmletFan(coordinator, device_id, device_data["name"]))

    async_add_entities(fans)


class OmletFan(OmletEntity, FanEntity):
    """Representation of an Omlet smart coop fan."""

    _ACTION_ON = "on"
    _ACTION_OFF = "off"
    _ACTION_BOOST = "boost"

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = f"{device_name} Fan"
        self._attr_unique_id = f"{device_id}_fan"
        self._attr_has_entity_name = True

    def _device_state(self) -> dict[str, Any]:
        return self.coordinator.data.get(self.device_id, {})

    def _fan_state(self) -> dict[str, Any]:
        return self._device_state().get("state", {}).get("fan", {}) or {}

    def _find_action(self, action_value: str) -> dict[str, Any] | None:
        actions = self._device_state().get("actions", []) or []
        return next(
            (action for action in actions if action.get("actionValue") == action_value),
            None,
        )

    @property
    def available(self) -> bool:
        """Return True if the fan provides state data."""
        return bool(self._fan_state())

    @property
    def is_on(self) -> bool:
        """Return whether the fan is running."""
        state = (self._fan_state().get("state") or "").lower()
        return state in {"on", "onpending", "boost", "boostpending"}

    @property
    def preset_mode(self) -> str | None:
        """Return the active preset mode, if any."""
        state = (self._fan_state().get("state") or "").lower()
        if state in {"boost", "boostpending"} and self._has_boost():
            return "boost"
        return None

    @property
    def preset_modes(self) -> list[str]:
        """Return the list of supported preset modes."""
        return ["boost"] if self._has_boost() else []

    @property
    def supported_features(self) -> FanEntityFeature:
        """Return supported fan features."""
        features = FanEntityFeature(0)
        if self._has_boost():
            features |= FanEntityFeature.PRESET_MODE
        return features

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the fan on."""
        preset = kwargs.get("preset_mode")
        if preset == "boost" and self._has_boost():
            await self._execute_action(self._ACTION_BOOST)
        else:
            await self._execute_action(self._ACTION_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the fan off."""
        await self._execute_action(self._ACTION_OFF)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        if preset_mode != "boost" or not self._has_boost():
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        await self._execute_action(self._ACTION_BOOST)
        await self.coordinator.async_request_refresh()

    def _has_boost(self) -> bool:
        return self._find_action(self._ACTION_BOOST) is not None

    async def _execute_action(self, action: str) -> None:
        """Execute an action on the fan."""
        action_data = self._find_action(action)
        if not action_data:
            _LOGGER.warning(
                "Action %s unavailable for fan %s", action, self.device_id
            )
            return
        await self.coordinator.api_client.execute_action(action_data["url"])
