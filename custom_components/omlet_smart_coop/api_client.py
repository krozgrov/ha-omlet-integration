import aiohttp
from aiohttp import ClientError, ClientTimeout
import logging
from typing import Any, Dict, List, Optional
from .const import API_BASE_URL, ERROR_VALIDATE_API
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class OmletApiClient:
    """Client for interacting with the Omlet API."""

    BASE_URL = API_BASE_URL

    def __init__(self, api_key: str, hass=None):
        """Initialize the API client.

        Args:
            api_key: The API key for authentication
        """
        self.api_key = api_key
        self._hass = hass
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = 10
        self._session = async_get_clientsession(hass) if hass is not None else None

    async def is_valid(self) -> bool:
        """Validate the connection to the API.

        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            session = self._session or aiohttp.ClientSession()
            async with session.get(
                    f"{self.BASE_URL}/whoami",
                    headers=self._headers,
                    timeout=ClientTimeout(total=self._timeout),
                ) as response:
                    return response.status == 200
        except ClientError as err:
            _LOGGER.error(ERROR_VALIDATE_API, err)
            return False
        finally:
            if self._session is None and 'session' in locals():
                await session.close()

    async def fetch_devices(self) -> List[Dict[str, Any]]:
        """Fetch the list of devices.

        Returns:
            List[Dict[str, Any]]: List of device information

        Raises:
            ClientError: If there's an error fetching devices
        """
        try:
            session = self._session or aiohttp.ClientSession()
            async with session.get(
                    f"{self.BASE_URL}/device",
                    headers=self._headers,
                    timeout=ClientTimeout(total=self._timeout),
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientError as err:
            _LOGGER.error("Error fetching devices: %s", err)
            raise
        finally:
            if self._session is None and 'session' in locals():
                await session.close()

    async def execute_action(self, action_url: str) -> Optional[Dict[str, Any]]:
        """Execute an action on the device.

        Args:
            action_url: The URL path for the action to execute

        Returns:
            Dict containing the response from the API if content is returned,
            None for successful no-content responses

        Raises:
            ClientError: If there's an error executing the action
        """
        try:
            # Ensure action_url is treated as a path by removing any leading slash
            action_path = action_url.lstrip("/")
            full_url = f"{self.BASE_URL}/{action_path}"
            session = self._session or aiohttp.ClientSession()
            _LOGGER.debug("Executing action at URL: %s", full_url)
            async with session.post(
                full_url, headers=self._headers, timeout=ClientTimeout(total=self._timeout)
            ) as response:
                response.raise_for_status()
                # Handle 204 No Content response
                if response.status == 204:
                    _LOGGER.debug(
                        "Action executed successfully (no content returned)"
                    )
                    return None
                return await response.json()
        except ClientError as err:
            _LOGGER.error("Error executing action %s: %s", action_url, err)
            raise
        finally:
            if self._session is None and 'session' in locals():
                await session.close()

    async def patch_device_configuration(
        self, device_id: str, configuration: dict
    ) -> Optional[Dict[str, Any]]:
        """Send a PATCH request to update the device configuration.

        Args:
            device_id: The device ID to update
            configuration: The configuration data to patch

        Returns:
            Optional[Dict[str, Any]]: Response data if content is returned, None for 204 responses

        Raises:
            ClientError: If there's an error patching the configuration
        """
        try:
            url = f"{self.BASE_URL}/device/{device_id}/configuration"
            session = self._session or aiohttp.ClientSession()
            _LOGGER.debug(
                "Patching configuration at URL: %s with data: %s",
                url,
                configuration,
            )
            async with session.patch(
                url,
                json=configuration,
                headers=self._headers,
                timeout=ClientTimeout(total=self._timeout),
            ) as response:
                response.raise_for_status()
                if response.status == 204:
                    _LOGGER.debug(
                        "Patch successful for device %s (no content)", device_id
                    )
                    return None

                response_data = await response.json()
                _LOGGER.debug(
                    "Patch successful for device %s with response: %s",
                    device_id,
                    response_data,
                )
                return response_data

        except ClientError as err:
            _LOGGER.error("Error patching device configuration: %s", err)
            raise
        finally:
            if self._session is None and 'session' in locals():
                await session.close()

    async def get_device_configuration(self, device_id: str) -> Dict[str, Any]:
        """Get configuration for a specific device.

        Args:
            device_id: The ID of the device

        Returns:
            Dict containing the device configuration

        Raises:
            ClientError: If there's an error fetching the configuration
        """
        try:
            session = self._session or aiohttp.ClientSession()
            async with session.get(
                f"{self.BASE_URL}/device/{device_id}/configuration",
                headers=self._headers,
                timeout=ClientTimeout(total=self._timeout),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except ClientError as err:
            _LOGGER.error("Error fetching device configuration: %s", err)
            raise
        finally:
            if self._session is None and 'session' in locals():
                await session.close()

    async def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get current state for a specific device.

        Args:
            device_id: The ID of the device

        Returns:
            Dict containing the device state

        Raises:
            ClientError: If there's an error fetching the state
        """
        try:
            session = self._session or aiohttp.ClientSession()
            async with session.get(
                f"{self.BASE_URL}/device/{device_id}/state",
                headers=self._headers,
                timeout=ClientTimeout(total=self._timeout),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except ClientError as err:
            _LOGGER.error("Error fetching device state: %s", err)
            raise
        finally:
            if self._session is None and 'session' in locals():
                await session.close()

    async def update_device_configuration(
        self, device_id: str, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update configuration for a specific device.

        Args:
            device_id: The ID of the device
            configuration: Dictionary containing the configuration to update

        Returns:
            Dict containing the updated configuration

        Raises:
            ClientError: If there's an error updating the configuration
        """
        try:
            session = self._session or aiohttp.ClientSession()
            async with session.put(
                f"{self.BASE_URL}/device/{device_id}/configuration",
                headers=self._headers,
                json=configuration,
                timeout=ClientTimeout(total=self._timeout),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except ClientError as err:
            _LOGGER.error("Error updating device configuration: %s", err)
            raise
        finally:
            if self._session is None and 'session' in locals():
                await session.close()
