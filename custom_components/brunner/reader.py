"""Tie VNC capture, navigation and OCR together into a single poll.

Kept free of Home Assistant imports so it can be exercised standalone against a
live display (see scripts/poll_once.py).
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from PIL import Image

from .ocr import GlyphOcr
from .regions import SCREENS, Screen
from .vnc import capture_once, tap_once

_LOGGER = logging.getLogger(__name__)

# Home baseline: tap Home on the EOS tab so every screen's tap sequence starts
# from a known place.
_HOME_TAPS = ((230, 465), (40, 45))


def read_all(
    host: str,
    port: int,
    ocr: GlyphOcr,
    settle: float = 1.0,
    screens: tuple[Screen, ...] = SCREENS,
    on_screen: Callable[[str, Image.Image], None] | None = None,
) -> dict[str, float | None]:
    """Navigate every screen and OCR its regions, one tap per VNC connection.

    Returns a flat ``{sensor_key: value}`` dict. Unreadable regions map to None.
    """
    values: dict[str, float | None] = {}
    for tap in _HOME_TAPS:
        tap_once(host, port, *tap, settle=0.5)
    for screen in screens:
        for tap in screen.taps:
            tap_once(host, port, *tap, settle=settle)
        frame = capture_once(host, port)
        image = Image.frombytes("RGB", (frame.width, frame.height), frame.rgb)
        if on_screen is not None:
            on_screen(screen.name, image)
        for region in screen.regions:
            num = ocr.read_number(image, region.box, region.invert)
            values[region.key] = (
                round(num * region.scale, 2) if num is not None else None
            )
    # Return the panel to a neutral Home screen for the local user.
    for tap in _HOME_TAPS:
        tap_once(host, port, *tap, settle=0.3)
    return values
