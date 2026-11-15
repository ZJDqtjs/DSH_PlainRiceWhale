"""Clean the meme to an *empty* thought bubble, working on the pristine master.

The master drew a red rectangle around the bubble's text only, so the ask is a blank
thought bubble — not another head cut, and not the annotated screenshot either.

Two inputs, two jobs:

  * `.work/meme2_src.png` (the annotated screenshot) is read only to learn **where**:
    its toolbar band and blue selection frame are measured, and the red rectangle's
    bounding box is taken as the master's own selection.
  * `.work/meme_src.jpg` (the pristine 850x807 master) is what actually gets edited.
    This matters: re-compressing the screenshot fused the bubble ring with the
    character's outlines, and the red line was drawn *on top of* the ring, so erasing
    it on the screenshot chews a hole in the bubble. On the pristine master the ring is
    a separate 18227 px block and the text strokes are 19 small independent blocks, so
    the words lift out and the bubble comes back whole.

Output: whale-aside/assets/gifs/meme2_clean.png — this is the shipped `meh` sticker,
so the builder writes straight into the bundle instead of leaving a scratch copy.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = os.path.join(BASE, '.work', 'meme2_src.png')
MASTER = os.path.join(BASE, '.work', 'meme_src.jpg')
OUT = os.path.join(BASE, 'whale-aside', 'assets', 'gifs', 'meme2_clean.png')

INK_THR = 28                 # distance from white that counts as drawn ink
HALO = 4                     # px of ringing eaten around anything erased
RING_MAX = 40000             # the bubble ring is ~18k px; the character is ~247k
TEXT_MAX = 5000              # a text stroke is small; the ring is not


def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    comps = []
    cur = 0
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or lab[y, x]:
                continue
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
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        q.append((ny, nx))
            comps.append((cur, size, xmin, xmax, ymin, ymax))
    return lab, comps


def grow(mask, iters):
    out = mask
    for _ in range(iters):
        nxt = out.copy()
        nxt[1:, :] |= out[:-1, :]
        nxt[:-1, :] |= out[1:, :]
        nxt[:, 1:] |= out[:, :-1]
        nxt[:, :-1] |= out[:, 1:]
        out = nxt
    return out


def selection_box():
    """The red rectangle the master drew, shifted into master coordinates.

    The screenshot carries a viewer toolbar above the artwork and a blue selection
    frame around it, so its pixel origin is not the artwork's. Both offsets are
    measured and subtracted, otherwise the box sits ~43px too low and the first line
    of text falls outside it.
    """
    a = np.asarray(Image.open(SHOT).convert('RGB')).astype(np.int16)
    h, w = a.shape[0], a.shape[1]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    mean = a.mean(axis=2)
    sat = a.max(axis=2) - a.min(axis=2)
    grey = (sat < 12) & (mean > 120) & (mean < 246)
    band = grey.sum(axis=1) / w
    top = 0
    for y in range(min(120, h)):
        if band[y] > 0.5:
            top = y + 1

    blue = (b > 150) & (b - r > 70) & (b - g > 50)
    cols = blue.sum(axis=0) / h
    left = int(np.argmax(cols > 0.4)) if (cols > 0.4).any() else 0
    print(f'screenshot chrome: toolbar to y={top}, frame left x={left}')

    red = (r - g > 120) & (r - b > 120)
    if not red.any():
        raise SystemExit('no red annotation found in the screenshot')
    ys, xs = np.nonzero(red)
    box = (int(xs.min()) - left - 2, int(xs.max()) - left - 2,
           int(ys.min()) - top - 1, int(ys.max()) - top - 1)
    print(f'selection box in master coords: x {box[0]}..{box[1]} y {box[2]}..{box[3]}')
    return box


def main():
    sel = selection_box()

    im = Image.open(MASTER).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    h, w = a.shape[0], a.shape[1]
    print('master', w, 'x', h)

    ink = np.asarray(255 - a.min(axis=2) > INK_THR, dtype=np.uint8)
    lab, comps = label(ink)

    # the bubble ring: the widest-bounding-box block that is not the character
    ring = max((c for c in comps if c[1] < RING_MAX), key=lambda c: (c[3] - c[2]) * (c[5] - c[4]))
    _, rsize, rx0, rx1, ry0, ry1 = ring
    print(f'bubble ring: size={rsize} bbox x {rx0}..{rx1} y {ry0}..{ry1}')

    text_ids = []
    for cid, size, x0, x1, y0, y1 in comps:
        inside_ring = x0 > rx0 + 12 and x1 < rx1 - 12 and y0 > ry0 + 12 and y1 < ry1 - 12
        inside_sel = x0 >= sel[0] - 24 and x1 <= sel[1] + 24 and y0 >= sel[2] - 24 and y1 <= sel[3] + 24
        if size < TEXT_MAX and inside_ring and inside_sel:
            text_ids.append(cid)
    if len(text_ids) < 8:
        raise SystemExit(f'only {len(text_ids)} strokes matched — the words would survive')
    text_mask = np.isin(lab, text_ids)

    erased = a.copy()
    erased[grow(text_mask.astype(np.uint8), HALO).astype(bool)] = 255
    print(f'text erased: {len(text_ids)} blocks, {int(text_mask.sum())} ink px, ring kept intact')

    out = Image.fromarray(np.clip(erased, 0, 255).astype(np.uint8), 'RGB')
    out.save(OUT)
    print('wrote', OUT, out.size, round(os.path.getsize(OUT) / 1024, 1), 'KB')


if __name__ == '__main__':
    main()
