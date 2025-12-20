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
    CONF_WEBHOOK_NOTIFIED_ID,
)
from homeassistant.components import webhook as hass_webhook
from homeassistant.components import persistent_notification as pn
from aiohttp.web import Response
import secrets
from homeassistant.helpers.network import get_url
import time
from homeassistant.helpers import entity_registry as er
from .const import CONF_WEBHOOK_TIP_SHOWN
from .webhook_helpers import get_expected_webhook_token, get_provided_webhook_token

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Omlet Smart Coop integration."""
    hass.data.setdefault(DOMAIN, {})
    # Register services at startup so they remain available even if an entry reload fails.
    await async_register_services(hass, None)
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

    # Ensure services are registered even if HA hasn't been restarted (dev upgrades).
    # Registration is idempotent in services.py.
    try:
        await async_register_services(hass, None)
    except Exception as ex:
        _LOGGER.warning("Service registration during setup_entry failed: %r", ex)

    # One-time setup tip: guide users to enable webhooks in Options
    try:
        if not entry.options.get(CONF_ENABLE_WEBHOOKS, False) and not entry.data.get(CONF_WEBHOOK_TIP_SHOWN):
            pn.async_create(
                hass,
                (
                    "You can enable webhooks in Options to receive real-time updates. "
                    "When enabled, a full webhook URL will be shown and can be added in the Omlet Developer Portal."
                ),
                title="Omlet Smart Coop: Enable Webhooks (Optional)",
            )
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_WEBHOOK_TIP_SHOWN: True}
            )
    except Exception:
        pass

    # One-time entity registry migration: stable unique_id for light/cover (v1)
    try:
        if not entry.data.get("unique_id_migrated_v1"):
            ent_reg = er.async_get(hass)
            reg_entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
            for reg_entry in reg_entries:
                if reg_entry.platform != DOMAIN:
                    continue
                if reg_entry.domain not in ("light", "cover"):
                    continue
                uid = reg_entry.unique_id or ""
                for suffix in ("_light", "_door"):
                    if uid.endswith(suffix):
                        base = uid[: -len(suffix)]
                        # Old pattern: <device_id>_<sanitized_name><suffix>
                        if "_" in base:
                            new_base = base.rsplit("_", 1)[0]
                            new_uid = f"{new_base}{suffix}"
                            if new_uid != uid:
                                # Skip if target unique_id already exists
                                existing = ent_reg.async_get_entity_id(
                                    reg_entry.domain, DOMAIN, new_uid
                                )
                                if existing is None:
                                    ent_reg.async_update_entity(
                                        reg_entry.entity_id, new_unique_id=new_uid
                                    )
                                    _LOGGER.info(
                                        "Migrated unique_id for %s from %s to %s",
                                        reg_entry.entity_id,
                                        uid,
                                        new_uid,
                                    )
                                else:
                                    _LOGGER.warning(
                                        "Skip unique_id migration for %s; new id %s already bound to %s",
                                        reg_entry.entity_id,
                                        new_uid,
                                        existing,
                                    )
                        break
            # Mark migration complete
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "unique_id_migrated_v1": True}
            )
    except Exception as ex:
        _LOGGER.warning("Unique_id migration v1 skipped due to error: %r", ex)

    # Follow-up migration (v2): ensure we strip any name segments fully,
    # leaving only {deviceId}_light / {deviceId}_door even when names include underscores
    try:
        if not entry.data.get("unique_id_migrated_v2"):
            ent_reg = er.async_get(hass)
            reg_entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
            for reg_entry in reg_entries:
                if reg_entry.platform != DOMAIN or reg_entry.domain not in ("light", "cover"):
                    continue
                uid = reg_entry.unique_id or ""
                for suffix in ("_light", "_door"):
                    if not uid.endswith(suffix):
                        continue
                    base = uid[: -len(suffix)]
                    if "_" not in base:
                        # Already in the {deviceId}{suffix} form
                        continue
                    # Take deviceId as the prefix up to the first underscore
                    device_id_prefix = base.split("_", 1)[0]
                    new_uid = f"{device_id_prefix}{suffix}"
                    if new_uid == uid:
                        continue
                    existing = ent_reg.async_get_entity_id(reg_entry.domain, DOMAIN, new_uid)
                    if existing is None:
                        ent_reg.async_update_entity(reg_entry.entity_id, new_unique_id=new_uid)
                        _LOGGER.info(
                            "Migrated unique_id v2 for %s from %s to %s",
                            reg_entry.entity_id,
                            uid,
                            new_uid,
                        )
                    else:
                        _LOGGER.warning(
                            "Skip unique_id v2 migration for %s; new id %s already bound to %s",
                            reg_entry.entity_id,
                            new_uid,
                            existing,
                        )
                    break
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "unique_id_migrated_v2": True}
            )
    except Exception as ex:
        _LOGGER.warning("Unique_id migration v2 skipped due to error: %r", ex)

    # Optionally register webhook support
    try:
        if entry.options.get(CONF_ENABLE_WEBHOOKS, False):
            # Use a stable, random webhook id per entry
            webhook_id = entry.data.get(CONF_WEBHOOK_ID)
            # Migrate away from any prior fixed id (== DOMAIN)
            if webhook_id == DOMAIN:
                try:
                    hass_webhook.async_unregister(hass, DOMAIN)
                except Exception:
                    pass
                webhook_id = None
            if not webhook_id:
                # Generate a shorter, random hex ID (32 chars; 128-bit entropy)
                webhook_id = secrets.token_hex(16)
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_WEBHOOK_ID: webhook_id}
                )

            async def _handle_webhook(hass, webhook_id_recv, request):
                """Handle incoming Omlet webhook events."""
                payload = None
                try:
                    # Debounce rapid events
                    ts = time.monotonic()
                    entry_bucket = hass.data[DOMAIN].setdefault(entry.entry_id, {})
                    last = entry_bucket.get("_last_webhook_ts", 0.0)
                    if ts - last < 1.0:
                        return Response(status=200, text="ok")
                    entry_bucket["_last_webhook_ts"] = ts
                    try:
                        payload = await request.json()
                    except Exception:
                        _LOGGER.debug("Webhook received non-JSON payload")

                    # Optional token validation
                    expected = get_expected_webhook_token(entry)
                    provided = get_provided_webhook_token(request, payload)
                    if expected:
                        if not provided or provided != expected:
                            _LOGGER.warning("Rejected webhook: invalid token")
                            return Response(status=401, text="invalid token")

                    # Redacted logging: never log tokens; summarize event
                    try:
                        evt = (payload or {}).get("payload") or {}
                        _LOGGER.debug(
                            "Webhook event: device=%s param=%s old=%s new=%s",
                            evt.get("deviceId"),
                            evt.get("parameterName"),
                            evt.get("oldValue"),
                            evt.get("newValue"),
                        )
                    except Exception:
                        _LOGGER.debug("Webhook event received (details redacted)")
                except Exception as ex:
                    _LOGGER.error("Error handling webhook: %s", ex)
                    return Response(status=200, text="ok")
                # Refresh data to sync state post-event (async so webhook returns fast).
                try:
                    hass.async_create_task(coordinator.async_request_refresh())
                except Exception as ex:
                    _LOGGER.debug("Failed to schedule webhook refresh: %r", ex)
                return Response(status=200, text="ok")

            # Register webhook in HA
            # Ensure clean registration
            try:
                hass_webhook.async_unregister(hass, webhook_id)
            except Exception:
                pass
            hass_webhook.async_register(hass, DOMAIN, "Omlet Smart Coop", webhook_id, _handle_webhook)

            try:
                webhook_url = hass_webhook.async_generate_url(hass, webhook_id)
            except Exception as gen_err:
                # Fallback: try HA base URL builder, then path-only
                try:
                    base = get_url(hass)
                    webhook_url = f"{base}/api/webhook/{webhook_id}"
                except Exception as url_err:
                    webhook_url = f"/api/webhook/{webhook_id}"
                    _LOGGER.debug(
                        "Falling back to path-only webhook URL (setup). generate_url=%r, get_url=%r",
                        gen_err,
                        url_err,
                    )
            _LOGGER.info(
                "Omlet Smart Coop webhook enabled. Configure at Omlet portal to POST to: %s",
                webhook_url,
            )
            # Notify only once per webhook_id unless rotated
            if entry.data.get(CONF_WEBHOOK_NOTIFIED_ID) != webhook_id:
                try:
                    pn.async_create(
                        hass,
                        f"Webhook enabled. Use this URL in Omlet Developer Portal → Manage Webhooks: {webhook_url}",
                        title="Omlet Smart Coop Webhook",
                    )
                except Exception:
                    pass
                # Persist that we've notified for this id
                hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_WEBHOOK_ID: webhook_id, CONF_WEBHOOK_NOTIFIED_ID: webhook_id},
                )
    except Exception as ex:
        _LOGGER.exception("Failed to set up webhook: %r", ex)

    # Forward the entry to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add an update listener for handling options changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

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

    # Handle enabling/disabling webhooks dynamically (random id persisted in entry)
    try:
        enabled = entry.options.get(CONF_ENABLE_WEBHOOKS, False)
        current_id = entry.data.get(CONF_WEBHOOK_ID)

        if enabled:
            # Ensure we have a random id; migrate from fixed id if needed
            if not current_id or current_id == DOMAIN:
                try:
                    hass_webhook.async_unregister(hass, DOMAIN)
                except Exception:
                    pass
                # Generate a shorter, random hex ID (32 chars)
                current_id = secrets.token_hex(16)
                hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_WEBHOOK_ID: current_id}
                )

            # Unregister then register (idempotent)
            try:
                hass_webhook.async_unregister(hass, current_id)
            except Exception:
                pass

            async def _handle_webhook(hass, webhook_id_recv, request):
                payload = None
                try:
                    ts = time.monotonic()
                    entry_bucket = hass.data[DOMAIN].setdefault(entry.entry_id, {})
                    last = entry_bucket.get("_last_webhook_ts", 0.0)
                    if ts - last < 1.0:
                        return Response(status=200, text="ok")
                    entry_bucket["_last_webhook_ts"] = ts
                    try:
                        payload = await request.json()
                    except Exception:
                        pass
                    expected = get_expected_webhook_token(entry)
                    provided = get_provided_webhook_token(request, payload)
                    if expected and (not provided or provided != expected):
                        _LOGGER.warning("Rejected webhook: invalid token")
                        return Response(status=401, text="invalid token")
                    # Redacted logging: summarize event without secrets
                    try:
                        evt = (payload or {}).get("payload") or {}
                        _LOGGER.debug(
                            "Webhook event: device=%s param=%s old=%s new=%s",
                            evt.get("deviceId"),
                            evt.get("parameterName"),
                            evt.get("oldValue"),
                            evt.get("newValue"),
                        )
                    except Exception:
                        pass
                except Exception:
                    return Response(status=200, text="ok")
                try:
                    hass.async_create_task(coordinator.async_request_refresh())
                except Exception as ex:
                    _LOGGER.debug("Failed to schedule webhook refresh: %r", ex)
                return Response(text="ok")

            hass_webhook.async_register(hass, DOMAIN, "Omlet Smart Coop", current_id, _handle_webhook)
            try:
                webhook_url = hass_webhook.async_generate_url(hass, current_id)
            except Exception as gen_err:
                try:
                    base = get_url(hass)
                    webhook_url = f"{base}/api/webhook/{current_id}"
                except Exception as url_err:
                    webhook_url = f"/api/webhook/{current_id}"
                    _LOGGER.debug(
                        "Falling back to path-only webhook URL (toggle). generate_url=%r, get_url=%r",
                        gen_err,
                        url_err,
                    )
            _LOGGER.info("Webhook enabled (enabled=%s, id=%s). URL: %s", enabled, current_id, webhook_url)
            # Notify only once per webhook_id unless rotated
            if entry.data.get(CONF_WEBHOOK_NOTIFIED_ID) != current_id:
                try:
                    pn.async_create(
                        hass,
                        f"Webhook enabled. Use this URL in Omlet Developer Portal → Manage Webhooks: {webhook_url}",
                        title="Omlet Smart Coop Webhook",
                    )
                except Exception:
                    pass
                hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_WEBHOOK_ID: current_id, CONF_WEBHOOK_NOTIFIED_ID: current_id},
                )
        else:
            # Disabled: unregister current id if present
            if current_id:
                try:
                    hass_webhook.async_unregister(hass, current_id)
                    _LOGGER.info("Webhook disabled and unregistered")
                except Exception:
                    pass
    except Exception as ex:
        _LOGGER.exception("Webhook option update handling failed: %r", ex)
