from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol
from .const import DOMAIN, CONF_API_KEY, CONF_HOST


# Error to indicate we cannot connect.
class CannotConnect(HomeAssistantError):
    pass


# Error to indicate invalid authentication.
class InvalidAuth(HomeAssistantError):
    pass


# Handle the config flow for Omlet Smar Coop.
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
            else:
                # Set unique ID and abort if already configured
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                # Create the configuration entry
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        # Handle reauthentication.
        self.reauth_entry = entry_data
        await self.async_set_unique_id(entry_data[CONF_HOST])
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
            else:
                # Update entry with new API key
                self.hass.config_entries.async_update_entry(
                    self.reauth_entry,
                    data={
                        **self.reauth_entry.data,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                    },
                )
                await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def _validate_input(self, data):
        # Validate the user input.
        host = data[CONF_HOST]
        api_key = data[CONF_API_KEY]

        # Replace this with API validation logic
        if not await MyApiClient(host, api_key).is_valid():
            raise InvalidAuth
