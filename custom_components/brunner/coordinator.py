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
from .enums import EnumMatcher
from .ocr import GlyphOcr
from .reader import read_all
from .vnc import BrunnerVncError

_LOGGER = logging.getLogger(__name__)


class BrunnerCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Polls the Brunner touchdisplay over VNC and exposes parsed values."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._host: str = entry.data[CONF_HOST]
        self._port: int = entry.data.get(CONF_PORT, 5900)
        interval = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        self._ocr: GlyphOcr | None = None
        self._enums: EnumMatcher | None = None
        super().__init__(
            hass,
            _LOGGER,
            name="Brunner Heating",
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> dict[str, object]:
        return await self.hass.async_add_executor_job(self._poll)

    def _poll(self) -> dict[str, object]:
        """Blocking poll: navigate each screen, capture and OCR its regions.

        One tap per VNC connection (the display drops taps batched over a single
        session). Takes over the local panel for the duration, so poll gently.
        """
        if self._ocr is None:
            self._ocr = GlyphOcr.load()
        if self._enums is None:
            self._enums = EnumMatcher.load()
        try:
            return read_all(self._host, self._port, self._ocr, self._enums)
        except BrunnerVncError as err:
            raise UpdateFailed(f"Brunner display unreachable: {err}") from err
