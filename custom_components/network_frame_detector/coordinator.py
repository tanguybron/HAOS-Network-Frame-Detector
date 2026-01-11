"""Data coordinator for Network Frame Detector."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import EVENT_NETWORK_FRAME_DETECTED

_LOGGER = logging.getLogger(__name__)


class NetworkFrameDetectorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for managing network frame detection state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        sensor_duration: float,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{entry_id}_coordinator",
            update_interval=None,  # No periodic updates needed
        )
        self.entry_id = entry_id
        self.sensor_duration = timedelta(seconds=sensor_duration)
        self._last_detection_time: datetime | None = None
        self._sensor_state = False
        self._reset_task: Any = None

    @callback
    def on_detection(self) -> None:
        """
        Called when a frame is detected.
        Updates sensor state and fires event.
        """
        now = datetime.now()
        self._last_detection_time = now
        self._sensor_state = True

        # Fire event
        self.hass.bus.async_fire(
            EVENT_NETWORK_FRAME_DETECTED,
            {
                "entry_id": self.entry_id,
                "detection_time": now.isoformat(),
            },
        )

        # Schedule sensor state reset
        self._schedule_sensor_reset()

        # Notify listeners
        self.async_update_listeners()

    @callback
    def _schedule_sensor_reset(self) -> None:
        """Schedule sensor state to reset after duration."""
        # Cancel any existing reset task
        if self._reset_task:
            self._reset_task()

        # Schedule new reset using Home Assistant's async_call_later
        self._reset_task = async_call_later(
            self.hass,
            self.sensor_duration.total_seconds(),
            self._reset_sensor_state,
        )

    @callback
    def _reset_sensor_state(self, _now: datetime) -> None:
        """Reset sensor state to OFF."""
        self._sensor_state = False
        self._reset_task = None
        self.async_update_listeners()

    @property
    def is_on(self) -> bool:
        """Return current sensor state."""
        return self._sensor_state

    @property
    def last_detection(self) -> datetime | None:
        """Return last detection time."""
        return self._last_detection_time

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and cancel tasks."""
        if self._reset_task:
            self._reset_task()
            self._reset_task = None
        await super().async_shutdown()

