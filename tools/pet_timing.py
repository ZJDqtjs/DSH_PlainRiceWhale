import os, sys, glob, json
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\code\DSH_PlainRiceWhale\tools\pet_gifs'
for p in sorted(glob.glob(os.path.join(D, '*.gif'))):
    im = Image.open(p)
    durs = []
    n = getattr(im, 'n_frames', 1)
    for i in range(min(n, 6)):
        im.seek(i)
        durs.append(im.info.get('duration'))
    print(f'{os.path.basename(p)[:50]:52s} frames={n} dur_head={durs} loop={im.info.get("loop")}')
