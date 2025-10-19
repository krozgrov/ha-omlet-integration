# Constants for Omlet Integration. - 1/5/2024

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

# Service constants
SERVICE_OPEN_DOOR = "open_door"
SERVICE_CLOSE_DOOR = "close_door"
SERVICE_UPDATE_OVERNIGHT_SLEEP = "update_overnight_sleep"
SERVICE_UPDATE_DOOR_SCHEDULE = "update_door_schedule"

# Service Fields/Attributes
ATTR_ENABLED = "enabled"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_DOOR_MODE = "door_mode"
ATTR_OPEN_TIME = "open_time"
ATTR_CLOSE_TIME = "close_time"
ATTR_OPEN_LIGHT_LEVEL = "open_light_level"
ATTR_CLOSE_LIGHT_LEVEL = "close_light_level"
ATTR_OPEN_DELAY = "open_delay"
ATTR_CLOSE_DELAY = "close_delay"
ATTR_POLL_MODE = "poll_mode"
POLL_MODE_RESPONSIVE = "responsive"
POLL_MODE_POWER_SAVINGS = "power_savings"
POLL_FREQ_RESPONSIVE = 120
POLL_FREQ_POWER_SAVINGS = 600

# Valid Modes
VALID_DOOR_MODES = ["time", "light", "manual"]

# Webhook configuration
CONF_ENABLE_WEBHOOKS = "enable_webhooks"
CONF_WEBHOOK_ID = "webhook_id"
CONF_WEBHOOK_TOKEN = "webhook_token"
CONF_DISABLE_POLLING = "disable_polling"  # Webhooks-only mode

# Log Messages

# General API Errors
ERROR_VALIDATE_API = "Failed to validate API connection: %s"
