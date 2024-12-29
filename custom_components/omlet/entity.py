from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from .coordinator import OmletDataCoordinator
from .const import DOMAIN


class OmletBaseEntity(CoordinatorEntity):
    """Base entity for Omlet integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: OmletDataCoordinator, device: dict):
        """Initialize the base entity."""
        super().__init__(coordinator)
        self.device = device
        self.device_id = device["deviceId"]
        self.device_name = device["name"]

        # Define device info for linking in Home Assistant
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": self.device_name,
            "manufacturer": "Omlet",
            "model": device.get("deviceType", "Smart Coop"),
        }

    @property
    def available(self):
        """Return True if entity is available."""
        # Use coordinator availability and ensure data exists for this device
        return super().available and self.device_id in self.coordinator.data
