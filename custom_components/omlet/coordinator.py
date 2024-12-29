from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import API_BASE_URL, API_TIMEOUT
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class OmletDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Omlet API."""

    def __init__(self, hass: HomeAssistant, api_key: str, update_interval: timedelta):
        """Initialize the coordinator."""
        self.api_key = api_key
        super().__init__(
            hass,
            _LOGGER,
            name="Omlet Smart Coop",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from the API."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{API_BASE_URL}/device", headers=headers, timeout=API_TIMEOUT
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error fetching data: {response.status}")
                    data = await response.json()
                    _LOGGER.debug("Fetched data from API: %s", data)
                    return data
            except Exception as e:
                raise UpdateFailed(f"Error communicating with API: {e}")
