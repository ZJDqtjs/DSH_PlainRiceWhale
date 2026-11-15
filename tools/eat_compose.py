"""Compose one「吃饭饭」scene: the meme whale-girl head behind a table, facing a bowl.

The head comes straight out of `.work/meme_src.jpg` with the same component erasure
`build_meme_jpg.py` uses, so the speech bubble and its baked-in line are gone; the
high-resolution cut is kept here (the shipped sticker is downscaled to 256px).

Everything else — table, bowl, rice, chopsticks, steam — is drawn with PIL in the
flat sticker style (navy outlines, soft fills) so it sits next to the art instead of
fighting it. The scene is rendered at 2x supersampling and downscaled for clean edges.

Output: .work/whale-eating.png
"""
import os
import sys
import math
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, '.work', 'meme_src.jpg')
OUT = os.path.join(BASE, '.work', 'whale-eating.png')

SS = 2                       # supersample factor
W, H = 1024, 1024
INK = (43, 51, 80)           # the artwork's own navy outline colour

# head placement: the crop bleeds off the right edge, its bottom hides behind the table
HEAD_W = 772
HEAD_AT = (252, 78)
TABLE_Y = 690

BOWL_CX, BOWL_CY = 336, 800  # rim centre on the table
BOWL_RX = 158
BOWL_RY = 104


def label(mask):
    """4-connected labelling, same walk the sticker builder uses."""
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


def head_cutout():
    """Return the whale-girl head as RGBA at native resolution, bubble and text erased."""
    im = Image.open(SRC).convert('RGB')
    w, h = im.size
    a = np.asarray(im).astype(np.int16)
    ink = np.asarray(255 - a.min(axis=2) > 28, dtype=np.uint8)
    lab, comps = label(ink)
    keep, drop = [], []
    for cid, size, x0, x1, y0, y1 in comps:
        sub = a[y0:y1 + 1, x0:x1 + 1]
        subm = ink[y0:y1 + 1, x0:x1 + 1]
        mean = sub.reshape(-1, 3)[subm.reshape(-1) > 0].mean(axis=0) if subm.any() else np.zeros(3)
        body = size >= 20000
        dashes = y0 >= 460 and mean[2] - mean[0] >= 30
        (keep if body or dashes else drop).append(cid)

    keep_ink = np.isin(lab, keep)
    drop_ink = np.isin(lab, drop)
    erased = a.copy()
    halo = grow(drop_ink.astype(np.uint8), 4).astype(bool)
    erased[halo] = 255

    alpha = np.asarray(255 - erased.min(axis=2) > 8, dtype=np.uint8) * 255
    # keep only what belongs to the character, then close every pocket the outline encloses
    near = grow(keep_ink.astype(np.uint8), 6).astype(bool)
    alab, acomps = label((alpha > 0).astype(np.uint8))
    for cid, size, x0, x1, y0, y1 in acomps:
        region = alab[y0:y1 + 1, x0:x1 + 1] == cid
        if not np.any(near[y0:y1 + 1, x0:x1 + 1] & region):
            alpha[alab == cid] = 0
    opaque = alpha > 0
    blab, bcomps = label((~opaque).astype(np.uint8))
    for cid, size, x0, x1, y0, y1 in bcomps:
        if y0 == 0 or x0 == 0 or y1 == h - 1 or x1 == w - 1:
            continue
        alpha[blab == cid] = 255

    ys, xs = np.nonzero(alpha > 0)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    rgb = Image.fromarray(erased.astype(np.uint8), 'RGB').crop(box)
    m = Image.fromarray(alpha, 'L').crop(box).filter(ImageFilter.GaussianBlur(0.6))
    cut = Image.merge('RGBA', (*rgb.split(), m))
    scale = HEAD_W * SS / cut.width
    return cut.resize((int(round(cut.width * scale)), int(round(cut.height * scale))), Image.LANCZOS)


