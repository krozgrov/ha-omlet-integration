import aiohttp
from aiohttp import ClientError


class OmletApiClient:
    """Client for interacting with the Omlet API."""

    BASE_URL = "https://x107.omlet.co.uk/api/v1"

    def __init__(self, api_key: str):
        """Initialize the API client."""
        self.api_key = api_key

    async def is_valid(self) -> bool:
        """Validate the connection to the API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.BASE_URL}/whoami", headers=headers, timeout=10
                ) as response:
                    return response.status == 200
        except ClientError:
            return False

    async def fetch_devices(self):
        """Fetch the list of devices."""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.get(
                f"{self.BASE_URL}/device", headers=headers, timeout=10
            ) as response:
                response.raise_for_status()
                return await response.json()
