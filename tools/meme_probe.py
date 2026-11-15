# -*- coding: utf-8 -*-
"""Probe the meme sticker: ink density map + colour stats, to find where the
speech bubble ends and the character begins."""
import os
import sys
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, ".work", "meme_src.jpg")


def main():
    im = Image.open(SRC).convert("RGB")
    w, h = im.size
    print("size", w, h)
    a = np.asarray(im).astype(np.int16)

    # ink = distance from white background
    dist = 255 - a.min(axis=2)
    ink = (dist > 28)

    # coarse map: 48 columns x 32 rows
    cols, rows = 48, 32
    cw, ch = w / cols, h / rows
    glyphs = " .:-=+*#%@"
    print("ink density map (each cell = %.0fx%.0f px):" % (cw, ch))
    for r in range(rows):
        line = []
        for c in range(cols):
            block = ink[int(r * ch):int((r + 1) * ch), int(c * cw):int((c + 1) * cw)]
            frac = block.mean() if block.size else 0.0
            line.append(glyphs[min(9, int(frac * 10))])
        print("%4d %s" % (int(r * ch), "".join(line)))

    # per-row ink profile in the left half vs right half, to spot the bubble band
    left = ink[:, : w // 2]
    right = ink[:, w // 2 :]
    print("\nrows where left half has ink and right half is nearly empty (bubble-only band):")
    bands = []
    run = None
    for y in range(h):
        l = left[y].mean()
        rr = right[y].mean()
        solo = l > 0.02 and rr < 0.005
        if solo and run is None:
            run = y
        elif not solo and run is not None:
            if y - run > 3:
                bands.append((run, y))
            run = None
    if run is not None:
        bands.append((run, h))
    for b in bands:
        print("  y %d..%d (%d px)" % (b[0], b[1], b[1] - b[0]))

    # bounding box of the darkest navy stroke colour (bubble outline + eyes)
    navy = (a[:, :, 2] > a[:, :, 0] + 10) & (a.max(axis=2) < 130)
    ys, xs = np.nonzero(navy)
    if len(xs):
        print("\ndark-navy pixels: %d, bbox x %d..%d y %d..%d" % (len(xs), xs.min(), xs.max(), ys.min(), ys.max()))

    # corner colours (background check)
    for name, (x, y) in {"TL": (2, 2), "TR": (w - 3, 2), "BL": (2, h - 3), "BR": (w - 3, h - 3), "C": (w // 2, h // 2)}.items():
        print("corner %s = %s" % (name, tuple(int(v) for v in a[y, x])))


if __name__ == "__main__":
    sys.exit(main())
