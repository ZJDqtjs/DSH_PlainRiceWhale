import os, sys, glob
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\code\DSH_PlainRiceWhale\whale-aside\assets\gifs"
for p in sorted(glob.glob(os.path.join(D, "*.gif"))):
    im = Image.open(p)
    n = getattr(im, "n_frames", 1)
    tot = 0
    for i in range(n):
        im.seek(i)
        tot += (im.info.get("duration") or 0)
    im.seek(0)
    pal = im.getpalette() or []
    ncol = len(pal)//3
    print(f"{os.path.basename(p):11s} {im.width}x{im.height} frames={n:3d} palette={ncol:3d} avg_ms={tot//n:4d} loop={tot/1000:.1f}s pal_mode={im.mode}")
