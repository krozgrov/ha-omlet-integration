from homeassistant.components.cover import CoverEntity
from .const import DOMAIN
from homeassistant.helpers import entity_registry as er
from .entity import OmletEntity
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the covers from the config entry.

    Args:
        hass: Home Assistant instance
        config_entry: The config entry
        async_add_entities: Callback to register entities
    """
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    ent_reg = er.async_get(hass)

    _LOGGER.debug("Setting up covers for devices: %s", coordinator.data)

    covers = []
    door_action_values = {"open", "close"}
    for device_id, device_data in coordinator.data.items():
        # Door Cover
        door_state = device_data.get("state", {}).get("door")
        if door_state:
            has_door_actions = any(
                (action.get("actionValue") or "").lower() in door_action_values
                for action in device_data.get("actions", []) or []
            )
            if has_door_actions:
                door_unique_id = f"{device_id}_door"
                existing = ent_reg.async_get_entity_id("cover", DOMAIN, door_unique_id)
                if not (existing and existing in hass.states):
                    covers.append(
                        OmletDoorCover(
                            coordinator,
                            device_id,
                            device_data["name"],
                        )
                    )

        # Feeder Cover
        feeder_state = device_data.get("state", {}).get("feeder")
        if feeder_state:
            has_feeder_actions = any(
                (action.get("actionValue") or "").lower() in door_action_values
                for action in device_data.get("actions", []) or []
            )
            if has_feeder_actions:
                feeder_unique_id = f"{device_id}_feeder"
                existing = ent_reg.async_get_entity_id("cover", DOMAIN, feeder_unique_id)
                if not (existing and existing in hass.states):
                    covers.append(
                        OmletFeederCover(
                            coordinator,
                            device_id,
                            device_data["name"],
                        )
                    )

    async_add_entities(covers)


class OmletDoorCover(OmletEntity, CoverEntity):
    """Representation of a cover for the Omlet door."""

    def __init__(self, coordinator, device_id, device_name):
        """Initialize the cover.

        Args:
            coordinator: The data coordinator
            device_id: The device identifier
            device_name: The name of the device
        """
        super().__init__(coordinator, device_id)
        self._attr_translation_key = "door"
        # Stable unique_id not tied to names
        self._attr_unique_id = f"{device_id}_door"
        self._attr_has_entity_name = True

    @property
    def available(self):
        """Return if entity is available.

        Returns:
            bool: True if available, False otherwise
        """
        device_data = self.coordinator.data.get(self.device_id, {})
        state = device_data["state"]["door"]["state"]
        # Only unavailable during "stopping"
        return state != "stopping"

    @property
    def is_opening(self):
        """Return if the door is in the process of opening.

        Returns:
            bool: True if opening, False otherwise
        """
        device_data = self.coordinator.data.get(self.device_id, {})
        state = device_data["state"]["door"]["state"]
        return state == "openpending"

    @property
    def is_closing(self):
        """Return if the door is in the process of closing.

        Returns:
            bool: True if closing, False otherwise
        """
        device_data = self.coordinator.data.get(self.device_id, {})
        state = device_data["state"]["door"]["state"]
        return state == "closepending"

    @property
    def is_closed(self):
        """Return if the door is fully closed.

        Returns:
            bool: True if closed, False otherwise
        """
        device_data = self.coordinator.data.get(self.device_id, {})
        state = device_data["state"]["door"]["state"]
        return state == "closed"

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self._execute_action("open")
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await self._execute_action("close")
        await self.coordinator.async_request_refresh()

    async def _execute_action(self, action):
        """Execute an action on the device.

        Args:
            action: The action to execute (open/close)
        """
        device_data = self.coordinator.data.get(self.device_id, {})
        action = (action or "").lower()
        action_url = next(
            (
                a["url"]
                for a in device_data["actions"]
                if (a.get("actionValue") or "").lower() == action
            ),
            None,
        )
        if action_url:
            await self.coordinator.api_client.execute_action(action_url)


class OmletFeederCover(OmletEntity, CoverEntity):
    """Representation of a cover for the Omlet feeder."""

    def __init__(self, coordinator, device_id, device_name):
        """Initialize the cover."""
        super().__init__(coordinator, device_id)
        self._attr_translation_key = "feeder"
        self._attr_unique_id = f"{device_id}_feeder"
        self._attr_has_entity_name = True

    @property
    def available(self):
        """Return if entity is available."""
        device_data = self.coordinator.data.get(self.device_id, {}) or {}
        state = ((device_data.get("state") or {}).get("feeder") or {}).get("state", "")
        return str(state).lower() != "stopping"

    @property
    def is_opening(self):
        """Return if the feeder is opening."""
        device_data = self.coordinator.data.get(self.device_id, {}) or {}
        state = ((device_data.get("state") or {}).get("feeder") or {}).get("state", "")
        return str(state).lower() in {"openpending", "opening"}

    @property
    def is_closing(self):
        """Return if the feeder is closing."""
        device_data = self.coordinator.data.get(self.device_id, {}) or {}
        state = ((device_data.get("state") or {}).get("feeder") or {}).get("state", "")
        return str(state).lower() in {"closepending", "closing"}

    @property
    def is_closed(self):
        """Return if the feeder is fully closed."""
        device_data = self.coordinator.data.get(self.device_id, {}) or {}
        state = ((device_data.get("state") or {}).get("feeder") or {}).get("state", "")
        return str(state).lower() == "closed"

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self._execute_action("open")
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await self._execute_action("close")
        await self.coordinator.async_request_refresh()

    async def _execute_action(self, action):
        """Execute an action on the device."""
        device_data = self.coordinator.data.get(self.device_id, {}) or {}
        action = (action or "").lower()
        action_url = next(
            (
                a.get("url")
                for a in device_data.get("actions", []) or []
                if (a.get("actionValue") or "").lower() == action
            ),
            None,
        )
        if action_url:
            await self.coordinator.api_client.execute_action(action_url)
