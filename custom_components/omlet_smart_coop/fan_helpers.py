"""Shared helpers for Omlet fan-related entities and services.

This module is intentionally dependency-light to avoid circular imports and to keep
fan-related logic consistent across fan/select/time/number/services platforms.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import time as dt_time
from typing import Any, Iterable

_LOGGER = logging.getLogger(__name__)

# Observed Omlet manual speed values.
FAN_SPEED_MAP: dict[str, int] = {"low": 60, "medium": 80, "high": 100}

# Fan state values that indicate the fan is running (or effectively running).
_FAN_RUNNING_STATES = {"on", "onpending", "boost", "boostpending", "offpending"}


def is_fan_device(device_data: dict[str, Any]) -> bool:
    """True if this device reports fan state/config."""
    state = device_data.get("state", {}) or {}
    config = device_data.get("configuration", {}) or {}
    return bool(state.get("fan") or config.get("fan"))


def iter_fan_devices(coordinator) -> list[tuple[str, dict[str, Any]]]:
    """Return (device_id, device_data) for fan-capable devices."""
    devices = coordinator.data or {}
    out: list[tuple[str, dict[str, Any]]] = []
    for device_id, device_data in devices.items():
        if is_fan_device(device_data):
            out.append((device_id, device_data))
    return out


def fan_config(device_data: dict[str, Any]) -> dict[str, Any]:
    return (device_data.get("configuration", {}) or {}).get("fan", {}) or {}


def fan_state(device_data: dict[str, Any]) -> dict[str, Any]:
    return (device_data.get("state", {}) or {}).get("fan", {}) or {}


def fan_is_running(device_data: dict[str, Any]) -> bool:
    state = (fan_state(device_data).get("state") or "").lower()
    return state in _FAN_RUNNING_STATES


def parse_hhmm(value: Any) -> dt_time | None:
    """Parse 'HH:MM' (or datetime.time) into datetime.time."""
    if not value:
        return None
    if isinstance(value, dt_time):
        return value
    s = str(value)
    if ":" not in s:
        return None
    try:
        hh, mm = s.split(":", 1)
        return dt_time(hour=int(hh), minute=int(mm))
    except Exception:
        return None


def format_hhmm(value: dt_time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}"


async def cycle_fan_off_on(coordinator, device_id: str, *, delay_s: float = 0.5) -> None:
    """Cycle fan off then on using direct action endpoints."""
    await coordinator.api_client.execute_action(f"device/{device_id}/action/off")
    await asyncio.sleep(delay_s)
    await coordinator.api_client.execute_action(f"device/{device_id}/action/on")


def schedule_followup_refresh(hass, coordinator, delays: Iterable[float] = (1.5, 5.0)) -> None:
    """Schedule one or more follow-up refreshes to clear transient pending states."""
    if not hass:
        return

    async def _delayed(delay_s: float) -> None:
        await asyncio.sleep(delay_s)
        await coordinator.async_request_refresh()

    for delay in delays:
        hass.async_create_task(_delayed(float(delay)))


async def patch_fan_config_and_refresh(
    hass,
    coordinator,
    device_id: str,
    fan_patch: dict[str, Any],
    *,
    cycle_if_on: bool = False,
    followup_delays: Iterable[float] = (1.5, 5.0),
) -> None:
    """Patch fan configuration; optionally cycle off/on; refresh + follow-ups."""
    await coordinator.api_client.patch_device_configuration(device_id, {"fan": fan_patch})

    if cycle_if_on:
        device_data = coordinator.data.get(device_id, {}) or {}
        if fan_is_running(device_data):
            try:
                await cycle_fan_off_on(coordinator, device_id)
            except Exception as err:
                _LOGGER.debug("Failed to cycle fan for %s: %r", device_id, err)

    await coordinator.async_request_refresh()
    schedule_followup_refresh(getattr(coordinator, "hass", None) or hass, coordinator, followup_delays)


