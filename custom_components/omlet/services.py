"""Services for the Omlet Smart Coop integration."""

from __future__ import annotations
import logging
from typing import Any
from aiohttp import ClientError

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .coordinator import OmletDataCoordinator
from .const import (
    DOMAIN,
    SERVICE_OPEN_DOOR,
    SERVICE_CLOSE_DOOR,
    SERVICE_UPDATE_OVERNIGHT_SLEEP,
    SERVICE_UPDATE_DOOR_SCHEDULE,
    ATTR_ENABLED,
    ATTR_START_TIME,
    ATTR_END_TIME,
    ATTR_OPEN_TIME,
    ATTR_CLOSE_TIME,
    VALID_DOOR_MODES,
    ATTR_DOOR_MODE,
    ATTR_POLL_MODE,
    POLL_MODE_RESPONSIVE,
    POLL_MODE_POWER_SAVINGS,
    POLL_FREQ_RESPONSIVE,
    POLL_FREQ_POWER_SAVINGS,
)

_LOGGER = logging.getLogger(__name__)


async def get_integration_device_ids(
    hass: HomeAssistant, coordinator: OmletDataCoordinator, call_data: dict
) -> list[str]:  # Changed return type
    """Map Home Assistant device identifiers to integration device IDs."""
    device_ids = call_data.get("device_id", [])  # Changed to default to empty list
    entity_id = call_data.get("entity_id")
    device_name = call_data.get("name")

    _LOGGER.debug("Full service call data: %s", call_data)

    # Ensure device_ids is a list
    if not isinstance(device_ids, list):
        device_ids = [device_ids] if device_ids else []

    _LOGGER.debug("Processing device IDs: %s", device_ids)

    # Map Home Assistant device_ids to integration-specific device_ids
    integration_device_ids = []  # Changed to list
    device_registry = async_get_device_registry(hass)

    # Process all device IDs
    for device_id in device_ids:
        ha_device = device_registry.async_get(device_id)
        if ha_device:
            serial_number = next(
                (entry[1] for entry in ha_device.identifiers if entry[0] == DOMAIN),
                None,
            )
            _LOGGER.debug("Found device serial number: %s", serial_number)

            # Look up the device ID using the serial number
            for dev_id, dev_data in coordinator.devices.items():
                if dev_data.get("deviceSerial") == serial_number:
                    integration_device_ids.append(dev_id)  # Changed to append
                    _LOGGER.debug(
                        "Mapped serial %s to device ID: %s",
                        serial_number,
                        dev_id,
                    )
                    break

    # If no IDs found yet, try entity_id
    if not integration_device_ids and entity_id:
        entity = hass.states.get(entity_id)
        if entity and entity.attributes.get("device_id"):
            device_id = entity.attributes["device_id"]
            if device_id in coordinator.devices:
                integration_device_ids.append(device_id)

    # If still no IDs, try device name
    if not integration_device_ids and device_name:
        for dev_id, dev_data in coordinator.devices.items():
            if dev_data.get("name") == device_name:
                integration_device_ids.append(dev_id)
                break

    # Validate the resolved device_ids
    if not integration_device_ids:
        _LOGGER.error("No valid device IDs found. Service call data: %s", call_data)
        return []

    # Verify all devices exist in the coordinator
    valid_ids = []
    for device_id in integration_device_ids:
        if device_id in coordinator.devices:
            valid_ids.append(device_id)
        else:
            _LOGGER.error(
                "Device ID %s not found in coordinator data. Available devices: %s",
                device_id,
                list(coordinator.devices.keys()),
            )

    return valid_ids


