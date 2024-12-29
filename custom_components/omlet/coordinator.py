import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .api_client import OmletApiClient

_LOGGER = logging.getLogger(__name__)


class OmletDataCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching and structuring data from the Omlet API."""

    def __init__(self, hass, api_key, update_interval_seconds):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="OmletDataCoordinator",
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.api_key = api_key
        self.api_client = OmletApiClient(api_key)
        self.devices = {}  # Will hold all parsed device data

    async def _async_update_data(self):
        """Fetch and process data from the API."""
        try:
            # Fetch devices from the API
            devices_data = await self.api_client.fetch_devices()
            _LOGGER.debug("Fetched devices data: %s", devices_data)

            # Parse and structure the devices data
            self.devices = {
                device["deviceId"]: {
                    "deviceId": device.get("deviceId"),
                    "deviceSerial": device.get("deviceSerial"),
                    "deviceTypeId": device.get("deviceTypeId"),
                    "groupId": device.get("groupId"),
                    "name": device.get("name"),
                    "deletePending": device.get("deletePending", 0),
                    "lastConnected": device.get("lastConnected"),
                    "nextConnection": device.get("nextConnection"),
                    "overdueConnection": device.get("overdueConnection", 0),
                    "batteryCount": device.get("batteryCount", 0),
                    "batteryWarned": device.get("batteryWarned", 0),
                    "bleOnly": device.get("bleOnly", 0),
                    "state": {
                        "general": {
                            "firmwareVersionCurrent": device["state"]["general"].get(
                                "firmwareVersionCurrent"
                            ),
                            "firmwareLastCheck": device["state"]["general"].get(
                                "firmwareLastCheck"
                            ),
                            "batteryLevel": device["state"]["general"].get(
                                "batteryLevel"
                            ),
                            "powerSource": device["state"]["general"].get(
                                "powerSource"
                            ),
                            "displayLine1": device["state"]["general"].get(
                                "displayLine1"
                            ),
                            "displayLine2": device["state"]["general"].get(
                                "displayLine2"
                            ),
                            "firmwareVersionPrevious": device["state"]["general"].get(
                                "firmwareVersionPrevious"
                            ),
                            "uptime": device["state"]["general"].get("uptime"),
                        },
                        "connectivity": {
                            "wifiStrength": device["state"]["connectivity"].get(
                                "wifiStrength"
                            ),
                            "ssid": device["state"]["connectivity"].get("ssid"),
                            "connected": device["state"]["connectivity"].get(
                                "connected"
                            ),
                        },
                        "door": {
                            "state": device["state"]["door"].get("state"),
                            "lastOpenTime": device["state"]["door"].get("lastOpenTime"),
                            "lastCloseTime": device["state"]["door"].get(
                                "lastCloseTime"
                            ),
                            "fault": device["state"]["door"].get("fault"),
                            "lightLevel": device["state"]["door"].get("lightLevel"),
                        },
                        "light": {
                            "state": device["state"]["light"].get("state"),
                        },
                    },
                    "configuration": {
                        "light": {
                            "mode": device["configuration"]["light"].get("mode"),
                            "minutesBeforeClose": device["configuration"]["light"].get(
                                "minutesBeforeClose"
                            ),
                            "maxOnTime": device["configuration"]["light"].get(
                                "maxOnTime"
                            ),
                            "equipped": device["configuration"]["light"].get(
                                "equipped"
                            ),
                        },
                        "door": {
                            "openMode": device["configuration"]["door"].get("openMode"),
                            "openDelay": device["configuration"]["door"].get(
                                "openDelay"
                            ),
                            "openTime": device["configuration"]["door"].get("openTime"),
                            "closeMode": device["configuration"]["door"].get(
                                "closeMode"
                            ),
                            "closeDelay": device["configuration"]["door"].get(
                                "closeDelay"
                            ),
                            "closeLightLevel": device["configuration"]["door"].get(
                                "closeLightLevel"
                            ),
                            "closeTime": device["configuration"]["door"].get(
                                "closeTime"
                            ),
                            "openLightLevel": device["configuration"]["door"].get(
                                "openLightLevel"
                            ),
                            "doorType": device["configuration"]["door"].get("doorType"),
                            "colour": device["configuration"]["door"].get("colour"),
                        },
                        "connectivity": {
                            "wifiState": device["configuration"]["connectivity"].get(
                                "wifiState"
                            ),
                        },
                        "general": {
                            "datetime": device["configuration"]["general"].get(
                                "datetime"
                            ),
                            "timezone": device["configuration"]["general"].get(
                                "timezone"
                            ),
                            "updateFrequency": device["configuration"]["general"].get(
                                "updateFrequency"
                            ),
                            "language": device["configuration"]["general"].get(
                                "language"
                            ),
                            "stayAliveTime": device["configuration"]["general"].get(
                                "stayAliveTime"
                            ),
                            "statusUpdatePeriod": device["configuration"][
                                "general"
                            ].get("statusUpdatePeriod"),
                            "pollFreq": device["configuration"]["general"].get(
                                "pollFreq"
                            ),
                            "overnightSleepEnable": device["configuration"][
                                "general"
                            ].get("overnightSleepEnable"),
                            "overnightSleepStart": device["configuration"][
                                "general"
                            ].get("overnightSleepStart"),
                            "overnightSleepEnd": device["configuration"]["general"].get(
                                "overnightSleepEnd"
                            ),
                        },
                    },
                    "deviceType": device.get("deviceType"),
                    "actions": [
                        {
                            "actionName": action.get("actionName"),
                            "description": action.get("description"),
                            "actionValue": action.get("actionValue"),
                            "pendingValue": action.get("pendingValue"),
                            "url": action.get("url"),
                        }
                        for action in device.get("actions", [])
                    ],
                }
                for device in devices_data
            }

            return self.devices

        except Exception as err:
            _LOGGER.error("Error updating data from Omlet API: %s", err)
            raise
