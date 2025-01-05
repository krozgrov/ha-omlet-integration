import logging
from datetime import timedelta
from typing import Dict, Any, Set, List, Callable
from dataclasses import dataclass, field
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api_client import OmletApiClient
from .const import MIN_POLLING_INTERVAL, MAX_POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration class for validation settings."""

    min_polling_interval: int = MIN_POLLING_INTERVAL
    max_polling_interval: int = MAX_POLLING_INTERVAL
    required_device_fields: Set[str] = field(default_factory=lambda: {"deviceId"})
    required_action_fields: Set[str] = field(
        default_factory=lambda: {"actionName", "description", "actionValue"}
    )


class DataParser:
    """Utility class for parsing data safely."""

    @staticmethod
    def safe_parse(
        data: Dict[str, Any], parser_func: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Safely parse data using the provided parser function.

        Args:
            data: Dictionary of data to parse
            parser_func: Function to use for parsing

        Returns:
            Parsed data dictionary or empty dict if parsing fails
        """
        try:
            return parser_func(data)
        except Exception as err:
            _LOGGER.error("Error parsing data: %s", str(err))
            return {}

    @staticmethod
    def extract_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Extract specified fields from a dictionary.

        Args:
            data: Source dictionary
            fields: List of fields to extract

        Returns:
            Dictionary containing requested fields
        """
        return {field: data.get(field) for field in fields}


class OmletDataCoordinator(DataUpdateCoordinator):
    """Coordinator to handle Omlet data updates."""

    def __init__(self, hass, api_key: str, config_entry) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            api_key: API key for Omlet API
            config_entry: Configuration entry
        """
        self.api_key = api_key
        self.api_client = OmletApiClient(api_key)
        self.devices: Dict[str, Any] = {}
        self.config_entry = config_entry
        self.validation = ValidationConfig()
        self._unsub_refresh = None

        # Validate and set the polling interval
        refresh_interval = self._validate_polling_interval(
            config_entry.options.get("polling_interval", 300)
        )

        super().__init__(
            hass,
            _LOGGER,
            name="OmletDataCoordinator",
            update_interval=timedelta(seconds=refresh_interval),
        )

    def _validate_polling_interval(self, interval: int) -> int:
        """Validate and adjust polling interval if needed.

        Args:
            interval: Polling interval in seconds

        Returns:
            Validated polling interval
        """
        if interval < self.validation.min_polling_interval:
            _LOGGER.warning(
                "Polling interval too low, setting to minimum of %s seconds",
                self.validation.min_polling_interval,
            )
            return self.validation.min_polling_interval
        elif interval > self.validation.max_polling_interval:
            _LOGGER.warning(
                "Polling interval too high, setting to maximum of %s seconds",
                self.validation.max_polling_interval,
            )
            return self.validation.max_polling_interval
        return interval

    async def update_polling_interval(self, new_interval: int) -> None:
        """Update the polling interval.

        Args:
            new_interval: New polling interval in seconds
        """
        validated_interval = self._validate_polling_interval(new_interval)
        self.update_interval = timedelta(seconds=validated_interval)
        _LOGGER.info("Polling interval updated to %s seconds", validated_interval)
        await self.async_request_refresh()

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch updated data from API.

        Returns:
            Dictionary of device data

        Raises:
            UpdateFailed: If there is an error fetching or parsing data
        """
        try:
            devices_data = await self.api_client.fetch_devices()
            self._validate_devices_data(devices_data)

            self.devices = {
                device["deviceId"]: self._parse_device(device)
                for device in devices_data
                if self._is_valid_device(device)
            }

            _LOGGER.debug("Device data updated: %s", self.devices)
            return self.devices

        except Exception as err:
            _LOGGER.error("Error fetching devices data: %s", str(err))
            raise UpdateFailed(f"Error fetching devices: {str(err)}") from err

    def _validate_devices_data(self, data: Any) -> None:
        """Validate the devices data received from the API.

        Args:
            data: Data to validate

        Raises:
            UpdateFailed: If data is invalid
        """
        if not data:
            raise UpdateFailed("No data received from API")
        if not isinstance(data, list):
            raise UpdateFailed(f"Invalid data format received: {type(data)}")

    def _is_valid_device(self, device: Dict[str, Any]) -> bool:
        """Check if a device has all required fields.

        Args:
            device: Device data to validate

        Returns:
            True if device is valid, False otherwise
        """
        missing_fields = [
            field
            for field in self.validation.required_device_fields
            if field not in device
        ]
        if missing_fields:
            _LOGGER.warning(
                "Device %s is missing fields: %s",
                device.get("deviceId", "Unknown"),
                missing_fields,
            )
        return not missing_fields

    def _parse_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Parse device data into standard format.

        Args:
            device: Raw device data

        Returns:
            Parsed device data
        """
        parser = DataParser()

        # Get firmware version from state if available
        state = device.get("state", {})
        general_state = state.get("general", {})
        firmware = general_state.get("firmwareVersionCurrent", "Unknown")

        parsed_device = {
            "deviceId": device.get("deviceId"),
            "deviceSerial": device.get("deviceSerial", "Unknown"),
            "firmware": firmware,
            "name": device.get("name", "Unknown"),
            "deviceType": device.get("deviceType", "Unknown Model"),
            "state": self._parse_device_state(device.get("state", {})),
            "configuration": self._parse_device_configuration(
                device.get("configuration", {})
            ),
            "actions": self._parse_device_actions(device.get("actions", [])),
        }

        _LOGGER.debug("Parsed device data: %s", parsed_device)
        return parsed_device

    def _parse_device_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse device state data.

        Args:
            state: Raw state data

        Returns:
            Parsed state data
        """
        parser = DataParser()

        general_fields = [
            "firmwareVersionCurrent",
            "batteryLevel",
            "powerSource",
            "uptime",
        ]
        connectivity_fields = ["wifiStrength", "ssid", "connected"]
        door_fields = ["state", "lastOpenTime", "lastCloseTime", "fault", "lightLevel"]
        light_fields = ["state"]

        return {
            "general": parser.extract_fields(state.get("general", {}), general_fields),
            "connectivity": parser.extract_fields(
                state.get("connectivity", {}), connectivity_fields
            ),
            "door": parser.extract_fields(state.get("door", {}), door_fields),
            "light": parser.extract_fields(state.get("light", {}), light_fields),
        }

    def _parse_device_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse device configuration data.

        Args:
            config: Raw configuration data

        Returns:
            Parsed configuration data
        """
        config_fields = ["light", "door", "connectivity", "general"]
        return {key: config.get(key, {}) for key in config_fields}

    def _parse_device_actions(self, actions: list) -> list:
        """Parse device actions.

        Args:
            actions: List of raw actions

        Returns:
            List of valid actions
        """
        return [
            action
            for action in actions
            if all(field in action for field in self.validation.required_action_fields)
        ]

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        _LOGGER.info("Shutting down Omlet Data Coordinator")
        if self._unsub_refresh is not None:
            self._unsub_refresh()
