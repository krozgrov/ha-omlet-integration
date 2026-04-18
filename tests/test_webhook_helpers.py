from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from custom_components.omlet_smart_coop import webhook_helpers


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


def test_extracts_authorization_token():
    request = FakeRequest(headers={"Authorization": "Bearer expected"})
    details = webhook_helpers.get_provided_webhook_token_details(request, {})
    assert details.token == "expected"
    assert details.source == "header:Authorization"


def test_extracts_supported_header_token():
    request = FakeRequest(headers={"X-Omlet-Webhook-Token": " expected "})
    details = webhook_helpers.get_provided_webhook_token_details(request, {})
    assert details.token == "expected"
    assert details.source == "header:X-Omlet-Webhook-Token"


def test_extracts_top_level_payload_token():
    request = FakeRequest()
    details = webhook_helpers.get_provided_webhook_token_details(
        request,
        {"token": "expected"},
    )
    assert details.token == "expected"
    assert details.source == "payload:token"


def test_extracts_nested_payload_token():
    request = FakeRequest()
    details = webhook_helpers.get_provided_webhook_token_details(
        request,
        {"payload": {"webhookToken": "expected"}},
    )
    assert details.token == "expected"
    assert details.source == "payload.payload:webhookToken"


def test_extracts_query_token():
    request = FakeRequest(query={"token": "expected"})
    details = webhook_helpers.get_provided_webhook_token_details(request, {})
    assert details.token == "expected"
    assert details.source == "query:token"


@pytest.mark.asyncio
async def test_official_payload_without_configured_token_refreshes():
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
    assert response.status == 200
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_configured_token_mismatch_rejects_without_refresh():
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
    assert response.status == 401
    assert coordinator.refreshes == 0
    assert hass.tasks == []


@pytest.mark.asyncio
async def test_configured_token_match_refreshes():
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
    assert response.status == 200
    assert coordinator.refreshes == 1


@pytest.mark.asyncio
async def test_non_json_payload_is_controlled_response():
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
    assert response.status == 200
    assert coordinator.refreshes == 1


def test_generates_stable_random_webhook_id():
    hass = FakeHassWithConfig()
    entry = SimpleNamespace(data={})
    webhook_id = webhook_helpers.ensure_omlet_webhook_id(hass, entry)
    assert len(webhook_id) == 32
    assert entry.data["webhook_id"] == webhook_id
    assert hass.config_entries.updates[-1]["webhook_id"] == webhook_id


def test_reuses_existing_random_webhook_id():
    hass = FakeHassWithConfig()
    entry = SimpleNamespace(data={"webhook_id": "existing"})
    webhook_id = webhook_helpers.ensure_omlet_webhook_id(hass, entry)
    assert webhook_id == "existing"
    assert hass.config_entries.updates == []


def test_warns_for_non_public_urls():
    assert webhook_helpers.describe_webhook_url("/api/webhook/id") is not None
    assert (
        webhook_helpers.describe_webhook_url(
            "https://homeassistant.local/api/webhook/id"
        )
        is not None
    )
    assert (
        webhook_helpers.describe_webhook_url("http://192.168.1.10/api/webhook/id")
        is not None
    )
    assert (
        webhook_helpers.describe_webhook_url("https://example.com/api/webhook/id")
        is None
    )
