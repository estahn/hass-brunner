"""Data update coordinator for Brunner Heating.

Strategy (see docs/sensor-map.md): the touchdisplay exposes only pixels over
VNC, so each poll navigates to the relevant screens, captures the framebuffer,
and OCRs fixed regions into values. This module currently provides the capture
loop; per-screen region OCR is filled in during the poller build.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .vnc import BrunnerVnc, BrunnerVncError

_LOGGER = logging.getLogger(__name__)


class BrunnerCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Polls the Brunner touchdisplay over VNC and exposes parsed values."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._host: str = entry.data[CONF_HOST]
        self._port: int = entry.data.get(CONF_PORT, 5900)
        interval = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            name="Brunner Heating",
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> dict[str, object]:
        return await self.hass.async_add_executor_job(self._poll)

    def _poll(self) -> dict[str, object]:
        """Blocking poll: capture screens and OCR them into a flat dict.

        TODO(poller build): navigate Home -> each screen, capture, and run
        region OCR per docs/sensor-map.md. For now this only proves liveness.
        """
        try:
            with BrunnerVnc(self._host, self._port) as vnc:
                frame = vnc.capture()
        except BrunnerVncError as err:
            raise UpdateFailed(f"Brunner display unreachable: {err}") from err

        return {
            "display_name": vnc.name,
            "frame_width": frame.width,
            "frame_height": frame.height,
        }
