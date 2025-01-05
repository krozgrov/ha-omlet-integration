"""Services for the Omlet Smart Coop integration."""

from __future__ import annotations
import logging
from typing import Any
from aiohttp import ClientError

from homeassistant.core import HomeAssistant, ServiceCall
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


async def async_register_services(
    hass: HomeAssistant, coordinator: OmletDataCoordinator
) -> None:
    """Register services for Omlet Smart Coop."""

    async def handle_update_door_schedule(call: ServiceCall) -> None:
        """Handle updating door schedule."""
        try:
            device_id = coordinator.device_id
            if not device_id:
                _LOGGER.error("No device ID available")
                return

            # Get current configuration
            current_config = await coordinator.api_client.get_device_configuration(
                device_id
            )
            door_config = current_config.get("door", {})

            # Update only the changed fields
            door_mode = call.data[ATTR_DOOR_MODE]
            if door_mode not in VALID_DOOR_MODES:
                _LOGGER.error(
                    "Invalid door mode '%s'. Valid modes are: %s",
                    door_mode,
                    ", ".join(VALID_DOOR_MODES),
                )
                return

            door_config["openMode"] = door_mode

            if door_mode == "time":
                if ATTR_OPEN_TIME in call.data:
                    # Validate and format open time
                    open_time = call.data[ATTR_OPEN_TIME]
                    if not isinstance(open_time, str):
                        open_time = open_time.strftime("%H:%M")
                    else:
                        # Remove seconds if present
                        open_time_parts = open_time.split(":")
                        open_time = (
                            f"{open_time_parts[0]:0>2}:{open_time_parts[1]:0>2}"
                            if len(open_time_parts) >= 2
                            else "00:00"
                        )

                    door_config["openTime"] = open_time

                if ATTR_CLOSE_TIME in call.data:
                    # Validate and format close time
                    close_time = call.data[ATTR_CLOSE_TIME]
                    if not isinstance(close_time, str):
                        close_time = close_time.strftime("%H:%M")
                    else:
                        # Remove seconds if present
                        close_time_parts = close_time.split(":")
                        close_time = (
                            f"{close_time_parts[0]:0>2}:{close_time_parts[1]:0>2}"
                            if len(close_time_parts) >= 2
                            else "00:00"
                        )

                    door_config["closeTime"] = close_time

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

            response_data = await coordinator.api_client.patch_device_configuration(
                device_id, {"door": door_config}
            )

            if response_data:
                _LOGGER.debug(
                    "Door schedule update response for device %s: %s",
                    device_id,
                    response_data,
                )

            await coordinator.async_request_refresh()
            _LOGGER.debug("Successfully updated door schedule for device %s", device_id)

        except ClientError as err:
            _LOGGER.error("API error while updating door schedule: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to update door schedule: %s", err)

    async def handle_open_door(call: ServiceCall) -> None:
        """Handle the open door service call."""
        try:
            device_id = coordinator.device_id
            if not device_id:
                _LOGGER.error("No device ID available")
                return

            await coordinator.api_client.execute_action(
                f"device/{device_id}/action/open"
            )
            await coordinator.async_request_refresh()
            _LOGGER.debug("Successfully opened door for device %s", device_id)
        except ClientError as err:
            _LOGGER.error("API error while opening door: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to open door: %s", err)

    async def handle_close_door(call: ServiceCall) -> None:
        """Handle the close door service call."""
        try:
            device_id = coordinator.device_id
            if not device_id:
                _LOGGER.error("No device ID available")
                return

            await coordinator.api_client.execute_action(
                f"device/{device_id}/action/close"
            )
            await coordinator.async_request_refresh()
            _LOGGER.debug("Successfully closed door for device %s", device_id)
        except ClientError as err:
            _LOGGER.error("API error while closing door: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to close door: %s", err)

    async def handle_update_overnight_sleep(call: ServiceCall) -> None:
        """Handle updating overnight sleep schedule."""
        try:
            device_id = coordinator.device_id
            if not device_id:
                _LOGGER.error("No device ID available")
                return

            # Retrieve poll mode, default to power savings
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

            # Extract sleep times and ensure "HH:MM" format
            start_time = call.data.get(ATTR_START_TIME, "23:00")
            end_time = call.data.get(ATTR_END_TIME, "05:00")

            # Validate and format start_time
            if not isinstance(start_time, str):
                start_time = start_time.strftime("%H:%M")
            else:
                # Remove seconds if present
                start_time_parts = start_time.split(":")
                start_time = (
                    f"{start_time_parts[0]:0>2}:{start_time_parts[1]:0>2}"
                    if len(start_time_parts) >= 2
                    else "23:00"
                )

            # Validate and format end_time
            if not isinstance(end_time, str):
                end_time = end_time.strftime("%H:%M")
            else:
                # Remove seconds if present
                end_time_parts = end_time.split(":")
                end_time = (
                    f"{end_time_parts[0]:0>2}:{end_time_parts[1]:0>2}"
                    if len(end_time_parts) >= 2
                    else "05:00"
                )

            _LOGGER.debug("Start Time: %s, End Time: %s", start_time, end_time)

            # Prepare updated configuration with time values as strings
            updated_config = {
                "general": {
                    "updateFrequency": 86400,
                    "overnightSleepEnable": call.data.get(ATTR_ENABLED, True),
                    "overnightSleepStart": start_time,  # Removed extra quotes
                    "overnightSleepEnd": end_time,  # Removed extra quotes
                    "pollFreq": poll_freq,
                    "statusUpdatePeriod": 21600,
                }
            }

            # Log the payload for debugging
            _LOGGER.debug("PATCH payload: %s", updated_config)

            # Patch configuration
            await coordinator.api_client.patch_device_configuration(
                device_id, updated_config
            )

            # Refresh state
            await coordinator.async_request_refresh()

            _LOGGER.info(
                "Successfully updated overnight sleep for device %s with start: %s, end: %s",
                device_id,
                start_time,
                end_time,
            )

        except Exception as err:
            _LOGGER.error("Failed to update overnight sleep: %s", err)

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
