"""Whole-region template matching for text enum values.

The status/mode/defrost fields are short words in the fixed GUI font (e.g.
``Heating``, ``1 STAND BY``, ``Off``). Rather than full letter OCR, each known
state is stored as one small normalised image of its region; a live region is
matched to the nearest stored state by mean-squared difference, with a threshold
below which it returns None ("unknown state — not yet seen").

Because the UI is static, the same state renders to near-identical pixels, so
matching is reliable for seeded states. New states are added by capturing them
with scripts/train_enums.py — see docs/sensor-map.md for the open states. Needs
only Pillow + numpy.
"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image

ENUM_H = 28
ENUM_W = 190
# Max mean-squared pixel difference (greyscale [0,1]) to accept a match. Same-
# state captures differ only by anti-aliasing noise, so this can be strict.
MATCH_THRESHOLD = 0.02


def normalise_region(image: Image.Image, box: tuple[int, int, int, int]) -> np.ndarray:
    """Greyscale, contrast-stretch and resize a region to the enum grid."""
    crop = image.crop(box).convert("L")
    arr = np.asarray(crop, dtype=np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi > lo:
        arr = (arr - lo) / (hi - lo)
    else:
        arr = np.zeros_like(arr)
    img = Image.fromarray((arr * 255).astype(np.uint8)).resize(
        (ENUM_W, ENUM_H), Image.BILINEAR
    )
    return np.asarray(img, dtype=np.float32) / 255.0


class EnumMatcher:
    """Matches enum regions to the nearest seeded state label."""

    def __init__(self, templates: dict[str, np.ndarray]) -> None:
        # keys are "<field>::<label>"
        self._by_field: dict[str, list[tuple[str, np.ndarray]]] = {}
        for key, tpl in templates.items():
            field, label = key.split("::", 1)
            self._by_field.setdefault(field, []).append((label, tpl))

    @classmethod
    def load(cls, path: str | None = None) -> "EnumMatcher":
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "enum_templates.npz")
        if not os.path.exists(path):
            return cls({})
        data = np.load(path)
        return cls({k: data[k].astype(np.float32) for k in data.files})

    def match(
        self,
        image: Image.Image,
        box: tuple[int, int, int, int],
        field: str,
        threshold: float = MATCH_THRESHOLD,
    ) -> str | None:
        candidates = self._by_field.get(field)
        if not candidates:
            return None
        norm = normalise_region(image, box)
        best_label: str | None = None
        best_dist = float("inf")
        for label, tpl in candidates:
            dist = float(np.mean((tpl - norm) ** 2))
            if dist < best_dist:
                best_dist = dist
                best_label = label
        return best_label if best_dist <= threshold else None


# --- Screen landmark verification -------------------------------------------
# A navigation tap is occasionally dropped, leaving the wrong screen showing.
# Each screen has a static label region; comparing it to a seeded reference
# confirms the screen before its values are trusted.
LANDMARK_THRESHOLD = 0.04


def load_landmarks(path: str | None = None) -> dict[str, np.ndarray]:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "landmarks.npz")
    if not os.path.exists(path):
        return {}
    data = np.load(path)
    return {k: data[k].astype(np.float32) for k in data.files}


def landmark_matches(
    image: Image.Image,
    box: tuple[int, int, int, int],
    reference: np.ndarray,
    threshold: float = LANDMARK_THRESHOLD,
) -> bool:
    dist = float(np.mean((reference - normalise_region(image, box)) ** 2))
    return dist <= threshold
