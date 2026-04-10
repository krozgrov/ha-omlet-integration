from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "omlet_smart_coop"
    / "webhook_helpers.py"
)
SPEC = importlib.util.spec_from_file_location("omlet_webhook_helpers", MODULE_PATH)
webhook_helpers = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = webhook_helpers
SPEC.loader.exec_module(webhook_helpers)


class FakeRequest:
    def __init__(self, payload=None, *, headers=None, query=None, json_error=None):
        self._payload = payload
        self._json_error = json_error
        self.headers = headers or {}
        self.query = query or {}

    async def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


class FakeResponse:
    def __init__(self, *, status=200, text="ok"):
        self.status = status
        self.text = text


class FakeHass:
    def __init__(self):
        self.tasks = []

    def async_create_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.append(task)
        return task


class FakeCoordinator:
    def __init__(self):
        self.refreshes = 0

    async def async_request_refresh(self):
        self.refreshes += 1


class NullLogger:
    def debug(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def exception(self, *args, **kwargs):
        pass


class FakeConfigEntries:
    def __init__(self):
        self.updates = []

    def async_update_entry(self, entry, *, data):
        self.updates.append(data)
        entry.data = data


class FakeHassWithConfig:
    def __init__(self):
        self.config_entries = FakeConfigEntries()


class WebhookTokenTests(unittest.TestCase):
    def test_extracts_authorization_token(self):
        request = FakeRequest(headers={"Authorization": "Bearer expected"})

        details = webhook_helpers.get_provided_webhook_token_details(request, {})

        self.assertEqual(details.token, "expected")
        self.assertEqual(details.source, "header:Authorization")

    def test_extracts_supported_header_token(self):
        request = FakeRequest(headers={"X-Omlet-Webhook-Token": " expected "})

        details = webhook_helpers.get_provided_webhook_token_details(request, {})

        self.assertEqual(details.token, "expected")
        self.assertEqual(details.source, "header:X-Omlet-Webhook-Token")

    def test_extracts_top_level_payload_token(self):
        request = FakeRequest()

        details = webhook_helpers.get_provided_webhook_token_details(
            request,
            {"token": "expected"},
        )

        self.assertEqual(details.token, "expected")
        self.assertEqual(details.source, "payload:token")

    def test_extracts_nested_payload_token(self):
        request = FakeRequest()

        details = webhook_helpers.get_provided_webhook_token_details(
            request,
            {"payload": {"webhookToken": "expected"}},
        )

        self.assertEqual(details.token, "expected")
        self.assertEqual(details.source, "payload.payload:webhookToken")

    def test_extracts_query_token(self):
        request = FakeRequest(query={"token": "expected"})

        details = webhook_helpers.get_provided_webhook_token_details(request, {})

        self.assertEqual(details.token, "expected")
        self.assertEqual(details.source, "query:token")


class WebhookHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_payload_without_configured_token_refreshes(self):
        entry = SimpleNamespace(options={})
        coordinator = FakeCoordinator()
        hass = FakeHass()
        handler = webhook_helpers.create_omlet_webhook_handler(
            entry,
            coordinator,
            response_factory=FakeResponse,
            logger=NullLogger(),
        )

        response = await handler(
            hass,
            "0123456789abcdef",
            FakeRequest(
                {
                    "deviceId": "1234567",
                    "parameterName": "Door Open State",
                    "oldValue": "closed",
                    "newValue": "open",
                }
            ),
        )
        await asyncio.gather(*hass.tasks)

        self.assertEqual(response.status, 200)
        self.assertEqual(coordinator.refreshes, 1)

    async def test_configured_token_mismatch_rejects_without_refresh(self):
        entry = SimpleNamespace(options={"webhook_token": "expected"})
        coordinator = FakeCoordinator()
        hass = FakeHass()
        handler = webhook_helpers.create_omlet_webhook_handler(
            entry,
            coordinator,
            response_factory=FakeResponse,
            logger=NullLogger(),
        )

        response = await handler(
            hass,
            "0123456789abcdef",
            FakeRequest({"token": "wrong"}),
        )

        self.assertEqual(response.status, 401)
        self.assertEqual(coordinator.refreshes, 0)
        self.assertEqual(hass.tasks, [])

    async def test_configured_token_match_refreshes(self):
        entry = SimpleNamespace(options={"webhook_token": "expected"})
        coordinator = FakeCoordinator()
        hass = FakeHass()
        handler = webhook_helpers.create_omlet_webhook_handler(
            entry,
            coordinator,
            response_factory=FakeResponse,
            logger=NullLogger(),
        )

        response = await handler(
            hass,
            "0123456789abcdef",
            FakeRequest({"token": "expected"}),
        )
        await asyncio.gather(*hass.tasks)

        self.assertEqual(response.status, 200)
        self.assertEqual(coordinator.refreshes, 1)

    async def test_non_json_payload_is_controlled_response(self):
        entry = SimpleNamespace(options={})
        coordinator = FakeCoordinator()
        hass = FakeHass()
        handler = webhook_helpers.create_omlet_webhook_handler(
            entry,
            coordinator,
            response_factory=FakeResponse,
            logger=NullLogger(),
        )

        response = await handler(
            hass,
            "0123456789abcdef",
            FakeRequest(json_error=ValueError("not json")),
        )
        await asyncio.gather(*hass.tasks)

        self.assertEqual(response.status, 200)
        self.assertEqual(coordinator.refreshes, 1)


class WebhookIdAndUrlTests(unittest.TestCase):
    def test_generates_stable_random_webhook_id(self):
        hass = FakeHassWithConfig()
        entry = SimpleNamespace(data={})

        webhook_id = webhook_helpers.ensure_omlet_webhook_id(hass, entry)

        self.assertEqual(len(webhook_id), 32)
        self.assertEqual(entry.data["webhook_id"], webhook_id)
        self.assertEqual(hass.config_entries.updates[-1]["webhook_id"], webhook_id)

    def test_reuses_existing_random_webhook_id(self):
        hass = FakeHassWithConfig()
        entry = SimpleNamespace(data={"webhook_id": "existing"})

        webhook_id = webhook_helpers.ensure_omlet_webhook_id(hass, entry)

        self.assertEqual(webhook_id, "existing")
        self.assertEqual(hass.config_entries.updates, [])

    def test_warns_for_non_public_urls(self):
        self.assertIsNotNone(webhook_helpers.describe_webhook_url("/api/webhook/id"))
        self.assertIsNotNone(
            webhook_helpers.describe_webhook_url("https://homeassistant.local/api/webhook/id")
        )
        self.assertIsNotNone(
            webhook_helpers.describe_webhook_url("http://192.168.1.10/api/webhook/id")
        )
        self.assertIsNone(
            webhook_helpers.describe_webhook_url("https://example.com/api/webhook/id")
        )


if __name__ == "__main__":
    unittest.main()
