import aiohttp
import asyncio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, API_BASE_URL, CONF_API_KEY


class OmletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet Smart Coop integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step to set up the integration."""
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            errors = {}

            try:
                # Validate the provided API key
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    async with session.get(
                        f"{API_BASE_URL}/whoami", headers=headers, timeout=10
                    ) as response:
                        if response.status == 200:
                            # Successfully validated, create the config entry
                            return self.async_create_entry(
                                title="Omlet Smart Coop",
                                data={CONF_API_KEY: api_key},
                            )
                        elif response.status == 401:
                            errors["base"] = "invalid_auth"
                        else:
                            errors["base"] = "unknown_error"

            except asyncio.TimeoutError:
                errors["base"] = "timeout"
            except aiohttp.ClientError as e:
                self.hass.logger.error(f"API request failed: {e}")
                errors["base"] = "connection_error"
            except Exception as e:
                self.hass.logger.error(f"Unexpected error: {e}")
                errors["base"] = "unknown_error"

            # Show the form again with errors
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
                errors=errors,
            )

        # Show the form for the first time
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
        )
