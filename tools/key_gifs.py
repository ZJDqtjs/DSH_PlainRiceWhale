# -*- coding: utf-8 -*-
"""Rebuild the seven mood GIFs, keying out only the ones with an opaque backdrop.

Six of the seven Bilibili sources already carry an alpha channel; one (the "lazy"
sticker) ships with a dithered gray checkerboard backdrop, which would render as
a grey square inside the chat bubble. This script detects that case per slot and
removes the border-connected backdrop, then re-quantizes everything to the same
sticker look. Sources are never modified.
"""
import os

from PIL import Image, ImageChops, ImageDraw

BASE = r"D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs"
RAW = r"D:\code\DSH_PlainRiceWhale\.work\gifs_raw\dl3"
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

TOLERANCE = 34
MARK = 128


def keyed_background(frame):
    """Return (frame, removed_fraction) with the border-connected backdrop cleared."""
    rgba = frame.convert("RGBA")
    rgb = rgba.convert("RGB")
    w, h = rgb.size
    alpha = rgba.split()[3]
    cleared = 0
    for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        seed_rgb = rgb.getpixel(corner)
        if alpha.getpixel(corner) < 128:
            continue  # already transparent at this corner
        diff = ImageChops.difference(rgb, Image.new("RGB", (w, h), seed_rgb)).convert("L")
        similar = diff.point(lambda v: 255 if v <= TOLERANCE else 0)
        if similar.getpixel(corner) != 255:
            continue
        ImageDraw.floodfill(similar, corner, MARK, thresh=0)
        clear = similar.point(lambda v: 255 if v == MARK else 0)
        alpha = ImageChops.darker(alpha, ImageChops.invert(clear))
        cleared += 1
    if cleared == 0:
        return rgba, 0.0
    result = rgba.copy()
    result.putalpha(alpha)
    return result, cleared


def transparency_pct(frames):
    total = 0
    clear = 0
    for frame in frames:
        px = list(frame.getdata())
        total += len(px)
        clear += sum(1 for p in px if p[3] < 128)
    return 100.0 * clear / max(1, total)


def load_frames(path, width, max_frames):
    im = Image.open(path)
    frames = []
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        frame, _ = keyed_background(im.convert("RGBA"))
        frames.append(frame)
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
        clear = f.split()[3].point(lambda a: 255 if a < 110 else 0)
        p.paste(colors - 1, mask=clear)
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
        probe = Image.open(src_path)
        probe.seek(0)
        before_pct = transparency_pct([probe.convert("RGBA")])

        chosen = None
        after_pct = 0.0
        for width, frames, colors, duration in LADDER:
            loaded = load_frames(src_path, width, frames)
            after_pct = transparency_pct(loaded)
            save(loaded, dst, duration, colors)
            size = os.path.getsize(dst)
            chosen = (width, len(loaded), colors, duration, size)
            if size <= LIMIT:
                break
        chk = Image.open(dst)
        print(
            "%-7s %3dx%-3d f=%-2d c=%-3d %3dms %6.1fKB  alpha %5.1f%% -> %5.1f%%"
            % (slot, chk.size[0], chk.size[1], chk.n_frames, chosen[2], chosen[3],
               chosen[4] / 1024.0, before_pct, after_pct),
            flush=True,
        )


if __name__ == "__main__":
    main()
