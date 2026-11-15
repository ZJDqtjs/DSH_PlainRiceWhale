"""Fetch the video page HTML and pull __INITIAL_STATE__ bits + related info."""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_voice'
os.makedirs(OUT, exist_ok=True)
BV = 'BV1NtJB6TE19'

urls = [f'https://www.bilibili.com/video/{BV}/',
        f'https://m.bilibili.com/video/{BV}']
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': UA, 'Referer': 'https://www.bilibili.com/',
                                                 'Accept-Language': 'zh-CN,zh;q=0.9'})
        with urllib.request.urlopen(req, timeout=40) as r:
            b = r.read().decode('utf-8', 'ignore')
        print(u, 'len', len(b))
        fn = os.path.join(OUT, ('page_pc.html' if 'www.' in u else 'page_m.html'))
        open(fn, 'w', encoding='utf-8').write(b)
        # extract description-ish and credit-ish strings
        for kw in ('音源', '配音', 'TTS', 'so-vits', 'SoVITS', 'sovits', '声线', '音色', '调音', 'AI配音', '合成'):
            for m in re.finditer(kw, b):
                i = m.start()
                seg = re.sub(r'\s+', ' ', b[max(0, i - 120):i + 160])
                print(f'  [{kw}] {seg[:260]}')
                break
    except Exception as e:
        print('ERR', u, e)
    time.sleep(2)
