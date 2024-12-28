from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, API_BASE_URL, CONF_API_KEY
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up diagnostic sensors for the Omlet Smart Coop."""
    api_key = entry.data.get(CONF_API_KEY)
    if not api_key:
        _LOGGER.error("API key not found in config entry.")
        return

    # Fetch devices from the API
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with session.get(
                f"{API_BASE_URL}/device", headers=headers, timeout=10
            ) as response:
                if response.status != 200:
                    _LOGGER.error(f"Failed to fetch devices: {response.status}")
                    return
                devices = await response.json()
    except Exception as e:
        _LOGGER.error(f"Error fetching devices for diagnostics: {e}")
        return

    # Create diagnostic sensors
    diagnostic_entities = []
    for device in devices:
        device_id = device["deviceId"]
        device_name = device["name"]
        device_model = device["deviceType"]

        # Tie to service
        device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Omlet",
            model=device_model,
            via_device=(DOMAIN, device_id),
        )

        # Battery Level
        battery_level = device.get("state", {}).get("general", {}).get("batteryLevel")
        if battery_level is not None:
            diagnostic_entities.append(
                OmletDiagnosticSensor(
                    f"{device_name} Battery",
                    f"{device_id}_battery",
                    battery_level,
                    device_info,
                    "battery",
                )
            )

        # Firmware Version
        firmware_version = device.get("state", {}).get("general", {}).get(
            "firmwareVersionCurrent"
        )
        if firmware_version:
            diagnostic_entities.append(
                OmletDiagnosticSensor(
                    f"{device_name} Firmware",
                    f"{device_id}_firmware",
                    firmware_version,
                    device_info,
                )
            )

        # Power Source
        power_source = device.get("state", {}).get("general", {}).get("powerSource")
        if power_source:
            diagnostic_entities.append(
                OmletDiagnosticSensor(
                    f"{device_name} Power Source",
                    f"{device_id}_power_source",
                    power_source,
                    device_info,
                )
            )

        # Wi-Fi Strength
        wifi_strength = device.get("state", {}).get("connectivity", {}).get(
            "wifiStrength"
        )
        if wifi_strength:
            diagnostic_entities.append(
                OmletDiagnosticSensor(
                    f"{device_name} Wi-Fi Strength",
                    f"{device_id}_wifi_strength",
                    wifi_strength,
                    device_info,
                )
            )

    async_add_entities(diagnostic_entities)


class OmletDiagnosticSensor(SensorEntity):
    """A diagnostic sensor for the Omlet Smart Coop."""

    def __init__(self, name, unique_id, state, device_info, device_class=None):
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_native_value = state
        self._attr_device_info = device_info
        self._attr_entity_category = "diagnostic"  # Categorize as diagnostic
        self._attr_device_class = device_class  # Optional device class (e.g., "battery" for battery sensors)