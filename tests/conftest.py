pytest_plugins = "pytest_homeassistant_custom_component"

import pytest

from custom_components.omlet_smart_coop.const import CONF_API_KEY, DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def omlet_devices() -> list[dict]:
    return [
        {
            "deviceId": "door-1",
            "deviceSerial": "SERIAL_DOOR_1",
            "firmware": "1.0.0",
            "name": "Coop Door",
            "deviceType": "Autodoor",
            "state": {
                "general": {
                    "firmwareVersionCurrent": "1.0.0",
                    "batteryLevel": 75,
                    "powerSource": "internal",
                    "uptime": 1234,
                },
                "connectivity": {
                    "wifiStrength": -45,
                    "ssid": "TestNet",
                    "connected": True,
                },
                "door": {
                    "state": "closed",
                    "lastOpenTime": "2026-01-01T08:00:00-05:00",
                    "lastCloseTime": "2026-01-01T17:00:00-05:00",
                    "fault": "none",
                    "lightLevel": 10,
                },
                "light": {"state": "off"},
            },
            "configuration": {
                "light": {
                    "mode": "auto",
                    "minutesBeforeClose": 5,
                    "maxOnTime": 3,
                    "equipped": 1,
                },
                "door": {
                    "openMode": "time",
                    "openDelay": 0,
                    "openTime": "08:00",
                    "closeMode": "time",
                    "closeDelay": 0,
                    "closeLightLevel": 6,
                    "closeTime": "17:00",
                    "openLightLevel": 15,
                },
                "fan": {},
                "connectivity": {"wifiState": "on"},
                "general": {"timezone": "America/Detroit"},
            },
            "actions": [
                {
                    "actionName": "open",
                    "description": "Open Door",
                    "actionValue": "open",
                    "url": "/device/door-1/action/open",
                },
                {
                    "actionName": "close",
                    "description": "Close Door",
                    "actionValue": "close",
                    "url": "/device/door-1/action/close",
                },
                {
                    "actionName": "on",
                    "description": "Light On",
                    "actionValue": "on",
                    "url": "/device/door-1/action/on",
                },
                {
                    "actionName": "off",
                    "description": "Light Off",
                    "actionValue": "off",
                    "url": "/device/door-1/action/off",
                },
            ],
        }
    ]


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        options={},
        title="Omlet Smart Coop",
    )