def background():
    """Warm cream wall with a soft glow behind the girl."""
    ys = np.linspace(0.0, 1.0, H * SS)[:, None]
    top = np.array([248, 243, 233], dtype=float)
    bottom = np.array([235, 224, 208], dtype=float)
    grad = (top * (1 - ys) + bottom * ys).astype(np.uint8)
    img = Image.fromarray(np.repeat(grad[:, None, :], W * SS, axis=1), 'RGB')

    glow = Image.new('L', (W * SS, H * SS), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((int(0.42 * W * SS), int(0.02 * H * SS), int(1.18 * W * SS), int(0.92 * H * SS)),
               fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(90 * SS))
    img.paste(Image.new('RGB', img.size, (255, 252, 244)), (0, 0), glow)
    return img.convert('RGBA')


def table(canvas):
    """A wooden counter across the bottom, which also hides the head's cropped edge."""
    d = ImageDraw.Draw(canvas)
    y0 = TABLE_Y * SS
    d.rectangle((0, y0, W * SS, H * SS), fill=(206, 165, 122, 255))
    d.rectangle((0, y0, W * SS, y0 + 13 * SS), fill=(226, 189, 148, 255))
    d.line((0, y0, W * SS, y0), fill=INK + (255,), width=4 * SS)
    for k in range(1, 6):
        yy = y0 + int((18 + k * 52) * SS)
        d.line((0, yy, W * SS, yy), fill=(188, 148, 106, 120), width=2 * SS)
    shade = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(shade).rectangle((0, y0, W * SS, y0 + 40 * SS), fill=70)
    canvas.paste(Image.new('RGB', canvas.size, (120, 82, 48)), (0, 0), shade.filter(ImageFilter.GaussianBlur(6 * SS)))


def shadow(canvas, cx, cy, rx, ry, strength=90):
    blob = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(blob).ellipse(((cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS), fill=strength)
    blob = blob.filter(ImageFilter.GaussianBlur(9 * SS))
    canvas.paste(Image.new('RGB', canvas.size, (110, 76, 44)), (0, 0), blob)


def bowl(canvas):
    """A navy-outlined bowl heaped with white rice, drawn as a side view.

    Order matters: the mound goes down first, then the bowl body is painted over its
    lower half, so the rice reads as sitting *in* the bowl instead of floating above it.
    """
    d = ImageDraw.Draw(canvas)
    cx, cy = BOWL_CX * SS, BOWL_CY * SS
    rx, ry = BOWL_RX * SS, BOWL_RY * SS

    # 1. the mound: fill, then grains kept strictly inside, then the outline last so
    #    nothing pokes past the rim (the first pass read as a string of pearls).
    dome = (cx - rx * 0.84, cy - ry * 0.80, cx + rx * 0.84, cy + ry * 0.62)
    d.ellipse(dome, fill=(255, 255, 255, 255))
    for k in range(18):
        ang = math.radians(12 + k * 9.6)
        gx = cx - math.cos(ang) * rx * 0.70
        gy = cy - ry * 0.09 - math.sin(ang) * ry * 0.58
        d.ellipse((gx - 9 * SS, gy - 8 * SS, gx + 9 * SS, gy + 8 * SS),
                  fill=(255, 255, 255, 255), outline=(228, 232, 240, 255), width=2 * SS)
    rng = np.random.default_rng(11)
    for _ in range(20):
        gx = cx + rng.uniform(-0.52, 0.52) * rx
        gy = cy - ry * 0.10 - rng.uniform(0.06, 0.44) * ry
        d.ellipse((gx - 9 * SS, gy - 4 * SS, gx + 9 * SS, gy + 4 * SS), fill=(242, 245, 250, 255))
    d.ellipse(dome, outline=INK + (255,), width=5 * SS)

    # 2. the bowl body, painted over the mound's lower half
    pts = [(cx + rx * math.cos(math.radians(t)), cy + ry * math.sin(math.radians(t)))
           for t in range(0, 181, 5)]
    d.polygon(pts, fill=(250, 251, 254, 255))
    d.line(pts, fill=INK + (255,), width=5 * SS, joint='curve')
    d.line(((cx - rx, cy), (cx + rx, cy)), fill=INK + (255,), width=5 * SS)
    band = [(cx + rx * 0.90 * math.cos(math.radians(t)), cy + ry * 0.50 * math.sin(math.radians(t)))
            for t in range(6, 175, 5)]
    d.line(band, fill=(96, 132, 186, 255), width=9 * SS, joint='curve')
    d.rounded_rectangle((cx - rx * 0.22, cy + ry * 0.90, cx + rx * 0.22, cy + ry * 1.06),
                        radius=5 * SS, fill=(232, 236, 243, 255), outline=INK + (255,), width=4 * SS)


def chopsticks(canvas):
    """Two sticks resting across the rim, angled up but stopping short of her face."""
    for dx, dy, tilt in ((-4, 6, 27), (14, 14, 23)):
        length = 300
        stick = Image.new('RGBA', (length * SS, 18 * SS), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stick)
        sd.rounded_rectangle((0, 2 * SS, (length - 30) * SS, 14 * SS), radius=5 * SS,
                             fill=(201, 138, 75, 255), outline=INK + (255,), width=3 * SS)
        sd.polygon(((length - 30) * SS, 3 * SS, length * SS, 8 * SS, (length - 30) * SS, 14 * SS),
                   fill=(150, 96, 52, 255))
        stick = stick.rotate(tilt, expand=True, resample=Image.BICUBIC)
        canvas.alpha_composite(stick, (int((BOWL_CX + dx) * SS) - stick.width // 4,
                                       int((BOWL_CY - 40 + dy) * SS) - stick.height // 2))


def steam(canvas):
    """Three pale wisps; they must stay white or they read as smudges over the art."""
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k, base in enumerate((-74, -8, 58)):
        pts = []
        for t in range(0, 33):
            u = t / 32
            pts.append(((BOWL_CX + base + 16 * math.sin(u * 4.6 + k)) * SS,
                        (BOWL_CY - 92 - u * 168) * SS))
        d.line(pts, fill=(255, 255, 255, 115), width=(6 - k) * SS, joint='curve')
    layer = layer.filter(ImageFilter.GaussianBlur(9 * SS))
    canvas.alpha_composite(layer)


def caption(canvas):
    def font(path, size):
        try:
            return ImageFont.truetype(path, size * SS)
        except OSError:
            return ImageFont.load_default()

    msyh = r'C:\Windows\Fonts\msyh.ttc'
    hei = r'C:\Windows\Fonts\simhei.ttf'
    d = ImageDraw.Draw(canvas)
    d.text((64 * SS, 96 * SS), '吃饭饭', font=font(msyh if os.path.exists(msyh) else hei, 78),
           fill=INK + (255,))
    d.text((70 * SS, 196 * SS), '白米饭是最高信仰', font=font(msyh if os.path.exists(msyh) else hei, 30),
           fill=(96, 106, 134, 255))


def main():
    canvas = background()
    head = head_cutout()
    canvas.alpha_composite(head, (HEAD_AT[0] * SS, HEAD_AT[1] * SS))
    table(canvas)
    shadow(canvas, BOWL_CX, BOWL_CY + 74, BOWL_RX + 26, 30)
    bowl(canvas)
    chopsticks(canvas)
    steam(canvas)
    caption(canvas)
    final = canvas.convert('RGB').resize((W, H), Image.LANCZOS)
    final.save(OUT)
    print('wrote', OUT, final.size, round(os.path.getsize(OUT) / 1024, 1), 'KB')


if __name__ == '__main__':
    main()
