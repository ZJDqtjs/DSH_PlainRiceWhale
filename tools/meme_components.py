# -*- coding: utf-8 -*-
"""Connected-component analysis of the meme sticker.

Separates the speech bubble (outline + trail circles + baked-in text) from the
character body, so the builder can drop everything that is not the whale girl.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, ".work", "meme_src.jpg")


def ink_mask(a, thr=28):
    dist = 255 - a.min(axis=2)
    return np.asarray(dist > thr, dtype=np.uint8)


def dilate(mask, iters=2):
    out = mask.copy()
    for _ in range(iters):
        nxt = out.copy()
        nxt[1:, :] |= out[:-1, :]
        nxt[:-1, :] |= out[1:, :]
        nxt[:, 1:] |= out[:, :-1]
        nxt[:, :-1] |= out[:, 1:]
        out = nxt
    return out


def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    comps = []
    cur = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and lab[y, x] == 0:
                cur += 1
                lab[y, x] = cur
                q = deque([(y, x)])
                ymin = ymax = y
                xmin = xmax = x
                size = 0
                while q:
                    cy, cx = q.popleft()
                    size += 1
                    if cy < ymin:
                        ymin = cy
                    if cy > ymax:
                        ymax = cy
                    if cx < xmin:
                        xmin = cx
                    if cx > xmax:
                        xmax = cx
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur
                            q.append((ny, nx))
                comps.append((cur, size, xmin, xmax, ymin, ymax))
    return lab, comps


def main():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    print("size", im.size)
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    raw = ink_mask(a)
    print("ink pixels", int(raw.sum()), "dilate", iters)
    thick = dilate(raw, iters)
    lab, comps = label(thick)
    comps.sort(key=lambda c: -c[1])
    print("components with size >= 120:")
    for cid, size, x0, x1, y0, y1 in comps:
        if size < 120:
            continue
        # average colour of the raw ink inside this bbox
        sub = a[y0:y1 + 1, x0:x1 + 1]
        subm = raw[y0:y1 + 1, x0:x1 + 1]
        mean = sub.reshape(-1, 3)[subm.reshape(-1) > 0].mean(axis=0) if subm.any() else [0, 0, 0]
        print("  #%3d size=%7d bbox x %3d..%3d y %3d..%3d  mean rgb(%3d,%3d,%3d)"
              % (cid, size, x0, x1, y0, y1, mean[0], mean[1], mean[2]))
    print("total components", len(comps))
    small = [c for c in comps if c[1] < 4000]
    print("components under 4000 px:", len(small))


if __name__ == "__main__":
    sys.exit(main())
