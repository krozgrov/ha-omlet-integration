from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol
from homeassistant.core import callback
import hashlib
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_POLLING_INTERVAL,
    CONF_DEFAULT_POLLING_INTERVAL,
    CONF_ENABLE_WEBHOOKS,
    CONF_WEBHOOK_TOKEN,
    CONF_DISABLE_POLLING,
)
from .api_client import OmletApiClient

import logging

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

    pass


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid authentication."""

    pass


async def validate_api_key(api_key: str):
    """Validate the API key.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if validation succeeds

    Raises:
        InvalidAuth: If the API key is invalid
    """
    client = OmletApiClient(api_key)
    if not await client.is_valid():
        raise InvalidAuth
    return True


@config_entries.HANDLERS.register(DOMAIN)
class OmletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet Smart Coop."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step.

        Args:
            user_input: Dictionary of user input

        Returns:
            The next step in the flow
        """
        errors = {}
        if user_input is not None:
            try:
                await validate_api_key(user_input[CONF_API_KEY])
            except InvalidAuth:
                errors[CONF_API_KEY] = "invalid_auth"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception during setup: %s", ex)
                errors["base"] = "unknown"

            if not errors:
                # Prevent duplicate configuration: derive a deterministic unique_id
                api_key_hash = hashlib.sha256(user_input[CONF_API_KEY].encode()).hexdigest()
                await self.async_set_unique_id(api_key_hash)
                self._abort_if_unique_id_configured()
                # Create a new configuration entry
                return self.async_create_entry(
                    title="Omlet Smart Coop",
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_POLLING_INTERVAL: user_input.get(
                            CONF_POLLING_INTERVAL, CONF_DEFAULT_POLLING_INTERVAL
                        ),
                    },
                )

        # Display the setup form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_POLLING_INTERVAL, default=CONF_DEFAULT_POLLING_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow.

        Args:
            config_entry: The config entry to get options for

        Returns:
            The options flow handler
        """
        return OmletOptionsFlowHandler(config_entry)


class OmletOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Omlet Smart Coop."""

    def __init__(self, config_entry):
        """Initialize options flow.

        Args:
            config_entry: The config entry being configured
        """
        self.config_entry_id = config_entry.entry_id  # Store only the entry ID

    async def async_step_init(self, user_input=None):
        """Manage the options.

        Args:
            user_input: Dictionary of user input

        Returns:
            The next step in the flow
        """
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle user options.

        Args:
            user_input: Dictionary of user input

        Returns:
            The next step in the flow
        """
        errors = {}

        # Retrieve the config entry dynamically
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)

        if user_input is not None:
            try:
                # Validate polling interval or other options if necessary
                polling_interval = user_input[CONF_POLLING_INTERVAL]
                if not (60 <= polling_interval <= 86400):
                    raise ValueError("Polling interval out of range")
            except ValueError:
                errors[CONF_POLLING_INTERVAL] = "invalid_polling_interval"

            if not errors:
                # Save updated options
                return self.async_create_entry(title="", data=user_input)

        # Default values for the form
        current_interval = config_entry.options.get(
            CONF_POLLING_INTERVAL, CONF_DEFAULT_POLLING_INTERVAL
        )

        # Display the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLLING_INTERVAL, default=current_interval
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
                    vol.Optional(CONF_ENABLE_WEBHOOKS, default=self._get_current_option(config_entry, CONF_ENABLE_WEBHOOKS, False)): bool,
                    vol.Optional(CONF_WEBHOOK_TOKEN, default=self._get_current_option(config_entry, CONF_WEBHOOK_TOKEN, "")): str,
                    vol.Optional(CONF_DISABLE_POLLING, default=self._get_current_option(config_entry, CONF_DISABLE_POLLING, False)): bool,
                }
            ),
            errors=errors,
        )

    def _get_current_option(self, config_entry, key, default):
        try:
            return config_entry.options.get(key, default)
        except Exception:
            return default
