"""Test diagnostics for Omlet Smart Coop integration."""

from unittest.mock import AsyncMock, patch

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant

from custom_components.omlet_smart_coop.const import CONF_API_KEY, CONF_WEBHOOK_TOKEN, DOMAIN
from custom_components.omlet_smart_coop.diagnostics import async_get_config_entry_diagnostics
from pytest_homeassistant_custom_component.common import MockConfigEntry

from . import init_integration


async def test_entry_diagnostics_redacts_secrets(
    hass: HomeAssistant,
    omlet_devices,
) -> None:
    """Ensure diagnostics redact secrets."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test-api-key"},
        options={CONF_WEBHOOK_TOKEN: "secret"},
        title="Omlet Smart Coop",
    )

    with patch(
        "custom_components.omlet_smart_coop.api_client.OmletApiClient.fetch_devices",
        new=AsyncMock(return_value=omlet_devices),
    ):
        await init_integration(hass, entry)

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["data"][CONF_API_KEY] == REDACTED
    assert diagnostics["entry"]["options"][CONF_WEBHOOK_TOKEN] == REDACTED
