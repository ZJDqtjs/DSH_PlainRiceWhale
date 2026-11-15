# -*- coding: utf-8 -*-
"""Diagnostic: how much of a sticker's backdrop is reachable from its border?

For every slot it reports, per corner seed, the fraction of the frame whose colour
sits within TOLERANCE of that seed and is 4-connected to the border. Used to decide
which slots have an opaque backdrop and how aggressive keying must be.
"""
import numpy as np
from PIL import Image

RAW = r"D:\code\DSH_PlainRiceWhale\.work\gifs_raw\dl3"
SLOTS = {
    "tsun": "a40694985_004.gif",
    "sweet": "a40694985_005.gif",
    "lazy": "a40694985_018.gif",
    "shy": "a40694985_019.gif",
    "panic": "a40694985_014.gif",
    "hungry": "a40694985_020.gif",
    "smug": "a40694985_011.gif",
}
TOL = 34


def grow(reach, allowed):
    """4-connected propagation of `reach` inside `allowed` until stable."""
    cur = reach
    for _ in range(4000):
        nxt = cur.copy()
        nxt[1:, :] |= cur[:-1, :]
        nxt[:-1, :] |= cur[1:, :]
        nxt[:, 1:] |= cur[:, :-1]
        nxt[:, :-1] |= cur[:, 1:]
        nxt &= allowed
        if nxt.sum() == cur.sum():
            break
        cur = nxt
    return cur


def analyse(path):
    im = Image.open(path)
    im.seek(0)
    arr = np.asarray(im.convert("RGBA")).astype(np.int16)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    h, w = alpha.shape
    opaque = alpha >= 128
    report = []
    for cy, cx in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]:
        seed = rgb[cy, cx]
        near = (np.abs(rgb - seed).max(axis=2) <= TOL) & opaque
        if not near[cy, cx]:
            report.append(((cy, cx), tuple(int(v) for v in seed), 0.0, 0.0))
            continue
        reach = np.zeros_like(near)
        reach[cy, cx] = True
        reached = grow(reach, near)
        pct = 100.0 * reached.sum() / (h * w)
        pct_near = 100.0 * near.sum() / (h * w)
        report.append(((cy, cx), tuple(int(v) for v in seed), pct, pct_near))
    return report


for slot, src in SLOTS.items():
    print(slot, flush=True)
    for corner, seed, pct, near in analyse(RAW + "\\" + src):
        print("   corner=%-9s seed=%-16s reachable=%5.1f%% nearc=%5.1f%%" % (str(corner), str(seed), pct, near))
