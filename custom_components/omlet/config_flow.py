from smartcoop.client import SmartCoopClient
from smartcoop.api.omlet import Omlet
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN


class OmletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            # Redirect to the appropriate step based on the user's choice
            return await self.async_step_api_key(user_input)

        # Show the form to enter API key
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("api_key"): str,  # Request the API key
                }
            ),
        )

    async def async_step_api_key(self, user_input: dict) -> FlowResult:
        """Step for setting up using API key."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")

            # Validate the API key
            try:
                client = SmartCoopClient(client_secret=api_key)  # Initialize the client
                omlet = Omlet(client)  # Access Omlet API to test the connection
                devices = await self.hass.async_add_executor_job(
                    omlet.get_devices
                )  # Fetch devices
                if not devices:
                    errors["base"] = (
                        "no_devices"  # Handle case where no devices are found
                    )
            except Exception as e:
                self.hass.logger.error(
                    f"Error authenticating with SmartCoopClient: {e}"
                )
                errors["base"] = "invalid_auth"  # Handle authentication errors
            else:
                # Create a new config entry and store the API key
                return self.async_create_entry(
                    title="Omlet Smart Coop",
                    data={"api_key": api_key},  # Save the API key in the config entry
                )

        # Show the form again with an error message
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("api_key"): str,
                }
            ),
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