async def async_register_services(
    hass: HomeAssistant, coordinator: OmletDataCoordinator
) -> None:
    """Register services for Omlet Smart Coop."""

    async def handle_open_door(call: ServiceCall) -> None:
        """Handle the open door service call."""
        try:
            integration_device_ids = await get_integration_device_ids(
                hass, coordinator, call.data
            )
            if not integration_device_ids:
                return

            for device_id in integration_device_ids:
                try:
                    await coordinator.api_client.execute_action(
                        f"device/{device_id}/action/open"
                    )
                    _LOGGER.info(
                        "Successfully opened door for device: %s",
                        coordinator.devices[device_id]["name"],
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to open door for device %s: %s", device_id, err
                    )

            await coordinator.async_request_refresh()

        except ClientError as err:
            _LOGGER.error("API error while opening door: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to process open door command: %s", err)

    async def handle_close_door(call: ServiceCall) -> None:
        """Handle the close door service call."""
        try:
            integration_device_ids = await get_integration_device_ids(
                hass, coordinator, call.data
            )
            if not integration_device_ids:
                return

            for device_id in integration_device_ids:
                try:
                    await coordinator.api_client.execute_action(
                        f"device/{device_id}/action/close"
                    )
                    _LOGGER.info(
                        "Successfully closed door for device: %s",
                        coordinator.devices[device_id]["name"],
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to close door for device %s: %s", device_id, err
                    )

            await coordinator.async_request_refresh()

        except ClientError as err:
            _LOGGER.error("API error while closing door: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to process close door command: %s", err)

    async def handle_update_overnight_sleep(call: ServiceCall) -> None:
        """Handle updating overnight sleep schedule."""
        try:
            integration_device_ids = await get_integration_device_ids(
                hass, coordinator, call.data
            )
            if not integration_device_ids:
                return

            # Get configuration parameters
            poll_mode = (
                call.data.get(ATTR_POLL_MODE, POLL_MODE_POWER_SAVINGS).strip().lower()
            )
            if poll_mode == POLL_MODE_RESPONSIVE:
                poll_freq = POLL_FREQ_RESPONSIVE
            elif poll_mode == POLL_MODE_POWER_SAVINGS:
                poll_freq = POLL_FREQ_POWER_SAVINGS
            else:
                poll_mode = POLL_MODE_POWER_SAVINGS
                poll_freq = POLL_FREQ_POWER_SAVINGS
                _LOGGER.warning(
                    "Invalid poll mode provided: %s. Defaulting to power savings.",
                    poll_mode,
                )

            # Process time settings
            start_time = call.data.get(ATTR_START_TIME, "23:00")
            end_time = call.data.get(ATTR_END_TIME, "05:00")

            if not isinstance(start_time, str):
                start_time = start_time.strftime("%H:%M")
            else:
                start_time_parts = start_time.split(":")
                start_time = (
                    f"{start_time_parts[0]:0>2}:{start_time_parts[1]:0>2}"
                    if len(start_time_parts) >= 2
                    else "23:00"
                )

            if not isinstance(end_time, str):
                end_time = end_time.strftime("%H:%M")
            else:
                end_time_parts = end_time.split(":")
                end_time = (
                    f"{end_time_parts[0]:0>2}:{end_time_parts[1]:0>2}"
                    if len(end_time_parts) >= 2
                    else "05:00"
                )

            updated_config = {
                "general": {
                    "updateFrequency": 86400,
                    "overnightSleepEnable": call.data.get(ATTR_ENABLED, True),
                    "overnightSleepStart": start_time,
                    "overnightSleepEnd": end_time,
                    "pollFreq": poll_freq,
                    "statusUpdatePeriod": 21600,
                }
            }

            for device_id in integration_device_ids:
                try:
                    await coordinator.api_client.patch_device_configuration(
                        device_id, updated_config
                    )
                    _LOGGER.info(
                        "Successfully updated overnight sleep for device %s with start: %s, end: %s",
                        coordinator.devices[device_id]["name"],
                        start_time,
                        end_time,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to update overnight sleep for device %s: %s",
                        device_id,
                        err,
                    )

            await coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error("Failed to update overnight sleep: %s", err)

    async def handle_update_door_schedule(call: ServiceCall) -> None:
        """Handle updating door schedule."""
        try:
            integration_device_ids = await get_integration_device_ids(
                hass, coordinator, call.data
            )
            if not integration_device_ids:
                return

            # Validate door mode
            door_mode = call.data[ATTR_DOOR_MODE]
            if door_mode not in VALID_DOOR_MODES:
                _LOGGER.error(
                    "Invalid door mode '%s'. Valid modes are: %s",
                    door_mode,
                    ", ".join(VALID_DOOR_MODES),
                )
                return

            for device_id in integration_device_ids:
                try:
                    # Get current configuration for this device
                    current_config = (
                        await coordinator.api_client.get_device_configuration(device_id)
                    )
                    door_config = current_config.get("door", {})

                    # Apply door mode settings
                    door_config["openMode"] = door_mode
                    door_config["closeMode"] = door_mode

                    # Handle time settings if mode is "time"
                    if door_mode == "time":
                        if ATTR_OPEN_TIME in call.data:
                            open_time = call.data[ATTR_OPEN_TIME]
                            if not isinstance(open_time, str):
                                open_time = open_time.strftime("%H:%M")
                            else:
                                open_time_parts = open_time.split(":")
                                open_time = (
                                    f"{open_time_parts[0]:0>2}:{open_time_parts[1]:0>2}"
                                    if len(open_time_parts) >= 2
                                    else "00:00"
                                )
                            door_config["openTime"] = open_time

                        if ATTR_CLOSE_TIME in call.data:
                            close_time = call.data[ATTR_CLOSE_TIME]
                            if not isinstance(close_time, str):
                                close_time = close_time.strftime("%H:%M")
                            else:
                                close_time_parts = close_time.split(":")
                                close_time = (
                                    f"{close_time_parts[0]:0>2}:{close_time_parts[1]:0>2}"
                                    if len(close_time_parts) >= 2
                                    else "00:00"
                                )
                            door_config["closeTime"] = close_time

                    # Handle light settings if mode is "light"
                    elif door_mode == "light":
                        field_mapping = {
                            "open_light_level": "openLightLevel",
                            "close_light_level": "closeLightLevel",
                            "open_delay": "openDelay",
                            "close_delay": "closeDelay",
                        }

                        for service_field, api_field in field_mapping.items():
                            if service_field in call.data:
                                door_config[api_field] = call.data[service_field]

                    # Update configuration for this device
                    response_data = (
                        await coordinator.api_client.patch_device_configuration(
                            device_id, {"door": door_config}
                        )
                    )

                    if response_data:
                        _LOGGER.debug(
                            "Door schedule update response for device %s: %s",
                            coordinator.devices[device_id]["name"],
                            response_data,
                        )

                    _LOGGER.info(
                        "Successfully updated door schedule for device: %s",
                        coordinator.devices[device_id]["name"],
                    )

                except Exception as err:
                    _LOGGER.error(
                        "Failed to update door schedule for device %s: %s",
                        device_id,
                        err,
                    )

            await coordinator.async_request_refresh()

        except ClientError as err:
            _LOGGER.error("API error while updating door schedule: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to update door schedule: %s", err)

    # Register all services
    hass.services.async_register(DOMAIN, SERVICE_OPEN_DOOR, handle_open_door)
    hass.services.async_register(DOMAIN, SERVICE_CLOSE_DOOR, handle_close_door)
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_OVERNIGHT_SLEEP, handle_update_overnight_sleep
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_DOOR_SCHEDULE, handle_update_door_schedule
    )


def async_remove_services(hass: HomeAssistant) -> None:
    """Remove services for Omlet Smart Coop."""
    for service in [
        SERVICE_OPEN_DOOR,
        SERVICE_CLOSE_DOOR,
        SERVICE_UPDATE_OVERNIGHT_SLEEP,
        SERVICE_UPDATE_DOOR_SCHEDULE,
    ]:
        hass.services.async_remove(DOMAIN, service)
