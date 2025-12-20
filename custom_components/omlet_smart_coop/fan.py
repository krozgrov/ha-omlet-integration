import logging
import asyncio
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.components import persistent_notification as pn
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import OmletEntity
from .const import CONF_ENABLE_WEBHOOKS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up fan platforms from config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    _LOGGER.debug("Setting up fans for devices: %s", coordinator.data)

    fans = []
    for device_id, device_data in coordinator.data.items():
        # Any device that reports fan state can expose a fan entity regardless of deviceType label
        fan_state = device_data.get("state", {}).get("fan")
        fan_cfg = device_data.get("configuration", {}).get("fan")
        if not fan_state and not fan_cfg:
            continue
        fans.append(OmletFan(coordinator, device_id, device_data["name"]))

    async_add_entities(fans)


class OmletFan(OmletEntity, FanEntity):
    """Representation of an Omlet smart coop fan."""

    _ACTION_ON = "on"
    _ACTION_OFF = "off"
    _ACTION_BOOST = "boost"
    def __init__(self, coordinator, device_id: str, device_name: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_translation_key = "fan"
        self._attr_unique_id = f"{device_id}_fan"
        self._attr_has_entity_name = True
        # Always expose the fan as a basic on/off toggle in HA. Omlet's `actions`
        # list can be omitted temporarily, but core fan services should still work.
        self._attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        # Optimistic UI state for webhook-less installs (short-lived).
        self._optimistic_is_on: bool | None = None
        self._optimistic_until: float = 0.0

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
        return bool(self._fan_state() or self._fan_config())

    @property
    def is_on(self) -> bool:
        """Return whether the fan is running."""
        # If we've just issued a command, reflect it immediately in the UI while
        # we wait for Omlet API to converge (polling-only installs).
        if self._optimistic_is_on is not None and dt_util.utcnow().timestamp() < self._optimistic_until:
            return self._optimistic_is_on
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

        # Longer follow-ups when webhooks are disabled (polling-only installs).
        enable_webhooks = False
        try:
            enable_webhooks = bool(self.coordinator.config_entry.options.get(CONF_ENABLE_WEBHOOKS, False))
        except Exception:
            enable_webhooks = False

        delays = (1.5, 5.0) if enable_webhooks else (1.5, 5.0, 15.0, 30.0)
        for delay in delays:
            self.hass.async_create_task(_delayed(delay))

    def _set_optimistic(self, is_on: bool, *, seconds: float = 20.0) -> None:
        self._optimistic_is_on = bool(is_on)
        self._optimistic_until = dt_util.utcnow().timestamp() + float(seconds)
        try:
            self.async_write_ha_state()
        except Exception:
            pass

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
        #
        # Some Omlet API payloads omit the `actions` list (or it can be temporarily empty),
        # which would incorrectly disable core fan services in HA. The fan entity is
        # fundamentally a toggle, so always advertise TURN_ON/TURN_OFF.
        features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._has_boost():
            features |= FanEntityFeature.PRESET_MODE
        return features

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
        preset = preset_mode or kwargs.get("preset_mode")
        # Speed is configured via config entities/services (manualSpeed/timeSpeed/tempSpeed),
        # so the fan entity itself is intentionally toggle-only. Ignore percentage.
        if preset == "boost" and self._has_boost():
            await self._execute_action(self._ACTION_BOOST)
        else:
            # If the device is in temperature (thermostatic) or time mode, "turn on"
            # can behave unexpectedly (mode may immediately take over). For predictable
            # manual control from the HA fan entity, switch to manual first.
            mode = (self._fan_config().get("mode") or "").lower()
            if mode in {"temperature", "time"} and getattr(self, "hass", None):
                friendly = "Thermostatic" if mode == "temperature" else "Time"
                pn.async_create(
                    self.hass,
                    (
                        f"Fan is configured for {friendly} mode. Home Assistant will switch to "
                        "Manual for direct control when turning the fan on."
                    ),
                    title="Omlet Smart Coop: Fan Mode Changed",
                )
            if mode and mode != "manual":
                try:
                    await self.coordinator.api_client.patch_device_configuration(
                        self.device_id, {"fan": {"mode": "manual"}}
                    )
                    # Give the device a brief moment to apply the mode switch before actioning "on".
                    await asyncio.sleep(0.5)
                except Exception as err:
                    _LOGGER.debug("Failed to switch fan mode to manual before turning on: %r", err)
            await self._execute_action(self._ACTION_ON)
        self._set_optimistic(True)
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
        self._set_optimistic(False)
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
                "Action %s missing in device actions for fan %s; falling back to direct action endpoint",
                action,
                self.device_id,
            )
            await self.coordinator.api_client.execute_action(
                f"device/{self.device_id}/action/{action}"
            )
            return
        await self.coordinator.api_client.execute_action(action_data["url"])
