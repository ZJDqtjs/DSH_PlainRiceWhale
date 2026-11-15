import os, sys, glob
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\code\DSH_PlainRiceWhale\tools\pet_gifs'

for p in sorted(glob.glob(os.path.join(D, '*.gif'))):
    im = Image.open(p)
    n = getattr(im, 'n_frames', 1)
    im.seek(n // 2)
    rgba = im.convert('RGBA')
    a = np.asarray(rgba).astype(int)
    h, w = a.shape[:2]
    rgb = a[..., :3]
    alpha = a[..., 3]
    # green screen test
    g_mask = (rgb[..., 1] > 180) & (rgb[..., 0] < 120) & (rgb[..., 2] < 120)
    # corner colors
    corners = [tuple(a[0, 0][:4]), tuple(a[0, -1][:4]), tuple(a[-1, 0][:4]), tuple(a[-1, -1][:4])]
    trans = float((alpha < 20).mean())
    print(f'{os.path.basename(p)[:52]:55s} {w}x{h} f={n:3d} green={g_mask.mean():.3f} '
          f'transparent={trans:.3f} corner={corners[0]}')
