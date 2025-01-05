# Constants for Omlet Integration.

from homeassistant.const import Platform

# Domain of the integration
DOMAIN = "omlet_smart_coop"

# Supported platforms
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
]

# Configuration keys
API_BASE_URL = "https://x107.omlet.co.uk/api/v1"
CONF_API_KEY = "api_key"
CONF_POLLING_INTERVAL = "polling_interval"  # API Polling Interval
CONF_DEFAULT_POLLING_INTERVAL = 300  # Polling interval in seconds
MIN_POLLING_INTERVAL = 60  # Minimum allowed polling interval in seconds
MAX_POLLING_INTERVAL = 86400  # Maximum allowed polling interval in seconds

# Log Messages

# General API Errors
ERROR_VALIDATE_API = "Failed to validate API connection: %s"
