import pytest

from custom_components.omlet_smart_coop.const import (
    CONF_API_KEY,
    CONF_ENABLE_WEBHOOKS,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_TOKEN,
    DOMAIN,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from . import init_integration


@pytest.mark.asyncio
async def test_webhook_requires_token_when_configured(
    hass, hass_client, mock_fetch_devices
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        options={CONF_ENABLE_WEBHOOKS: True, CONF_WEBHOOK_TOKEN: "secret"},
    )
    await init_integration(hass, entry)

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    assert webhook_id

    client = await hass_client()

    resp = await client.post(
        f"/api/webhook/{webhook_id}",
        json={"payload": {"deviceId": "door-1"}},
    )
    assert resp.status == 401
    assert await resp.json() == ["invalid token"]

    resp = await client.post(
        f"/api/webhook/{webhook_id}",
        json={"payload": {"deviceId": "door-1"}},
        headers={"X-Omlet-Token": "secret"},
    )
    assert resp.status == 200
    assert await resp.json() == ["ok"]
