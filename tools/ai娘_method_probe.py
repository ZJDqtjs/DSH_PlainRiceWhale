"""Check method videos and sibling AI娘 accounts that may credit the TTS engine."""
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


def get(url, tries=3, wait=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://www.bilibili.com/',
                                                       'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1))
                continue
            return e.code, ''
        except Exception:
            time.sleep(wait)
    return None, ''


bvs = {
    'BV1eaaS6jETy': '方法参考（AI娘视频制作方法）',
    'BV1pGnn67EC2': 'DeepSeek鲸鱼娘在运营 首条',
    'BV1oYnB6dEUa': '9位AI娘出道成为偶像',
    'BV1NtJB6TE19': '目标视频',
    'BV1Rjar6sEj9': '鲸尾亭 公路番预告',
}
for bv, note in bvs.items():
    st, b = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        j = json.loads(b)
        d = j.get('data') or {}
        print('===', bv, note)
        print('   title:', d.get('title'))
        print('   UP:', (d.get('owner') or {}).get('name'))
        print('   desc:', str(d.get('desc') or '').replace('\n', ' | ')[:900])
    except Exception as e:
        print('===', bv, 'fail', st, e, (b or '')[:100])
    time.sleep(4)
