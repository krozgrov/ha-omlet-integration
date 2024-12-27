"""Constants for Omlet Integration."""

from homeassistant.const import Platform

# Domain of the integration
DOMAIN = "omlet_smart_coop"

# Supported platforms
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

# Device types
DEVICE_TYPES = {
    "CHICKEN_DOOR": "Chicken Door",  # Automatic chicken door
}

# Default configurations
DEFAULT_POLLING_INTERVAL = 60  # Polling interval in seconds

# Entity attribute keys
ATTR_DOOR_STATE = "door_state"  # e.g., "open" or "closed"
ATTR_LIGHT_STATE = "light_state"  # e.g., "on" or "off"
ATTR_BATTERY_LEVEL = "battery_level"  # Battery percentage (e.g., 100)
ATTR_SIGNAL_STRENGTH = "signal_strength"  # Wi-Fi signal strength (e.g., RSSI)

# Entity states
STATE_DOOR_OPEN = "open"
STATE_DOOR_CLOSED = "closed"
STATE_LIGHT_ON = "on"
STATE_LIGHT_OFF = "off"

# Configuration keys
CONF_TIMEZONE = "timezone"
CONF_USE_DST = "use_dst"  # Daylight Saving Time
CONF_UPDATE_FREQUENCY = "update_frequency"  # Firmware check interval in seconds
CONF_LANGUAGE = "language"
CONF_OVERNIGHT_SLEEP_ENABLE = "overnight_sleep_enable"
CONF_OVERNIGHT_SLEEP_START = "overnight_sleep_start"
CONF_OVERNIGHT_SLEEP_END = "overnight_sleep_end"

# Connectivity configuration keys
CONF_BLUETOOTH_STATE = "bluetooth_state"
CONF_WIFI_STATE = "wifi_state"

# Door configuration keys
CONF_DOOR_TYPE = "door_type"  # e.g., 'sliding' or 'rotary'
CONF_OPEN_MODE = "open_mode"  # e.g., 'light', 'time', 'manual'
CONF_OPEN_DELAY = "open_delay"  # Delay in minutes
CONF_OPEN_LIGHT_LEVEL = "open_light_level"  # Light level threshold
CONF_OPEN_TIME = "open_time"  # Scheduled open time

# Light configuration keys
CONF_LIGHT_MODE = "light_mode"  # e.g., 'auto' or 'manual'
CONF_MINUTES_BEFORE_CLOSE = "minutes_before_close"  # For auto mode
CONF_MAX_ON_TIME = "max_on_time"  # Prevents light from being left on

# Event types
EVENT_TYPE_DOOR_STATE_CHANGE = "door_state_change"
EVENT_TYPE_LIGHT_STATE_CHANGE = "light_state_change"
EVENT_TYPE_BATTERY_LEVEL_CHANGE = "battery_level_change"

# Fault types
FAULT_NONE = "none"
FAULT_BLOCKED = "blocked"
FAULT_CRUSH = "crush"
FAULT_WIRING = "wiring"

# Power source types
POWER_SOURCE_INTERNAL = "internal"
POWER_SOURCE_EXTERNAL = "external"

# Connectivity states
CONNECTIVITY_STATE_ON = "on"
CONNECTIVITY_STATE_OFF = "off"

# Language options
LANGUAGE_ENGLISH = "en"
LANGUAGE_SPANISH = "es"
# Add other supported languages as needed

# Timezone offsets
TIMEZONE_UTC = "0"
TIMEZONE_PST = "-8"
TIMEZONE_EST = "-5"
# Add other timezones as needed

# Logging/debugging
DEBUG_ENABLED = False  # Can be toggled for verbose logging

# API-specific constants
API_BASE_URL = "https://x107.omlet.co.uk/api/v1"
CONF_API_KEY = "api_key"
API_ENDPOINT_DEVICES = "/device"
API_ENDPOINT_DEVICE_ACTION = "/device/{deviceId}/action/{action}"
API_ENDPOINT_DEVICE_CONFIG = "/device/{deviceId}/configuration"
API_ENDPOINT_WHOAMI = "/whoami"
API_RETRY_COUNT = 3  # Number of retries for API calls
API_TIMEOUT = 10  # Timeout for API requests in seconds
