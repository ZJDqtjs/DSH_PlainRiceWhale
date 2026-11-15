import os, sys, glob
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\code\DSH_PlainRiceWhale\tools\pet_gifs'

for p in sorted(glob.glob(os.path.join(D, '*.gif'))):
    im = Image.open(p)
    n = getattr(im, 'n_frames', 1)
    im.seek(n // 2)
    a = np.asarray(im.convert('RGBA')).astype(int)
    alpha = a[..., 3]
    rgb = a[..., :3]
    opaque = alpha > 128
    ys, xs = np.nonzero(opaque)
    if len(xs) == 0:
        print(os.path.basename(p), 'NO OPAQUE PIXELS'); continue
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    sel = rgb[opaque]
    mean = sel.mean(0)
    # hue stats of opaque pixels
    mx = sel.max(1); mn = sel.min(1)
    sat = (mx - mn)
    colorful = sel[sat > 30] if (sat > 30).sum() > 30 else sel
    cm = colorful.mean(0)
    print(f'{os.path.basename(p)[:48]:50s} opaque={opaque.mean():.3f} bbox=({x0},{y0})-({x1},{y1}) '
          f'size={x1-x0+1}x{y1-y0+1} meanRGB={[int(v) for v in mean]} colorfulRGB={[int(v) for v in cm]} ncolor={len(colorful)}')
