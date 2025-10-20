from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .coordinator import OmletDataCoordinator
from .services import async_register_services, async_remove_services
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_POLLING_INTERVAL,    
    CONF_DEFAULT_POLLING_INTERVAL,
    CONF_ENABLE_WEBHOOKS,
    CONF_WEBHOOK_ID,
    CONF_DISABLE_POLLING,
    FIXED_WEBHOOK_ID,
)
from homeassistant.components import webhook as hass_webhook
from homeassistant.components import persistent_notification as pn
from aiohttp.web import Response

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Omlet Smart Coop integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omlet Smart Coop from a config entry."""
    _LOGGER.info(
        "Setting up Omlet Smart Coop integration for entry: %s", entry.entry_id
    )

    # Initialize the data coordinator
    try:
        coordinator = OmletDataCoordinator(
            hass,
            entry.data["api_key"],
            entry,
        )
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.error("Failed to initialize Omlet Smart Coop: %s", ex)
        raise ConfigEntryNotReady from ex

    # Store the coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Optionally register webhook support
    try:
        if entry.options.get(CONF_ENABLE_WEBHOOKS, False):
            # Always use fixed webhook id for this integration
            old_id = entry.data.get(CONF_WEBHOOK_ID)
            webhook_id = FIXED_WEBHOOK_ID
            if old_id and old_id != webhook_id:
                try:
                    hass_webhook.async_unregister(hass, old_id)
                except Exception:
                    pass
            # Persist fixed id for clarity
            if old_id != webhook_id:
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_WEBHOOK_ID: webhook_id}
                )

            async def _handle_webhook(hass, webhook_id_recv, request):
                """Handle incoming Omlet webhook events."""
                try:
                    payload = None
                    try:
                        payload = await request.json()
                    except Exception:
                        _LOGGER.debug("Webhook received non-JSON payload")

                    # Optional token validation
                    expected = entry.options.get("webhook_token") or entry.options.get("token") or entry.options.get("secret") or entry.options.get("WEBHOOK_TOKEN")
                    provided = (
                        request.headers.get("X-Omlet-Token")
                        or (payload or {}).get("token")
                        or (payload or {}).get("secret")
                        or request.query.get("token")
                    )
                    if expected:
                        if not provided or provided != expected:
                            _LOGGER.warning("Rejected webhook: invalid token")
                            return Response(status=401, text="invalid token")

                    _LOGGER.debug("Received Omlet webhook: %s", payload)
                    # Refresh data to sync state post-event
                    await coordinator.async_request_refresh()
                    return Response(status=200, text="ok")
                except Exception as ex:
                    _LOGGER.error("Error handling webhook: %s", ex)
                    return Response(status=500, text="error")

            # Register webhook in HA
            # Ensure clean registration
            try:
                hass_webhook.async_unregister(hass, webhook_id)
            except Exception:
                pass
            hass_webhook.async_register(hass, DOMAIN, "Omlet Smart Coop", webhook_id, _handle_webhook)

            webhook_url = hass_webhook.async_generate_url(hass, webhook_id)
            _LOGGER.info(
                "Omlet Smart Coop webhook enabled. Configure at Omlet portal to POST to: %s",
                webhook_url,
            )
            try:
                pn.async_create(
                    hass,
                    f"Webhook enabled. Use this URL in Omlet Developer Portal → Manage Webhooks: {webhook_url}",
                    title="Omlet Smart Coop Webhook",
                )
            except Exception:
                pass
    except Exception as ex:
        _LOGGER.exception("Failed to set up webhook: %r", ex)

    # Register services
    try:
        await async_register_services(hass, coordinator)
        _LOGGER.debug("Successfully registered Omlet Smart Coop services")
    except Exception as ex:
        _LOGGER.error("Failed to register services: %s", ex)
        return False

    # Forward the entry to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add an update listener for handling options changes
    entry.add_update_listener(update_listener)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Omlet Smart Coop integration for entry: %s", entry.entry_id)

    # Unload platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up coordinator
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        coordinator = entry_data.get("coordinator")
        if coordinator:
            await coordinator.async_shutdown()

        # Remove services last
        async_remove_services(hass)

        # Unregister webhook if present
        try:
            webhook_id = entry.data.get(CONF_WEBHOOK_ID)
            if webhook_id:
                hass_webhook.async_unregister(hass, webhook_id)
        except Exception as ex:
            _LOGGER.warning("Failed to unregister webhook: %s", ex)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options updates."""
    _LOGGER.info("Updating options for entry: %s", entry.entry_id)

    # Retrieve the coordinator
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]

    # Extract the new polling interval from options
    disable_polling = entry.options.get(CONF_DISABLE_POLLING, False)
    new_interval = None if disable_polling else entry.options.get(
        CONF_POLLING_INTERVAL, CONF_DEFAULT_POLLING_INTERVAL
    )

    # Update the coordinator with the new polling interval
    try:
        await coordinator.update_polling_interval(new_interval)
        _LOGGER.info(
            "Polling %s",
            "disabled (webhooks only)" if disable_polling else f"{new_interval} seconds",
        )
    except ValueError as ex:
        _LOGGER.error("Failed to update polling interval: %s", ex)

    # Trigger a refresh of data after options update
    await coordinator.async_request_refresh()

    # Handle enabling/disabling webhooks dynamically (fixed id)
    try:
        enabled = entry.options.get(CONF_ENABLE_WEBHOOKS, False)
        current_id = FIXED_WEBHOOK_ID

        if enabled:
            # Persist fixed id for clarity
            if entry.data.get(CONF_WEBHOOK_ID) != current_id:
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_WEBHOOK_ID: current_id}
                )

            # Unregister then register (idempotent)
            try:
                hass_webhook.async_unregister(hass, current_id)
            except Exception:
                pass

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
                    await coordinator.async_request_refresh()
                    return Response(text="ok")
                except Exception:
                    return Response(status=500, text="error")

            hass_webhook.async_register(hass, DOMAIN, "Omlet Smart Coop", current_id, _handle_webhook)
            webhook_url = hass_webhook.async_generate_url(hass, current_id)
            _LOGGER.info("Webhook enabled (enabled=%s, id=%s). URL: %s", enabled, current_id, webhook_url)
            try:
                pn.async_create(
                    hass,
                    f"Webhook enabled. Use this URL in Omlet Developer Portal → Manage Webhooks: {webhook_url}",
                    title="Omlet Smart Coop Webhook",
                )
            except Exception:
                pass
        else:
            # Disabled: unregister fixed id
            try:
                hass_webhook.async_unregister(hass, current_id)
                _LOGGER.info("Webhook disabled and unregistered")
            except Exception:
                pass
    except Exception as ex:
        _LOGGER.exception("Webhook option update handling failed: %r", ex)
