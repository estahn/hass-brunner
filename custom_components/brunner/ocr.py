"""Pure-Python OCR for the Brunner touchdisplay's fixed GUI font.

The display renders values in one consistent sans-serif font at a few sizes,
always as short numeric strings (e.g. ``24``, ``0,0``, ``35,3``, ``-4``,
``1000``). Shipping Tesseract inside Home Assistant is awkward (it needs a
system binary), so this module reads those strings with nothing but Pillow and
numpy — both already present in Home Assistant.

How it works:

1. The value region is cropped and thresholded to ink/background (polarity is
   given per region, since some values are dark-on-light and some, like the
   buffer temperatures, are white-on-colour).
2. Ink is segmented into glyphs by vertical projection (gaps between columns).
3. Tiny low glyphs become a decimal separator; short wide centred glyphs become
   a minus sign; everything else is height-normalised and matched against
   bundled digit templates by nearest sum-of-squared-difference.

Templates live in ``glyphs.npz`` next to this file and are produced by
``scripts/train_glyphs.py`` from live captures. The matcher is deliberately
scoped to numbers: units and labels are known from the region definition, so
they are never OCR'd.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
from PIL import Image

GLYPH_H = 24
GLYPH_W = 16
_INK_THRESHOLD = 0.35  # fraction of a column that must be ink to count as a stroke


@dataclass
class _Glyph:
    x0: int
    x1: int
    y0: int  # top of the ink within the line
    bitmap: np.ndarray  # bool, row+col tight ink bbox


class GlyphOcr:
    """Reads numeric strings from screen regions using bundled templates."""

    def __init__(self, templates: dict[str, np.ndarray]) -> None:
        # templates: char -> float32 [GLYPH_H, GLYPH_W] in [0,1]
        self._chars = list(templates.keys())
        self._stack = (
            np.stack([templates[c] for c in self._chars]) if templates else None
        )

    @classmethod
    def load(cls, path: str | None = None) -> "GlyphOcr":
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "glyphs.npz")
        data = np.load(path)
        return cls({k: data[k].astype(np.float32) for k in data.files})

    # -- public --------------------------------------------------------------
    def read_number(
        self, image: Image.Image, box: tuple[int, int, int, int], invert: bool = False
    ) -> float | None:
        """Return the numeric value in ``box`` (``image`` is a full frame)."""
        text = self.read_text(image, box, invert)
        return parse_number(text)

    def read_text(
        self, image: Image.Image, box: tuple[int, int, int, int], invert: bool = False
    ) -> str:
        """Return the first whitespace-delimited number token in ``box``.

        Values are rendered as ``<number> <unit>`` (e.g. ``43 °C``), so the
        unit is dropped by splitting glyphs into words on wide gaps and keeping
        the first word that contains a digit.
        """
        binary = self._binarise(image.crop(box), invert)
        glyphs = _segment(binary)
        if not glyphs:
            return ""
        line_h = binary.shape[0]
        # Reference glyph height = tallest glyph (the digits); decimals/minus are
        # judged small relative to it, independent of box padding or font size.
        ref_h = max(g.bitmap.shape[0] for g in glyphs)
        gap_limit = max(4.0, ref_h * 0.6)
        current: list[str] = []
        prev_x1: int | None = None

        def flush() -> str | None:
            token = "".join(current)
            return token if any(c.isdigit() for c in token) else None

        for g in glyphs:
            if prev_x1 is not None and (g.x0 - prev_x1) > gap_limit:
                done = flush()
                if done is not None:
                    return done
                current = []
            current.append(self._classify(g, ref_h))
            prev_x1 = g.x1
        done = flush()
        return done if done is not None else ""

    # -- internals -----------------------------------------------------------
    @staticmethod
    def _binarise(crop: Image.Image, invert: bool) -> np.ndarray:
        arr = np.asarray(crop.convert("L"), dtype=np.float32)
        # Otsu-ish: midpoint between min and max is plenty for this UI.
        thr = (arr.min() + arr.max()) / 2.0
        ink = arr < thr  # dark is ink
        if invert:
            ink = ~ink
        return ink

    def _classify(self, g: _Glyph, ref_h: int) -> str:
        bh = g.bitmap.shape[0]
        gw = g.bitmap.shape[1]
        # decimal separator: a small dot/comma, much shorter and narrower than a digit
        if bh <= ref_h * 0.5 and gw <= ref_h * 0.5:
            return "."
        # minus sign: short but clearly wider than tall
        if bh <= ref_h * 0.4 and gw >= bh * 1.5:
            return "-"
        # '1' is a full-height but distinctly narrow stroke; template SSD alone
        # confuses it with '3' at tiny sizes, so recognise it by shape here.
        if bh >= ref_h * 0.7 and gw <= ref_h * 0.45:
            return "1"
        if self._stack is None:
            return "?"
        norm = _normalise(g.bitmap)
        diffs = ((self._stack - norm) ** 2).sum(axis=(1, 2))
        return self._chars[int(diffs.argmin())]


def _segment(ink: np.ndarray) -> list[_Glyph]:
    """Split a binary line into glyphs by columns of whitespace."""
    cols = ink.sum(axis=0)
    h = ink.shape[0]
    active = cols > max(1, h * 0.04)
    glyphs: list[_Glyph] = []
    x = 0
    n = len(active)
    while x < n:
        if not active[x]:
            x += 1
            continue
        x0 = x
        while x < n and active[x]:
            x += 1
        x1 = x
        sub = ink[:, x0:x1]
        rows = np.where(sub.any(axis=1))[0]
        if rows.size == 0:
            continue
        cols = np.where(sub.any(axis=0))[0]
        tight = sub[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]
        glyphs.append(_Glyph(x0 + int(cols.min()), x0 + int(cols.max()) + 1,
                             int(rows.min()), tight))
    return glyphs


def _normalise(bitmap: np.ndarray) -> np.ndarray:
    """Scale a tight ink bbox to the template grid, preserving aspect ratio.

    Height is fixed to GLYPH_H and width scaled proportionally (capped at
    GLYPH_W) then centred — so a narrow '1' stays narrow and is not confused
    with a full-width digit. The result is binarised to sharpen matching. The
    trainer must use this exact function so templates and queries align.
    """
    h, w = bitmap.shape
    if h == 0 or w == 0:
        return np.zeros((GLYPH_H, GLYPH_W), dtype=np.float32)
    scale = GLYPH_H / h
    new_w = max(1, min(GLYPH_W, int(round(w * scale))))
    img = Image.fromarray((bitmap * 255).astype(np.uint8)).resize(
        (new_w, GLYPH_H), Image.BILINEAR
    )
    arr = np.asarray(img, dtype=np.float32) / 255.0
    canvas = np.zeros((GLYPH_H, GLYPH_W), dtype=np.float32)
    x0 = (GLYPH_W - new_w) // 2
    canvas[:, x0 : x0 + new_w] = arr
    # Keep the anti-aliased greyscale (not binarised): the soft edges carry the
    # detail that separates 0/3/9 at small sizes.
    return canvas


def parse_number(text: str) -> float | None:
    """Parse the display's number format (German comma, stray spaces)."""
    if not text:
        return None
    cleaned = text.replace(",", ".").replace(" ", "")
    # keep only number-ish characters
    buf = []
    for ch in cleaned:
        if ch.isdigit() or ch in ".-":
            buf.append(ch)
    cleaned = "".join(buf)
    if cleaned in ("", "-", ".", "-."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        # collapse accidental multiple dots (keep first)
        first = cleaned.find(".")
        if first != -1:
            cleaned = cleaned[: first + 1] + cleaned[first + 1 :].replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
