# -*- coding: utf-8 -*-
"""Quick numeric QA of the seven mood GIFs (no human eyes needed)."""
import hashlib
import os

from PIL import Image, ImageChops, ImageStat

BASE = r"D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs"
MOODS = ["tsun", "sweet", "lazy", "shy", "panic", "hungry", "smug"]

seen = {}
for mood in MOODS:
    path = os.path.join(BASE, mood + ".gif")
    size = os.path.getsize(path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]
    im = Image.open(path)
    frames = []
    for i in range(im.n_frames):
        im.seek(i)
        frames.append(im.convert("RGB"))
    first = frames[0]
    stat = ImageStat.Stat(first)
    spread = sum(stat.stddev) / 3.0
    motion = 0.0
    for a, b in zip(frames, frames[1:]):
        diff = ImageChops.difference(a, b)
        motion += ImageStat.Stat(diff).mean[0]
    motion /= max(1, len(frames) - 1)
    bg = first.getpixel((1, 1))
    dup = seen.get(digest)
    seen[digest] = mood
    print(
        "%-7s %3dx%-3d f=%-2d %6.1fKB std=%-5.1f motion=%-5.2f corner=%s %s"
        % (
            mood,
            first.size[0],
            first.size[1],
            im.n_frames,
            size / 1024.0,
            spread,
            motion,
            bg,
            ("DUP with " + dup) if dup else "",
        ),
        flush=True,
    )
