from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_API_KEY


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omlet Smart Coop from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store the API key for use in platforms
    hass.data[DOMAIN][entry.entry_id] = {CONF_API_KEY: entry.data[CONF_API_KEY]}

    # Forward the setup to supported platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "switch"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok