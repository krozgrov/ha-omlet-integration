import pytest
from unittest.mock import AsyncMock, patch
from datetime import timedelta
from coordinator import OmletDataCoordinator
from api_client import OmletApiClient


@pytest.mark.asyncio
async def test_coordinator_gathers_data_correctly(hass):
    """Test the OmletDataCoordinator processes data correctly."""
    # Mock JSON response from the API
    mock_api_response = [
        {
            "deviceId": "y4df1owDkxSDshaO",
            "deviceSerial": "744dbd8b403c",
            "deviceTypeId": 1,
            "groupId": "C5P00xW59v6PHaLo",
            "name": "Big birbs",
            "deletePending": 0,
            "lastConnected": "2024-12-28T17:32:16+00:00",
            "nextConnection": "2024-12-29 02:00:00",
            "overdueConnection": 0,
            "batteryCount": 0,
            "batteryWarned": 0,
            "bleOnly": 0,
            "state": {
                "general": {
                    "firmwareVersionCurrent": "1.0.43-30ae801d",
                    "firmwareLastCheck": "2024-12-27T13:43:49+00:00",
                    "batteryLevel": 85,
                    "powerSource": "internal",
                    "displayLine1": "                ",
                    "displayLine2": "                ",
                    "firmwareVersionPrevious": "1.0.42-50f4ab95",
                    "uptime": 2501,
                },
                "connectivity": {
                    "wifiStrength": -69,
                    "ssid": "SlothNet-IoT",
                    "connected": False,
                },
                "door": {
                    "state": "open",
                    "lastOpenTime": "2024-12-28T07:30:14+00:00",
                    "lastCloseTime": "2024-12-27T18:40:15+00:00",
                    "fault": "none",
                    "lightLevel": 100,
                },
                "light": {
                    "state": "offpending",
                },
            },
            "configuration": {
                "light": {
                    "mode": "auto",
                    "minutesBeforeClose": 10,
                    "maxOnTime": 5,
                    "equipped": 2,
                },
                "door": {
                    "openMode": "time",
                    "openDelay": 0,
                    "openTime": "07:30",
                    "closeMode": "time",
                    "closeDelay": 0,
                    "closeLightLevel": 10,
                    "closeTime": "18:30",
                    "openLightLevel": 27,
                    "doorType": "sliding",
                    "colour": "grey",
                },
                "connectivity": {
                    "wifiState": "on",
                },
                "general": {
                    "datetime": "2024-12-28T12:32:14+00:00",
                    "timezone": "America/Detroit",
                    "updateFrequency": 86400,
                    "language": "en",
                    "stayAliveTime": 0,
                    "statusUpdatePeriod": 21600,
                    "pollFreq": 600,
                    "overnightSleepEnable": True,
                    "overnightSleepStart": "07:30",
                    "overnightSleepEnd": "21:00",
                },
            },
            "deviceType": "Autodoor",
            "actions": [
                {
                    "actionName": "close",
                    "description": "Close Door",
                    "actionValue": "close",
                    "pendingValue": "closepending",
                    "callback": None,
                    "url": "/device/y4df1owDkxSDshaO/action/close",
                },
            ],
        }
    ]

    # Mock the OmletApiClient's fetch_devices method
    with patch(
        "custom_components.omlet.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(return_value=mock_api_response),
    ):
        # Create an instance of the coordinator
        api_key = "mock_api_key"
        coordinator = OmletDataCoordinator(hass, api_key, timedelta(seconds=300))

        # Fetch the data
        await coordinator.async_config_entry_first_refresh()

        # Assertions to ensure data is processed correctly
        assert len(coordinator.devices) == 1  # Ensure one device is processed

        # Verify the device data
        device = coordinator.devices["y4df1owDkxSDshaO"]
        assert device["device_id"] == "y4df1owDkxSDshaO"
        assert device["state"]["general"]["firmwareVersionCurrent"] == "1.0.43-30ae801d"
        assert device["state"]["door"]["state"] == "open"
        assert device["configuration"]["door"]["doorType"] == "sliding"
        assert device["actions"][0]["description"] == "Close Door"