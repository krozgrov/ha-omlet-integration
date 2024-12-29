from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


class OmletEntity(CoordinatorEntity):
    """Base class for Omlet entities."""

    def __init__(self, coordinator, device_id):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device_id = device_id
        device_data = coordinator.data[device_id]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=device_data["name"],
            manufacturer="Omlet",
            model="Autodoor",
            sw_version=device_data.get(
                "firmware_version", "Unknown"
            ),  # Dynamically linked firmware
        )

    @property
    def device_info(self):
        """Return updated device info."""
        device_data = self.coordinator.data[self.device_id]
        self._attr_device_info["sw_version"] = device_data.get(
            "firmware_version", "Unknown"
        )
        return self._attr_device_info
