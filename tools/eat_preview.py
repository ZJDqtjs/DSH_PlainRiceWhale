"""Dump the eating-related candidate stickers so a composite can be eyeballed first.

Writes .work/eat/<name>.png: the raw first/middle frames of every `chi`/`fan` master
GIF in tools/pet_gifs, plus the shipped hungry.gif and the meh JPG face cut.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PETS = os.path.join(BASE, 'tools', 'pet_gifs')
OUT = os.path.join(BASE, '.work', 'eat')


def dump(path, tag, frames):
    im = Image.open(path)
    n = getattr(im, 'n_frames', 1)
    picked = sorted({int(n * f) % max(1, n) for f in frames}) if n > 1 else [0]
    for i in picked:
        im.seek(i)
        rgba = im.convert('RGBA')
        arr = np.asarray(rgba)
        a = arr[..., 3]
        ys, xs = np.nonzero(a > 40)
        if len(xs) == 0:
            continue
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        crop = rgba.crop(box)
        name = f'{tag}__f{i:03d}.png'
        crop.save(os.path.join(OUT, name))
        print(f'{name:34s} {crop.size}  src {im.size} frames={n}')


def main():
    os.makedirs(OUT, exist_ok=True)
    for entry in sorted(os.listdir(PETS)):
        if not entry.endswith('.gif'):
            continue
        stem = entry.split('__')[-1].rsplit('.', 1)[0]
        if 'chi' not in stem and 'fan' not in stem:
            continue
        dump(os.path.join(PETS, entry), entry[:-4], (0.0, 0.35, 0.7))
    dump(os.path.join(BASE, 'whale-aside', 'assets', 'gifs', 'hungry.gif'), 'shipped-hungry', (0.0, 0.5))
    face = Image.open(os.path.join(BASE, 'whale-aside', 'assets', 'gifs', 'meh.jpg')).convert('RGBA')
    face.save(os.path.join(OUT, 'meh-face.png'))
    print(f'{"meh-face.png":34s} {face.size}  src meh.jpg')


if __name__ == '__main__':
    main()
