"""Network Frame Detector integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import NetworkFrameDetectorCoordinator
from .listener import SecureNetworkListener

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Network Frame Detector from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config = entry.data

    # Create coordinator
    coordinator = NetworkFrameDetectorCoordinator(
        hass,
        entry.entry_id,
        config.get("sensor_duration", 30),
    )

    # Create listener
    listener = SecureNetworkListener(
        hass,
        config,
        coordinator.on_detection,
    )

    # Start listener
    try:
        await listener.start()
    except Exception as e:
        _LOGGER.error("Failed to start network listener: %s", e)
        return False

    # Store coordinator and listener
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "listener": listener,
    }

    # Forward setup to binary sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if entry.entry_id in hass.data[DOMAIN]:
        # Stop listener
        listener = hass.data[DOMAIN][entry.entry_id]["listener"]
        await listener.stop()

        # Shutdown coordinator
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        await coordinator.async_shutdown()

        # Remove from data
        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok

