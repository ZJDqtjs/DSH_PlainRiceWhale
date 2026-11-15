"""Inspect the shipped mood stickers: frames, delays, transparency, colour hygiene.

The seven animated GIFs that used to fill this list are retired material, so what ships
now is the single `meh` still. The tool still walks whatever `STICKERS` names, so adding
a slot back is one line. It reads every GIF frame separately and judges the decoded
alpha, not the header fields: Pillow never re-exposes `info["transparency"]` for frames
after the first one, so the composited pixels are the only trustworthy signal.
"""
import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# mood -> the file that ships it, mirroring MOOD_STICKERS in whale-aside/index.js
STICKERS = {'meh': 'meme2_clean.png'}
BUDGET = 620 * 1024
paths = sys.argv[1:] or [
    os.path.join(BASE, 'whale-aside', 'assets', 'gifs', name) for name in STICKERS.values()
]

for path in paths:
    im = Image.open(path)
    durs = []
    shares = []
    greens = 0
    total = 0
    frames = getattr(im, 'n_frames', 1)
    for i in range(frames):
        im.seek(i)
        durs.append(int(im.info.get('duration') or 0))
        arr = np.asarray(im.convert('RGBA'))
        a = arr[..., 3]
        total += a.size
        shares.append(round(100.0 * (a < 40).mean(), 1))
        r, g, b = (arr[..., k].astype(int) for k in range(3))
        greens += int(((g > r + 40) & (g > b + 40) & (a > 40)).sum())
    size = os.path.getsize(path)
    stem = os.path.basename(path).rsplit('.', 1)[0]
    # an RGB master (the clean meme still) has no alpha at all; only a file that
    # declares one can be accused of having lost it
    probe = Image.open(path)
    probe.seek(0)
    has_alpha = 'transparency' in probe.info or probe.mode in ('RGBA', 'LA', 'PA')
    problems = []
    if has_alpha and min(shares) < 1.0:
        problems.append('frame %d renders fully opaque (lost transparency)' % shares.index(min(shares)))
    if 100.0 * greens / total > 0.5:
        problems.append('green residue')
    if size > BUDGET:
        problems.append('over budget')
    print('%s %-12s %-4s %3dx%-3d f=%-3d %6.1fKB loop=%4.1fs delay=%-3d-%-3dms clear=%5.1f-%5.1f%%%s green=%.3f%% %s'
          % ('OK' if not problems else '!!', stem, im.format, im.width, im.height,
             frames, size / 1024, sum(durs) / 1000, min(durs), max(durs),
             min(shares), max(shares), '' if has_alpha else '  (no alpha)',
             100.0 * greens / total,
             '' if not problems else '; '.join(problems)))

