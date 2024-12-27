from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN
from omlet_sdk import OmletClient

class OmletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Redirect to the appropriate step based on the user's choice
            if user_input["setup_method"] == "email_password":
                return await self.async_step_email_password()
            if user_input["setup_method"] == "api_key":
                return await self.async_step_api_key()

        # Ask the user how they want to set up the integration
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("setup_method", default="email_password"): vol.In(
                        {"email_password": "Email and Password", "api_key": "API Key"}
                    )
                }
            ),
        )

    async def async_step_email_password(self, user_input: dict | None = None) -> FlowResult:
        """Step for setting up via email and password."""
        errors = {}

        if user_input is not None:
            email = user_input.get("email")
            password = user_input.get("password")

            # Validate credentials and generate API key
            try:
                client = OmletClient(email=email, password=password)
                api_key = await self.hass.async_add_executor_job(client.generate_api_key)
            except Exception:
                errors["base"] = "invalid_auth"
            else:
                # Create a new config entry
                return self.async_create_entry(
                    title="Omlet Integration",
                    data={"email": email, "password": password, "api_key": api_key},
                )

        # Show the form for email and password
        return self.async_show_form(
            step_id="email_password",
            data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_api_key(self, user_input: dict | None = None) -> FlowResult:
        """Step for setting up with an existing API key."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")

            # Validate the API key
            try:
                client = OmletClient(api_key=api_key)
                await self.hass.async_add_executor_job(client.validate_api_key)
            except Exception:
                errors["base"] = "invalid_api_key"
            else:
                # Create a new config entry
                return self.async_create_entry(
                    title="Omlet Integration",
                    data={"api_key": api_key},
                )

        # Show the form for API key
        return self.async_show_form(
            step_id="api_key",
            data_schema=vol.Schema({vol.Required("api_key"): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return OmletOptionsFlow(config_entry)


class OmletOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Omlet integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the integration options."""
        if user_input is not None:
            # Save options and exit
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    "polling_interval",
                    default=self.config_entry.options.get("polling_interval", 60),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)