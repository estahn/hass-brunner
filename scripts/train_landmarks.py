#!/usr/bin/env python3
"""Seed screen landmark references into landmarks.npz.

Dev-only. Navigates to each screen that declares a landmark, captures it, and
stores the normalised landmark region keyed by screen name. The reader uses
these to confirm navigation landed on the right screen (taps are occasionally
dropped). Run from the repo root: python scripts/train_landmarks.py <host> [port]
"""

from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "brunner")
)
import enums as _enums  # noqa: E402
import regions as _regions  # noqa: E402
import vnc as _vnc  # noqa: E402


def _nav_capture(host, port, taps):
    for tap in taps:
        _vnc.tap_once(host, port, *tap, settle=1.0)
    fr = _vnc.capture_once(host, port)
    return Image.frombytes("RGB", (fr.width, fr.height), fr.rgb)


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: train_landmarks.py <host> [port]")
        sys.exit(2)
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5900

    refs: dict[str, np.ndarray] = {}
    for tap in ((230, 465), (40, 45)):
        _vnc.tap_once(host, port, *tap, settle=0.5)
    screens = list(_regions.SCREENS) + list(_regions.ENUM_SCREENS)
    for screen in screens:
        if screen.landmark is None:
            continue
        image = _nav_capture(host, port, screen.taps)
        refs[screen.name] = _enums.normalise_region(image, screen.landmark)
        print(f"seeded landmark for {screen.name}")
    out = "custom_components/brunner/landmarks.npz"
    np.savez_compressed(out, **refs)
    print(f"wrote {out} ({len(refs)} landmarks)")


if __name__ == "__main__":
    main()
