"""Offline OCR regression tests — no hardware, no Home Assistant.

Reads known values from the committed reference screenshots in docs/screens/ to
guard the bundled digit templates (glyphs.npz) against regressions. Imports the
ocr module directly, so it needs only Pillow + numpy.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
_OCR_PATH = os.path.join(ROOT, "custom_components", "brunner", "ocr.py")
_GLYPHS = os.path.join(ROOT, "custom_components", "brunner", "glyphs.npz")
_SCREENS = os.path.join(ROOT, "docs", "screens")

_spec = importlib.util.spec_from_file_location("brunner_ocr_test", _OCR_PATH)
ocr = importlib.util.module_from_spec(_spec)
import sys

sys.modules[_spec.name] = ocr  # let dataclasses resolve the module
_spec.loader.exec_module(ocr)

Image = pytest.importorskip("PIL.Image")


# (screenshot, box, invert, expected)
CASES = [
    ("heating-circuit-1b.png", (550, 142, 605, 165), False, 43.0),
    ("heating-circuit-1b.png", (525, 330, 590, 350), False, 25.6),
    ("system-overview.png", (263, 246, 293, 262), True, 55.0),
    ("system-overview.png", (263, 296, 293, 312), True, 35.0),
    ("system-overview.png", (263, 345, 305, 362), True, 34.0),
    ("system-overview.png", (66, 145, 102, 163), False, 0.0),
    ("system-overview.png", (66, 250, 102, 268), False, 4.5),
    ("system-overview.png", (315, 405, 345, 421), False, 1.5),
    ("bwp-sensors.png", (290, 122, 322, 140), False, 0.0),
    ("bwp-sensors.png", (228, 293, 248, 309), False, 6.0),
    ("bwp-sensors.png", (288, 293, 308, 309), False, 3.0),
    ("hotwater-a.png", (272, 269, 302, 284), False, 50.0),
    # Wood stove combustion chamber (large font)
    ("brunner-eos.png", (249, 145, 345, 180), False, 246.0),
    ("eos-stove.png", (249, 145, 345, 180), False, 151.0),
    ("eos-stove.png", (28, 360, 120, 380), False, 40.1),
]


@pytest.fixture(scope="module")
def reader():
    return ocr.GlyphOcr.load(_GLYPHS)


@pytest.mark.parametrize("screenshot,box,invert,expected", CASES)
def test_reads_known_value(reader, screenshot, box, invert, expected):
    image = Image.open(os.path.join(_SCREENS, screenshot))
    assert reader.read_number(image, box, invert) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("0.0", 0.0),
        ("35,3", 35.3),
        ("-4", -4.0),
        ("1000", 1000.0),
        ("", None),
        ("--", None),
    ],
)
def test_parse_number(text, expected):
    assert ocr.parse_number(text) == expected
