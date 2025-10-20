"""Services for the Omlet Smart Coop integration."""

from __future__ import annotations
import logging
from typing import Any
from aiohttp import ClientError
from aiohttp.web import Response

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components import persistent_notification as pn
from homeassistant.components import webhook as hass_webhook
import secrets
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.network import get_url

from .coordinator import OmletDataCoordinator
from .const import (
    DOMAIN,
    SERVICE_OPEN_DOOR,
    SERVICE_CLOSE_DOOR,
    SERVICE_UPDATE_OVERNIGHT_SLEEP,
    SERVICE_UPDATE_DOOR_SCHEDULE,
    SERVICE_SHOW_WEBHOOK_URL,
    CONF_WEBHOOK_ID,
    CONF_ENABLE_WEBHOOKS,
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
        try:
            ent_reg = er.async_get(hass)
            ent_entry = ent_reg.async_get(entity_id)
            if ent_entry and ent_entry.device_id:
                ha_device = device_registry.async_get(ent_entry.device_id)
                if ha_device:
                    serial_number = next(
                        (entry[1] for entry in ha_device.identifiers if entry[0] == DOMAIN),
                        None,
                    )
                    for dev_id, dev_data in coordinator.devices.items():
                        if dev_data.get("deviceSerial") == serial_number:
                            integration_device_ids.append(dev_id)
                            break
        except Exception as e:
            _LOGGER.debug("Failed entity_id resolution via registry: %s", e)

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

    async def handle_show_webhook_url(call: ServiceCall) -> None:
        """Show the webhook URL and status via notification and log."""
        try:
            # Assume single entry for this domain
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                _LOGGER.error("No config entries found for %s", DOMAIN)
                return
            entry = entries[0]
            enabled = entry.options.get(CONF_ENABLE_WEBHOOKS, False)
            webhook_id = entry.data.get(CONF_WEBHOOK_ID)
            if enabled and webhook_id:
                try:
                    url = hass_webhook.async_generate_url(hass, webhook_id)
                except Exception as gen_err:
                    try:
                        base = get_url(hass)
                        url = f"{base}/api/webhook/{webhook_id}"
                    except Exception as url_err:
                        url = f"/api/webhook/{webhook_id}"
                        _LOGGER.debug(
                            "Falling back to path-only webhook URL in service. generate_url=%r, get_url=%r",
                            gen_err,
                            url_err,
                        )
                msg = f"Webhook enabled. URL: {url}"
            elif enabled and not webhook_id:
                msg = "Webhooks enabled but no webhook_id yet. Toggle webhooks off/on in Options to generate one."
            else:
                msg = "Webhooks are disabled in Options. Enable them to generate a webhook URL."

            _LOGGER.info(msg)
            try:
                pn.async_create(hass, msg, title="Omlet Smart Coop Webhook")
            except Exception:  # ignore notification failures
                pass
        except Exception as err:
            _LOGGER.error("Failed to show webhook URL: %s", err)

    async def handle_regenerate_webhook_id(call: ServiceCall) -> None:
        """Regenerate the webhook ID, re-register, and notify the new URL."""
        try:
            entries = hass.config_entries.async_entries(DOMAIN)
            if not entries:
                _LOGGER.error("No config entries found for %s", DOMAIN)
                return
            entry = entries[0]

            enabled = entry.options.get(CONF_ENABLE_WEBHOOKS, False)
            old_id = entry.data.get(CONF_WEBHOOK_ID)

            # Unregister old id if present
            if old_id:
                try:
                    hass_webhook.async_unregister(hass, old_id)
                except Exception:
                    pass

            # Generate a shorter, random hex ID (32 chars)
            new_id = secrets.token_hex(16)
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_WEBHOOK_ID: new_id}
            )

            url = f"/api/webhook/{new_id}"
            if enabled:
                # Register new webhook handler (simple refresh-only handler)
                async def _handle_webhook(hass, webhook_id_recv, request):
                    try:
                        payload = None
                        try:
                            payload = await request.json()
                        except Exception:
                            pass
                        expected = entry.options.get("webhook_token")
                        provided = (
                            request.headers.get("X-Omlet-Token")
                            or (payload or {}).get("token")
                            or (payload or {}).get("secret")
                            or request.query.get("token")
                        )
                        if expected and (not provided or provided != expected):
                            return Response(status=401, text="invalid token")
                        await hass.data[DOMAIN][entry.entry_id]["coordinator"].async_request_refresh()
                        return Response(text="ok")
                    except Exception:
                        return Response(status=500, text="error")

                hass_webhook.async_register(hass, DOMAIN, "Omlet Smart Coop", new_id, _handle_webhook)
                try:
                    url = hass_webhook.async_generate_url(hass, new_id)
                except Exception as gen_err:
                    try:
                        base = get_url(hass)
                        url = f"{base}/api/webhook/{new_id}"
                    except Exception:
                        url = f"/api/webhook/{new_id}"

            msg = (
                f"Webhook ID regenerated. New URL: {url}. Update Omlet Developer Portal."
                if enabled
                else f"Webhook ID regenerated (webhooks disabled). New path: {url}. Enable webhooks to register."
            )
            _LOGGER.info(msg)
            try:
                pn.async_create(hass, msg, title="Omlet Smart Coop Webhook")
            except Exception:
                pass
        except Exception as err:
            _LOGGER.error("Failed to regenerate webhook ID: %s", err)

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
    hass.services.async_register(DOMAIN, SERVICE_SHOW_WEBHOOK_URL, handle_show_webhook_url)
    hass.services.async_register(DOMAIN, "regenerate_webhook_id", handle_regenerate_webhook_id)


def async_remove_services(hass: HomeAssistant) -> None:
    """Remove services for Omlet Smart Coop."""
    for service in [
        SERVICE_OPEN_DOOR,
        SERVICE_CLOSE_DOOR,
        SERVICE_UPDATE_OVERNIGHT_SLEEP,
        SERVICE_UPDATE_DOOR_SCHEDULE,
        SERVICE_SHOW_WEBHOOK_URL,
        "regenerate_webhook_id",
    ]:
        hass.services.async_remove(DOMAIN, service)
