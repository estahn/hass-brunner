#!/usr/bin/env python3
"""Seed whole-region enum templates into enum_templates.npz.

Dev-only. Each entry maps a field to the label of the state currently shown in a
capture. Because the heat pump is usually idle, this seeds the common states;
capture other states as they occur and add them here. Run from the repo root.
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

# (capture png, {field: label}) — the label is the state shown in that capture.
SEEDS = [
    (
        "scratch/bs.png",
        {
            "bwp_status": "standby",   # "1 STAND BY"
            "bwp_mode": "heating",     # "Heating"
            "bwp_defrost": "off",      # "Off"
        },
    ),
]

BOXES = {
    r.field: r.box for s in _regions.ENUM_SCREENS for r in s.regions
}


def main() -> None:
    templates: dict[str, np.ndarray] = {}
    for png, labels in SEEDS:
        if not os.path.exists(png):
            print(f"skip (missing): {png}")
            continue
        image = Image.open(png)
        for field, label in labels.items():
            box = BOXES[field]
            templates[f"{field}::{label}"] = _enums.normalise_region(image, box)
            print(f"seeded {field}::{label} from {png}")
    out = "custom_components/brunner/enum_templates.npz"
    np.savez_compressed(out, **templates)
    print(f"wrote {out} ({len(templates)} templates)")


if __name__ == "__main__":
    main()
