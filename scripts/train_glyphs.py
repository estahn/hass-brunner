#!/usr/bin/env python3
"""Build digit templates for custom_components/brunner/glyphs.npz.

Dev-only tool. Uses Tesseract (per-character box mode) to LABEL glyphs harvested
from live screen captures, then stores height-normalised bitmaps that the
runtime matcher (custom_components/brunner/ocr.py) compares against. Tesseract is
therefore needed only to train; the shipped integration needs just Pillow+numpy.

Usage: run from the repo root inside the venv after capturing screens into
scratch/. Edit SAMPLES to point at regions whose digits you can read.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "brunner")
)
import ocr as _ocr  # noqa: E402  (standalone module, no HA imports)

GLYPH_H, GLYPH_W = _ocr.GLYPH_H, _ocr.GLYPH_W

# (png, box, invert) — regions rich in digits. Labels come from Tesseract.
SAMPLES = [
    ("scratch/bwp_sensors.png", (195, 120, 352, 320), False),
    ("scratch/sysov.png", (40, 135, 160, 400), False),      # left kW boxes
    ("scratch/sysov.png", (235, 240, 345, 390), True),       # buffer temps (white)
    ("scratch/sysov.png", (205, 400, 360, 420), False),      # 1000 l / 1,5 bar
    ("scratch/hc1b.png", (430, 140, 610, 350), False),       # HK1 right column
    ("scratch/eos_home.png", (40, 135, 170, 300), False),    # tile stove / boiler
    ("docs/screens/brunner-eos.png", (150, 120, 360, 400), False),  # 4,9 / 65 / 31,0
    ("docs/screens/heating-circuit-1a.png", (276, 205, 320, 226), False),  # 1,8
    ("docs/screens/heating-circuit-1a.png", (260, 328, 305, 350), False),  # 17
    # Clock + date strings are rich in 7/8/9 (weak digits). Colon is labelled
    # ':' by Tesseract and skipped.
    ("docs/screens/heating-circuit-1a.png", (474, 450, 600, 472), False),  # 17:39 ...
    ("scratch/bwp_sensors.png", (474, 452, 600, 472), False),  # 18:xx 09.11.2026
    ("scratch/poll_bwp_sensors.png", (275, 205, 322, 226), False),  # 19 -> 9
]


def binarise(crop: Image.Image, invert: bool) -> np.ndarray:
    arr = np.asarray(crop.convert("L"), dtype=np.float32)
    thr = (arr.min() + arr.max()) / 2.0
    ink = arr < thr
    if invert:
        ink = ~ink
    return ink


normalise = _ocr._normalise  # use the exact runtime normalisation


def char_boxes(crop: Image.Image) -> list[tuple[str, int, int, int, int]]:
    """Return Tesseract per-character boxes (char, x0, y0, x1, y1), top-left origin."""
    big = crop.resize((crop.width * 4, crop.height * 4), Image.LANCZOS)
    with tempfile.TemporaryDirectory() as d:
        png = os.path.join(d, "in.png")
        big.save(png)
        out = os.path.join(d, "out")
        # No whitelist: let Tesseract label unit letters as letters so we can
        # skip them. Forcing a digit whitelist mislabels °/C/k/W/l as digits
        # and poisons the templates.
        subprocess.run(
            ["tesseract", png, out, "--psm", "6",
             "-c", "tessedit_create_boxfile=1"],
            capture_output=True, check=False,
        )
        boxfile = out + ".box"
        if not os.path.exists(boxfile):
            return []
        H = big.height
        res = []
        for line in open(boxfile):
            parts = line.split()
            if len(parts) < 5:
                continue
            ch, x0, y0, x1, y1 = parts[0], *map(int, parts[1:5])
            # box coords are bottom-left origin, 4x scaled
            res.append((ch, x0 // 4, (H - y1) // 4, x1 // 4, (H - y0) // 4))
        return res


def main() -> None:
    samples: dict[str, list[np.ndarray]] = {}
    for png, box, invert in SAMPLES:
        if not os.path.exists(png):
            print(f"skip (missing): {png}")
            continue
        frame = Image.open(png)
        crop = frame.crop(box)
        ink = binarise(crop, invert)
        for ch, x0, y0, x1, y1 in char_boxes(crop):
            if ch not in "0123456789":
                continue
            sub = ink[max(0, y0):y1, max(0, x0):x1]
            rows = np.where(sub.any(axis=1))[0]
            colz = np.where(sub.any(axis=0))[0]
            if rows.size == 0 or colz.size == 0:
                continue
            tight = sub[rows.min():rows.max() + 1, colz.min():colz.max() + 1]
            samples.setdefault(ch, []).append(normalise(tight))

    templates: dict[str, np.ndarray] = {}
    for ch in "0123456789":
        if ch in samples:
            templates[ch] = np.mean(samples[ch], axis=0).astype(np.float32)
    have = "".join(sorted(templates))
    missing = "".join(c for c in "0123456789" if c not in templates)
    print(f"digits learned: {have!r}  counts=" +
          ", ".join(f"{c}:{len(samples[c])}" for c in sorted(samples)))
    if missing:
        print(f"!! MISSING digits: {missing!r}")

    out = "custom_components/brunner/glyphs.npz"
    np.savez_compressed(out, **templates)
    print(f"wrote {out} ({len(templates)} templates)")


if __name__ == "__main__":
    main()
