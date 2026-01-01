from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.omlet_smart_coop.const import (
    CONF_API_KEY,
    CONF_DEFAULT_POLLING_INTERVAL,
    CONF_DISABLE_POLLING,
    CONF_ENABLE_WEBHOOKS,
    CONF_POLLING_INTERVAL,
    CONF_WEBHOOK_TOKEN,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_config_flow_valid(hass):
    with patch(
        "custom_components.omlet_smart_coop.config_flow.OmletApiClient.is_valid",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_API_KEY: "valid-key", CONF_POLLING_INTERVAL: 600},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_API_KEY] == "valid-key"
    assert result["data"][CONF_POLLING_INTERVAL] == 600


@pytest.mark.asyncio
async def test_config_flow_invalid_auth(hass):
    with patch(
        "custom_components.omlet_smart_coop.config_flow.OmletApiClient.is_valid",
        new=AsyncMock(return_value=False),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_API_KEY: "invalid-key"},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"][CONF_API_KEY] == "invalid_auth"


@pytest.mark.asyncio
async def test_options_flow_validation(hass, config_entry):
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_POLLING_INTERVAL: 10,
            CONF_ENABLE_WEBHOOKS: True,
            CONF_WEBHOOK_TOKEN: "token",
            CONF_DISABLE_POLLING: False,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"][CONF_POLLING_INTERVAL] == "invalid_polling_interval"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_POLLING_INTERVAL: CONF_DEFAULT_POLLING_INTERVAL,
            CONF_ENABLE_WEBHOOKS: True,
            CONF_WEBHOOK_TOKEN: "token",
            CONF_DISABLE_POLLING: False,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_POLLING_INTERVAL] == CONF_DEFAULT_POLLING_INTERVAL
