"""Screen navigation and value regions for the Brunner touchdisplay.

Coordinates are in the fixed 640x480 framebuffer. Each ``Screen`` is reached by
a sequence of taps from any state (tab along the bottom, then an icon along the
top, then any drill-in/scroll), and exposes a set of ``Region``s. A region is a
pixel box, a polarity (``invert=True`` for white-on-colour text such as the
buffer temperatures) and a scale applied to the parsed number.

Boxes were measured and verified against live captures (see
scripts/train_glyphs.py and docs/sensor-map.md). Small-font values (buffer
pressure) are lower-confidence than the medium/large value fonts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Region:
    key: str
    box: tuple[int, int, int, int]
    invert: bool = False
    scale: float = 1.0


@dataclass(frozen=True)
class Screen:
    name: str
    taps: tuple[tuple[int, int], ...]  # from any state, in order
    regions: tuple[Region, ...] = field(default_factory=tuple)


# Bottom tabs and common top icons (640x480)
TAB_EOS = (230, 465)
TAB_HEIZUNG = (300, 465)
TAB_BWP = (370, 465)

SCREENS: tuple[Screen, ...] = (
    Screen(
        "bwp_sensors",
        taps=(TAB_BWP, (118, 45)),
        regions=(
            Region("bwp_cop", (290, 122, 322, 140)),
            Region("bwp_flow_rate", (250, 150, 322, 168)),
            Region("bwp_flow_temp", (279, 179, 322, 196)),
            Region("bwp_return_temp", (279, 207, 322, 224)),
            Region("bwp_air_intake_temp", (282, 235, 322, 252)),
            Region("bwp_heating_power", (262, 264, 296, 282)),
            Region("bwp_pressure_high", (228, 293, 248, 309)),
            Region("bwp_pressure_low", (288, 293, 308, 309)),
        ),
    ),
    Screen(
        "system_overview",
        taps=(TAB_HEIZUNG, (40, 45)),
        regions=(
            Region("outdoor_temp", (278, 148, 315, 166)),
            Region("solar_pv_power", (66, 145, 102, 163)),
            Region("fireplace_power", (66, 250, 102, 268)),
            Region("buffer_top_temp", (263, 246, 293, 262), invert=True),
            Region("buffer_middle_temp", (263, 296, 293, 312), invert=True),
            Region("buffer_bottom_temp", (263, 345, 305, 362), invert=True),
            Region("buffer_pressure", (315, 405, 345, 421)),
        ),
    ),
    Screen(
        "heating_circuit_1",
        taps=(TAB_HEIZUNG, (360, 45), (228, 152), (45, 400)),
        regions=(
            Region("hk1_flow_set", (550, 142, 605, 165)),
            Region("hk1_flow_actual", (515, 204, 605, 227)),
            Region("hk1_return_actual", (515, 266, 605, 289)),
            Region("hk1_flow_rate", (525, 330, 590, 350)),
        ),
    ),
    Screen(
        "hot_water",
        taps=(TAB_HEIZUNG, (440, 45)),
        regions=(
            Region("dhw_set_temp", (272, 269, 302, 284)),
        ),
    ),
)
