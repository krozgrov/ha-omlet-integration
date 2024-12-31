from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol
from .const import DOMAIN, CONF_API_KEY, CONF_REFRESH_INTERVAL
from .api_client import OmletApiClient


# Error to indicate we cannot connect.
class CannotConnect(HomeAssistantError):
    pass


# Error to indicate invalid authentication.
class InvalidAuth(HomeAssistantError):
    pass


# Handle the config flow for Omlet Smart Coop.
class OmletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Handle the user step.
        errors = {}
        if user_input is not None:
            try:
                await self._validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"
            else:
                # Set unique ID and abort if already configured
                await self.async_set_unique_id("omlet_coop")
                self._abort_if_unique_id_configured()

                # Create the configuration entry
                return self.async_create_entry(
                    title="Omlet Smart Coop",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional (CONF_REFRESH_INTERVAL, default=300): int,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        # Handle reauthentication.
        self.reauth_entry = entry_data
        await self.async_set_unique_id("omlet_coop")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        # Handle reauthentication confirmation.
        errors = {}
        if user_input is not None:
            try:
                await self._validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "unknown"
            else:
                # Update entry with new API key
                self.hass.config_entries.async_update_entry(
                    self.reauth_entry,
                    data={
                        **self.reauth_entry.data,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_REFRESH_INTERVAL: user_input.get(CONF_REFRESH_INTERVAL, 300),
                    },
                )
                await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        
        current_interval = self.reauth_entry.get(CONF_REFRESH_INTERVAL, 300)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(CONF_REFRESH_INTERVAL, default=current_interval): int,
                }
            ),
            errors=errors,
        )

    async def _validate_input(self, data):
        # Validate the user input.
        api_key = data[CONF_API_KEY]

        # Use the API client to validate
        client = OmletApiClient(api_key=api_key)  # No host needed
        if not await client.is_valid():
            raise InvalidAuth
