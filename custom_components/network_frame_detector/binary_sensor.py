"""Binary sensor platform for Network Frame Detector."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NetworkFrameDetectorCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: NetworkFrameDetectorCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]["coordinator"]

    async_add_entities([NetworkFrameDetectorBinarySensor(coordinator, config_entry)])


class NetworkFrameDetectorBinarySensor(
    CoordinatorEntity[NetworkFrameDetectorCoordinator], BinarySensorEntity
):
    """Binary sensor representing network frame detection state."""

    def __init__(
        self,
        coordinator: NetworkFrameDetectorCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = config_entry.title
        self._attr_unique_id = config_entry.entry_id
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool:
        """Return True if frame was detected."""
        return self.coordinator.is_on

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return additional state attributes."""
        last_detection = self.coordinator.last_detection
        return {
            "last_detection": last_detection.isoformat() if last_detection else None,
        }

