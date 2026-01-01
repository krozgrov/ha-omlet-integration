from unittest.mock import AsyncMock, patch

import pytest

from custom_components.omlet_smart_coop.const import (
    CONF_API_KEY,
    CONF_ENABLE_WEBHOOKS,
    CONF_WEBHOOK_ID,
    CONF_WEBHOOK_TOKEN,
    DOMAIN,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_webhook_requires_token_when_configured(hass, hass_client, omlet_devices):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        options={CONF_ENABLE_WEBHOOKS: True, CONF_WEBHOOK_TOKEN: "secret"},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.omlet_smart_coop.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(return_value=omlet_devices),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

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
