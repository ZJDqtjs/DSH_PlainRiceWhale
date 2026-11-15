"""Numeric QA for the shipped mood GIFs: real motion, no green fringe, clean alpha."""
import os
import sys
import glob
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs'


def frames(im, step=4):
    out = []
    for i in range(0, im.n_frames, step):
        im.seek(i)
        out.append(np.asarray(im.convert('RGBA')).astype(np.int16))
    return out


print(f"{'file':11s} {'motion':>7s} {'moving':>7s} {'green%':>7s} {'edge_green%':>11s} note")
worst = []
for p in sorted(glob.glob(os.path.join(D, '*.gif'))):
    im = Image.open(p)
    fs = frames(im)
    diffs, moving = [], []
    for a, b in zip(fs, fs[1:]):
        d = np.abs(a[..., :3].astype(np.int16) - b[..., :3].astype(np.int16)).mean()
        diffs.append(d)
        m = (np.abs(a[..., 3].astype(np.int16) - b[..., 3].astype(np.int16)) > 8)
        moving.append(m.mean())
    motion = float(np.mean(diffs))
    mov = float(np.mean(moving))

    a = fs[len(fs) // 2]
    alpha = a[..., 3]
    rgb = a[..., :3]
    op = alpha > 128
    sel = rgb[op]
    green = float(((sel[:, 1] > sel[:, 0] + 40) & (sel[:, 1] > sel[:, 2] + 40)).mean()) if len(sel) else 0.0

    # pixels adjacent to transparency inside the opaque mask = silhouette edge
    from numpy import roll
    nb = (roll(alpha, 1, 0) <= 128) | (roll(alpha, -1, 0) <= 128) | \
         (roll(alpha, 1, 1) <= 128) | (roll(alpha, -1, 1) <= 128)
    edge = op & nb
    es = rgb[edge]
    eg = float(((es[:, 1] > es[:, 0] + 40) & (es[:, 1] > es[:, 2] + 40)).mean()) if len(es) else 0.0

    note = []
    if motion < 1.0:
        note.append('LOW_MOTION')
    if mov < 0.01:
        note.append('STATIC')
    if green > 0.01:
        note.append('GREEN_INSIDE')
    if eg > 0.05:
        note.append('GREEN_FRINGE')
    if note:
        worst.append((os.path.basename(p), note))
    print(f'{os.path.basename(p):11s} {motion:7.2f} {mov:7.3f} {green*100:6.2f}% {eg*100:10.2f}% '
          f'{" ".join(note) or "ok"}')

print()
print('FAILURES:', worst if worst else 'none')
