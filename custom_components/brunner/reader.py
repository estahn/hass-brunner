"""Tie VNC capture, navigation and OCR together into a single poll.

Kept free of Home Assistant imports so it can be exercised standalone against a
live display (see scripts/poll_once.py).
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from PIL import Image

from .enums import EnumMatcher, landmark_matches, load_landmarks
from .ocr import GlyphOcr
from .regions import ENUM_SCREENS, SCREENS, EnumScreen, Screen
from .vnc import capture_once, tap_once

_LOGGER = logging.getLogger(__name__)

# Home baseline: tap Home on the EOS tab so every screen's tap sequence starts
# from a known place.
_HOME_TAPS = ((230, 465), (40, 45))


def _navigate_and_capture(host, port, taps, settle, landmark_box, landmarks, name):
    """Run a tap sequence and capture; if a landmark check fails, retry once."""
    for attempt in (1, 2):
        for tap in taps:
            tap_once(host, port, *tap, settle=settle)
        frame = capture_once(host, port)
        image = Image.frombytes("RGB", (frame.width, frame.height), frame.rgb)
        ref = landmarks.get(name)
        if landmark_box is None or ref is None:
            return image
        if landmark_matches(image, landmark_box, ref):
            return image
        _LOGGER.debug("Brunner: wrong screen for %s (attempt %d), retrying", name, attempt)
    _LOGGER.warning("Brunner: screen %s not confirmed after retry; values may be stale", name)
    return image


def read_all(
    host: str,
    port: int,
    ocr: GlyphOcr,
    enum_matcher: EnumMatcher | None = None,
    settle: float = 1.0,
    screens: tuple[Screen, ...] = SCREENS,
    enum_screens: tuple[EnumScreen, ...] = ENUM_SCREENS,
    on_screen: Callable[[str, Image.Image], None] | None = None,
) -> dict[str, object]:
    """Navigate every screen and read its regions, one tap per VNC connection.

    Returns a flat ``{sensor_key: value}`` dict (numbers, enum strings, and a
    derived ``bwp_running`` bool). Unreadable regions map to None.
    """
    landmarks = load_landmarks()
    values: dict[str, object] = {}
    for tap in _HOME_TAPS:
        tap_once(host, port, *tap, settle=0.5)
    for screen in screens:
        image = _navigate_and_capture(
            host, port, screen.taps, settle, screen.landmark, landmarks, screen.name
        )
        if on_screen is not None:
            on_screen(screen.name, image)
        for region in screen.regions:
            num = ocr.read_number(image, region.box, region.invert)
            values[region.key] = (
                round(num * region.scale, 2) if num is not None else None
            )
        if enum_matcher is not None:
            for er in screen.enum_regions:
                values[er.key] = enum_matcher.match(image, er.box, er.field)
    if enum_matcher is not None:
        for screen in enum_screens:
            image = _navigate_and_capture(
                host, port, screen.taps, settle, screen.landmark, landmarks, screen.name
            )
            if on_screen is not None:
                on_screen(screen.name, image)
            for region in screen.regions:
                values[region.key] = enum_matcher.match(image, region.box, region.field)
    # Derived: the heat pump is running when it moves water / makes heat. This is
    # more reliable than OCR'ing the tiny fan/compressor pills.
    flow_rate = values.get("bwp_flow_rate")
    heat_power = values.get("bwp_heating_power")
    if isinstance(flow_rate, (int, float)) or isinstance(heat_power, (int, float)):
        values["bwp_running"] = bool((flow_rate or 0) > 0 or (heat_power or 0) > 0)
    else:
        values["bwp_running"] = None
    # Return the panel to a neutral Home screen for the local user.
    for tap in _HOME_TAPS:
        tap_once(host, port, *tap, settle=0.3)
    return values
