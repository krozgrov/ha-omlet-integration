import logging
import asyncio
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components import persistent_notification as pn

from .const import DOMAIN
from .entity import OmletEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up fan platforms from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up fans for devices: %s", coordinator.data)

    fans = []
    fan_action_values = {"on", "off", "boost"}
    for device_id, device_data in coordinator.data.items():
        # Any device that reports fan state can expose a fan entity regardless of deviceType label
        fan_state = device_data.get("state", {}).get("fan")
        if not fan_state:
            continue
        has_fan_actions = any(
            (action.get("actionValue") or "").lower() in fan_action_values
            for action in device_data.get("actions", []) or []
        )
        if not has_fan_actions:
            continue
        fans.append(OmletFan(coordinator, device_id, device_data["name"]))

    async_add_entities(fans)


class OmletFan(OmletEntity, FanEntity):
    """Representation of an Omlet smart coop fan."""

    _ACTION_ON = "on"
    _ACTION_OFF = "off"
    _ACTION_BOOST = "boost"
    # These are the actual device values observed in Omlet (manual mode).
    # Low=60, Medium=80, High=100.
    _MANUAL_SPEEDS = (60, 80, 100)

    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = f"{device_name} Fan"
        self._attr_unique_id = f"{device_id}_fan"
        self._attr_has_entity_name = True

    def _device_state(self) -> dict[str, Any]:
        return self.coordinator.data.get(self.device_id, {})

    def _fan_state(self) -> dict[str, Any]:
        return self._device_state().get("state", {}).get("fan", {}) or {}

    def _fan_config(self) -> dict[str, Any]:
        return self._device_state().get("configuration", {}).get("fan", {}) or {}

    def _find_action(self, action_value: str) -> dict[str, Any] | None:
        actions = self._device_state().get("actions", []) or []
        action_value = (action_value or "").lower()
        return next(
            (
                action
                for action in actions
                if (action.get("actionValue") or "").lower() == action_value
            ),
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
        # Treat *pending-off* as still running until the device confirms "off".
        return state in {"on", "onpending", "boost", "boostpending", "offpending"}

    def _schedule_followup_refresh(self) -> None:
        """Poll shortly after actions since Omlet may report *pending* briefly."""
        if not getattr(self, "hass", None):
            return

        async def _delayed(delay_s: float) -> None:
            await asyncio.sleep(delay_s)
            await self.coordinator.async_request_refresh()

        # A few quick follow-ups to clear pending states without waiting for next poll.
        for delay in (1.5, 5.0, 15.0):
            self.hass.async_create_task(_delayed(delay))

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
        # Home Assistant gates service calls like `fan.turn_on` behind these flags.
        # If we don't advertise TURN_ON/TURN_OFF, HA will reject the call even if
        # async_turn_on/async_turn_off are implemented.
        features = FanEntityFeature(0)
        if self._has_on():
            features |= FanEntityFeature.TURN_ON
        if self._has_off():
            features |= FanEntityFeature.TURN_OFF
        # Speed control: Omlet supports manualSpeed (0-100) in manual mode.
        # Some HA versions call this SET_SPEED, newer ones expose percentage APIs.
        set_speed_feature = getattr(FanEntityFeature, "SET_SPEED", None)
        if set_speed_feature is not None:
            features |= set_speed_feature
        if self._has_boost():
            features |= FanEntityFeature.PRESET_MODE
        return features

    @property
    def percentage(self) -> int | None:
        """Return current target speed as a percentage (3 discrete steps)."""
        cfg = self._fan_config()
        if (cfg.get("mode") or "").lower() != "manual":
            return None
        raw = cfg.get("manualSpeed")
        if raw is None:
            return None
        try:
            speed = int(raw)
        except (TypeError, ValueError):
            return None
        # Snap to the closest known speed, then report as 33/67/100 for HA UI.
        nearest = min(self._MANUAL_SPEEDS, key=lambda s: abs(s - speed))
        if nearest == self._MANUAL_SPEEDS[0]:
            return 33
        if nearest == self._MANUAL_SPEEDS[1]:
            return 67
        return 100

    @property
    def speed_count(self) -> int:
        """Expose 3 discrete speeds (low/medium/high) to HA when supported."""
        return 3

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed (low/medium/high) by forcing manual mode + manualSpeed."""
        # Some HA UIs/cards "turn off" by calling set_percentage(0).
        # Treat 0% as OFF for a predictable UX.
        if percentage is not None and int(percentage) <= 0:
            await self.async_turn_off()
            return

        # Map arbitrary percentage into 3 buckets.
        pct = max(0, min(100, int(percentage)))
        if pct <= 33:
            target = self._MANUAL_SPEEDS[0]
        elif pct <= 67:
            target = self._MANUAL_SPEEDS[1]
        else:
            target = self._MANUAL_SPEEDS[2]

        await self.coordinator.api_client.patch_device_configuration(
            self.device_id,
            {"fan": {"mode": "manual", "manualSpeed": target}},
        )
        # Omlet applies manualSpeed after the fan is toggled off/on. If it is
        # currently running, cycle it to apply the new speed.
        if self.is_on:
            await self._execute_action(self._ACTION_OFF)
            await asyncio.sleep(0.5)
            await self._execute_action(self._ACTION_ON)

        await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs,
    ) -> None:
        """Turn the fan on."""
        # HA may call this with positional args (percentage, preset_mode), so keep
        # an explicit signature to avoid TypeError.
        _ = kwargs
        if percentage is not None:
            await self.async_set_percentage(percentage)

        preset = preset_mode or kwargs.get("preset_mode")
        if preset == "boost" and self._has_boost():
            await self._execute_action(self._ACTION_BOOST)
        else:
            await self._execute_action(self._ACTION_ON)
        await self.coordinator.async_request_refresh()
        self._schedule_followup_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the fan off."""
        _ = kwargs
        # In temperature (thermostatic) or time mode the device may immediately re-enable
        # the fan. To make "turn off" behave predictably, exit non-manual modes first.
        mode = (self._fan_config().get("mode") or "").lower()
        if mode and mode != "manual":
            try:
                await self.coordinator.api_client.patch_device_configuration(
                    self.device_id, {"fan": {"mode": "manual"}}
                )
                if getattr(self, "hass", None):
                    friendly = "Thermostatic" if mode == "temperature" else "Time" if mode == "time" else mode
                    pn.async_create(
                        self.hass,
                        (
                            f"Fan was running in {friendly} mode. Home Assistant turned the fan off and "
                            "switched mode to Manual so it won't automatically restart."
                        ),
                        title="Omlet Smart Coop: Fan Mode Changed",
                    )
            except Exception as err:
                _LOGGER.debug("Failed to switch fan mode to manual before turning off: %r", err)
        await self._execute_action(self._ACTION_OFF)
        await self.coordinator.async_request_refresh()
        self._schedule_followup_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        if preset_mode != "boost" or not self._has_boost():
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        await self._execute_action(self._ACTION_BOOST)
        await self.coordinator.async_request_refresh()

    def _has_boost(self) -> bool:
        return self._find_action(self._ACTION_BOOST) is not None

    def _has_on(self) -> bool:
        return self._find_action(self._ACTION_ON) is not None

    def _has_off(self) -> bool:
        return self._find_action(self._ACTION_OFF) is not None

    async def _execute_action(self, action: str) -> None:
        """Execute an action on the fan."""
        action_data = self._find_action(action)
        if not action_data:
            _LOGGER.warning(
                "Action %s unavailable for fan %s", action, self.device_id
            )
            return
        await self.coordinator.api_client.execute_action(action_data["url"])
