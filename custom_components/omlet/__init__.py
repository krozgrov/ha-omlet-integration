from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from aiohttp import ClientSession
from .const import DOMAIN, API_BASE_URL, API_TIMEOUT, API_RETRY_COUNT

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Omlet Smart Coop integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create an aiohttp session for the integration
    session = ClientSession()

    # Store the aiohttp session and API base URL in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "session": session,
        "api_base_url": API_BASE_URL,
        "api_key": entry.data["client_secret"],  # Assuming the client secret is the API key
        "timeout": API_TIMEOUT,
        "retry_count": API_RETRY_COUNT,
    }

    # Forward setup to supported platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    if unload_ok:
        # Close the aiohttp session
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        await session.close()

        # Clean up hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok