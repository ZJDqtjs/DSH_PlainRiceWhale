"""Turn the Bilibili whale-pet master GIFs into the 7 mood stickers whale-aside ships.

Source masters live in tools/pet_gifs/ as "<mood>__<original-name>.gif".
Output: whale-aside/assets/gifs/<mood>.gif — cropped to the character, resized for
chat-sticker display, and kept at the source frame count so the 12fps motion stays smooth.
"""
import os
import sys
import json
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\code\DSH_PlainRiceWhale\tools\pet_gifs'
DST = r'D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs'
BUDGET = 620 * 1024          # per-file ceiling; one sticker loads per bubble, served from localhost
DECIMATE = 1                 # keep every source frame -> original 12.5fps cadence, no choppiness
WIDTH = 128                  # displayed ~84px tall in the bubble; 128px source keeps it crisp

PICK = {
    'tsun': 'dianji-huiying-aojiao-shengqi-ceshen-zhanshi.gif',
    'sweet': 'dianji-huiying-kaixin-yuedong.gif',
    'lazy': 'haqian-liantian.gif',
    'shy': 'dianji-huiying-haixiu-jingya.gif',
    'panic': 'da-keshui-bei-jingxing.gif',
    'hungry': 'chi-baifan.gif',
    'smug': 'qian-dai-man-yi.gif',
}


def union_bbox(im, frames):
    x0 = y0 = 10 ** 9
    x1 = y1 = -1
    for i in frames:
        im.seek(i)
        a = np.asarray(im.convert('RGBA'))[..., 3]
        ys, xs = np.nonzero(a > 40)
        if len(xs) == 0:
            continue
        x0, x1 = min(x0, int(xs.min())), max(x1, int(xs.max()))
        y0, y1 = min(y0, int(ys.min())), max(y1, int(ys.max()))
    return x0, y0, x1, y1


def render(im, box, size, step, colors, out):
    n = im.n_frames
    frames, durations = [], []
    for i in range(0, n, step):
        im.seek(i)
        fr = im.convert('RGBA').crop(box).resize(size, Image.LANCZOS)
        frames.append(fr.convert('P', palette=Image.ADAPTIVE, colors=colors))
        durations.append(max(40, int((im.info.get('duration') or 80) * step)))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, disposal=2, optimize=True, transparency=0)
    return os.path.getsize(out), durations


def build(mood, name, pad=6):
    src = os.path.join(SRC, f'{mood}__{name}')
    im = Image.open(src)
    n = im.n_frames
    x0, y0, x1, y1 = union_bbox(im, list(range(0, n, max(1, n // 40))))
    box = (max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + 1 + pad), min(im.height, y1 + 1 + pad))
    cw, ch = box[2] - box[0], box[3] - box[1]
    out = os.path.join(DST, f'{mood}.gif')

    best = None
    for width in (WIDTH, WIDTH - 16, WIDTH - 32):
        size = (width, max(1, int(round(ch * width / cw))))
        for step in (DECIMATE, 3, 4):
            for colors in (64, 48):
                sz, durs = render(im, box, size, step, colors, out)
                best = {'mood': mood, 'src': name, 'box': list(box), 'size': list(size),
                        'frames': len(durs), 'colors': colors, 'bytes': sz,
                        'frame_ms': durs[0], 'loop_ms': sum(durs),
                        'over_budget': sz > BUDGET}
                if sz <= BUDGET:
                    return best
    return best


os.makedirs(DST, exist_ok=True)
report = [build(m, n) for m, n in PICK.items()]
for r in report:
    flag = ' OVER' if r['over_budget'] else ''
    print(f"{r['mood']:7s} {r['size'][0]}x{r['size'][1]} f={r['frames']:3d} c={r['colors']:3d} "
          f"{r['bytes']/1024:6.1f}KB loop={r['loop_ms']/1000:.1f}s  <- {r['src']}{flag}")
print('total KB', round(sum(r['bytes'] for r in report) / 1024, 1))
json.dump(report, open(os.path.join(SRC, 'build_report.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1, default=int)
