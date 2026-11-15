import json, os, sys, urllib.request, urllib.error, time
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
RAW = 'https://raw.githubusercontent.com/PC2005-cloud/dsh-pet/main/dsh-pet/assets/preview/'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\pet_gifs'
os.makedirs(OUT, exist_ok=True)

CANDS = {
    'tsun':   ['dianji-huiying-aojiao-shengqi-ceshen-zhanshi.gif', 'beixiayitiao-zhamao.gif'],
    'sweet':  ['dianji-huiying-kaixin-yuedong.gif', 'dianji-huiying-yuanqi-huishou.gif'],
    'lazy':   ['haqian-liantian.gif', 'yuandi-xiaoqi-chenmian.gif', 'daiji-huxi-xiuxian.gif'],
    'shy':    ['dianji-huiying-haixiu-jingya.gif', 'dianji-huiying-naoyang-gegexiao.gif'],
    'panic':  ['da-keshui-bei-jingxing.gif', 'beishubiao-tuozhuai-xuankong-fankui.gif'],
    'hungry': ['chi-baifan.gif', 'dakou-chi-lingshi.gif'],
    'smug':   ['dongzhangxiwang.gif', 'qian-dai-man-yi.gif'],
}

def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b''
            time.sleep(4)
        except Exception:
            time.sleep(4)
    return None, b''

def analyze(path):
    im = Image.open(path)
    n = getattr(im, 'n_frames', 1)
    im.seek(n // 2 if n > 1 else 0)
    rgb = im.convert('RGB').resize((80, 80))
    a = np.asarray(rgb).reshape(-1, 3).astype(float)
    # ignore near-black/near-white background
    mask = (a.max(1) > 40) & (a.min(1) < 235)
    sel = a[mask] if mask.sum() > 50 else a
    mean = sel.mean(0)
    r, g, b = mean
    blue_ratio = float(((b > r + 20) & (b > g + 10)).mean()) if len(sel) else 0.0
    return {'size': (im.width, im.height), 'frames': n, 'megapix': round(im.width * im.height / 1e6, 2),
            'mean_rgb': [round(x) for x in mean], 'blue_ratio': round(blue_ratio, 3),
            'bytes': os.path.getsize(path)}

report = {}
for mood, names in CANDS.items():
    for nm in names[:2]:
        st, body = fetch(RAW + nm)
        print(f'{mood:7s} {nm:55s} status={st} bytes={len(body)}')
        if body:
            p = os.path.join(OUT, f'{mood}__{nm}')
            open(p, 'wb').write(body)
            try:
                info = analyze(p)
                print('        ', info)
                report[nm] = {'mood': mood, **info}
            except Exception as e:
                print('         analyze fail', e)
        time.sleep(1)

json.dump(report, open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('done')
