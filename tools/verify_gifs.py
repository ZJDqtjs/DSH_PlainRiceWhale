import os, sys, glob
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs'

for p in sorted(glob.glob(os.path.join(D, '*.gif'))):
    im = Image.open(p)
    n = getattr(im, 'n_frames', 1)
    im.seek(n // 2)
    a = np.asarray(im.convert('RGBA')).astype(int)
    alpha = a[..., 3]
    rgb = a[..., :3]
    opaque = alpha > 128
    ys, xs = np.nonzero(opaque)
    sel = rgb[opaque]
    mx, mn = sel.max(1), sel.min(1)
    colorful = sel[(mx - mn) > 30]
    cm = colorful.mean(0) if len(colorful) else sel.mean(0)
    blue_dom = float(((sel[:, 2] > sel[:, 0] + 15) & (sel[:, 2] > sel[:, 1] + 5)).mean())
    print(f'{os.path.basename(p):11s} {im.width}x{im.height} f={n:3d} {os.path.getsize(p)/1024:6.1f}KB '
          f'opaque={opaque.mean():.2f} bbox={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1} '
          f'RGB={[int(v) for v in cm]} blue_frac={blue_dom:.2f} magic={open(p,"rb").read(6)[:3]}')
