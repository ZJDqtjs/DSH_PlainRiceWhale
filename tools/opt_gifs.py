# -*- coding: utf-8 -*-
"""Downsize the mood GIFs so each one fits a <=120KB budget for the bundle.

Tries a ladder of (width, frames, colors) settings per slot and keeps the first
one that lands under the byte budget, preferring the largest/richest settings.
"""
import os

from PIL import Image

BASE = r"D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs"
RAW = os.path.join(BASE, "_raw", "dl3")
LIMIT = 120 * 1024

SLOTS = {
    "tsun": "a40694985_004.gif",
    "sweet": "a40694985_005.gif",
    "lazy": "a40694985_018.gif",
    "shy": "a40694985_019.gif",
    "panic": "a40694985_014.gif",
    "hungry": "a40694985_020.gif",
    "smug": "a40694985_011.gif",
}

LADDER = [
    (240, 20, 96, 70),
    (220, 18, 80, 70),
    (200, 16, 64, 80),
    (180, 14, 48, 80),
    (160, 12, 32, 90),
    (140, 10, 32, 100),
    (120, 8, 24, 110),
]


def load_frames(path, width, max_frames):
    im = Image.open(path)
    frames = []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        frames.append(im.convert("RGBA"))
    w, h = frames[0].size
    if w > width:
        nh = max(1, round(h * width / w))
        frames = [f.resize((width, nh), Image.LANCZOS) for f in frames]
    if len(frames) > max_frames:
        step = len(frames) / float(max_frames)
        frames = [frames[min(len(frames) - 1, int(round(i * step)))] for i in range(max_frames)]
    return frames


def save(frames, path, duration, colors):
    w, h = frames[0].size
    montage = Image.new("RGB", (w, h * len(frames)), (255, 255, 255))
    for i, f in enumerate(frames):
        bg = Image.new("RGB", f.size, (255, 255, 255))
        bg.paste(f, mask=f.split()[3])
        montage.paste(bg, (0, i * h))
    pal = montage.quantize(colors=colors - 1, method=Image.MEDIANCUT)

    out = []
    for f in frames:
        bg = Image.new("RGB", f.size, (255, 255, 255))
        bg.paste(f, mask=f.split()[3])
        p = bg.quantize(palette=pal, dither=Image.NONE)
        transparent = f.split()[3].point(lambda a: 255 if a < 110 else 0)
        p.paste(colors - 1, mask=transparent)
        out.append(p)

    palette = list(out[0].getpalette())
    if len(palette) < 768:
        palette += [0] * (768 - len(palette))
    palette[(colors - 1) * 3 : (colors - 1) * 3 + 3] = [255, 255, 255]
    for p in out:
        p.putpalette(palette)

    out[0].save(
        path,
        save_all=True,
        append_images=out[1:],
        duration=duration,
        loop=0,
        transparency=colors - 1,
        disposal=2,
        optimize=True,
    )


def main():
    for slot, src in SLOTS.items():
        src_path = os.path.join(RAW, src)
        dst = os.path.join(BASE, slot + ".gif")
        chosen = None
        for width, frames, colors, duration in LADDER:
            loaded = load_frames(src_path, width, frames)
            save(loaded, dst, duration, colors)
            size = os.path.getsize(dst)
            chosen = (width, len(loaded), colors, duration, size)
            if size <= LIMIT:
                break
        chk = Image.open(dst)
        print(
            "%-7s %3dx%-3d frames=%-2d colors=%-3d %3dms %6.1fKB total=%dms"
            % (slot, chk.size[0], chk.size[1], chk.n_frames, chosen[2], chosen[3],
               chosen[4] / 1024.0, chk.n_frames * chosen[3]),
            flush=True,
        )


if __name__ == "__main__":
    main()
