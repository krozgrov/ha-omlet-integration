from homeassistant import config_entries
from aiohttp import ClientSession
from .const import DOMAIN, CONF_API_KEY, API_BASE_URL
import voluptuous as vol


class OmletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            try:
                # Validate the API key with a test request
                async with ClientSession() as session:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    async with session.get(
                        f"{API_BASE_URL}/whoami", headers=headers, timeout=10
                    ) as resp:
                        if resp.status == 200:
                            return self.async_create_entry(
                                title="Omlet Smart Coop",
                                data={CONF_API_KEY: api_key},
                            )
                        errors["base"] = "invalid_auth"

            except Exception as e:
                self.hass.logger.error(f"Error during API validation: {e}")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )
