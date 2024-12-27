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
            # Use the client_secret directly for setup
            return await self.async_step_client_secret(user_input)

        # Ask the user for the client_secret
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("client_secret"): str,  # Request the client_secret
                }
            ),
        )

    async def async_step_client_secret(self, user_input: dict) -> FlowResult:
        """Step for setting up using client_secret."""
        errors = {}

        if user_input is not None:
            client_secret = user_input.get("client_secret")

            # Validate the client_secret
            try:
                client = SmartCoopClient(
                    client_secret=client_secret
                )  # Initialize the client
                omlet = Omlet(client)  # Access Omlet API to test the connection
                devices = await self.hass.async_add_executor_job(
                    omlet.get_devices
                )  # Example API call
                if not devices:
                    errors["base"] = "no_devices"
            except Exception as e:
                self.hass.logger.error(
                    f"Error authenticating with SmartCoopClient: {e}"
                )
                errors["base"] = "invalid_auth"
            else:
                # Create a new config entry
                return self.async_create_entry(
                    title="Omlet Smart Coop",
                    data={"client_secret": client_secret},
                )

        # Show the form again with an error message
        return self.async_show_form(
            step_id="client_secret",
            data_schema=vol.Schema(
                {
                    vol.Required("client_secret"): str,
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