import aiohttp
from aiohttp import ClientError
import logging
from typing import Any, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


class OmletApiClient:
    # Client for interacting with the Omlet API.

    BASE_URL = "https://x107.omlet.co.uk/api/v1"

    def __init__(self, api_key: str):
        # Initialize the API client.
        self.api_key = api_key
        self._headers = {"Authorization": f"Bearer {self.api_key}"}
        self._timeout = 10

    async def is_valid(self) -> bool:
        # Validate the connection to the API.
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/whoami",
                    headers=self._headers,
                    timeout=self._timeout,
                ) as response:
                    return response.status == 200
        except ClientError as err:
            _LOGGER.error("Error validating API connection: %s", err)
            return False

    async def fetch_devices(self) -> List[Dict[str, Any]]:
        # Fetch the list of devices.
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/device",
                    headers=self._headers,
                    timeout=self._timeout,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientError as err:
            _LOGGER.error("Error fetching devices: %s", err)
            raise

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

            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("Executing action at URL: %s", full_url)
                async with session.post(
                    full_url, headers=self._headers, timeout=self._timeout
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

    async def get_device_configuration(self, device_id: str) -> Dict[str, Any]:
        """Get configuration for a specific device.

        Args:
            device_id: The ID of the device

        Returns:
            Dict containing the device configuration
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/device/{device_id}/configuration",
                    headers=self._headers,
                    timeout=self._timeout,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientError as err:
            _LOGGER.error("Error fetching device configuration: %s", err)
            raise

    async def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get current state for a specific device.

        Args:
            device_id: The ID of the device

        Returns:
            Dict containing the device state
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/device/{device_id}/state",
                    headers=self._headers,
                    timeout=self._timeout,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientError as err:
            _LOGGER.error("Error fetching device state: %s", err)
            raise

    async def update_device_configuration(
        self, device_id: str, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update configuration for a specific device.

        Args:
            device_id: The ID of the device
            configuration: Dictionary containing the configuration to update

        Returns:
            Dict containing the updated configuration
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.BASE_URL}/device/{device_id}/configuration",
                    headers=self._headers,
                    json=configuration,
                    timeout=self._timeout,
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientError as err:
            _LOGGER.error("Error updating device configuration: %s", err)
            raise
