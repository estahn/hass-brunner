#!/usr/bin/env python3
"""Run one full navigation+OCR poll against a live Brunner touchdisplay.

Usage: python scripts/poll_once.py <host> [port]
Standalone (no Home Assistant). Optionally dumps each visited screen to scratch/.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "brunner")
)
import ocr as _ocr  # noqa: E402
import regions as _regions  # noqa: E402
import vnc as _vnc  # noqa: E402

# reader.py uses relative imports; replicate its logic here without the package.
from PIL import Image  # noqa: E402


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.178.124"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5900
    dump = "--dump" in sys.argv
    O = _ocr.GlyphOcr.load(
        os.path.join(
            os.path.dirname(__file__), "..", "custom_components", "brunner", "glyphs.npz"
        )
    )
    values: dict[str, object] = {}
    for tap in ((230, 465), (40, 45)):
        _vnc.tap_once(host, port, *tap, settle=0.5)
    for screen in _regions.SCREENS:
        for tap in screen.taps:
            _vnc.tap_once(host, port, *tap, settle=1.0)
        fr = _vnc.capture_once(host, port)
        im = Image.frombytes("RGB", (fr.width, fr.height), fr.rgb)
        if dump:
            im.save(f"scratch/poll_{screen.name}.png")
        for r in screen.regions:
            values[r.key] = O.read_number(im, r.box, r.invert)
    for tap in ((230, 465), (40, 45)):
        _vnc.tap_once(host, port, *tap, settle=0.3)
    width = max(len(k) for k in values)
    for k, val in values.items():
        print(f"  {k:<{width}}  {val}")


if __name__ == "__main__":
    main()
