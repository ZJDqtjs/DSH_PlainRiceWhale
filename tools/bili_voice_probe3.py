"""Trace where the DS娘 voice comes from.

Checks:
1. the UP (彼岸花Channel, mid 13787349) signature + pinned dynamics
2. descriptions of their DS娘 videos (looking for voice credits)
3. the candidate voice-model videos found by search (full desc, links)
"""
import json
import os
import re
import sys
import time
import hashlib
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_voice'
os.makedirs(OUT, exist_ok=True)

MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19,
             29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
             22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]


def get(url, tries=3, wait=4):
    for i in range(tries):
        try:
            with opener.open(url, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1))
                continue
            return e.code, ''
        except Exception:
            time.sleep(wait)
    return None, ''


st, body = get('https://api.bilibili.com/x/frontend/finger/spi')
if body:
    d = json.loads(body)['data']
    for nm, key in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
        cj.set_cookie(http.cookiejar.Cookie(0, nm, d[key], None, False, '.bilibili.com', True, True, '/', True,
                                            False, None, True, None, None, {}))


def mixin_key():
    _, body = get('https://api.bilibili.com/x/web-interface/nav')
    wbi = (json.loads(body or '{}').get('data') or {}).get('wbi_img') or {}
    ik = os.path.basename(wbi.get('img_url', '')).split('.')[0]
    sk = os.path.basename(wbi.get('sub_url', '')).split('.')[0]
    return ''.join((ik + sk)[i] for i in MIXIN_TAB)[:32]


MK = mixin_key()


def sign(params):
    p = dict(params)
    p['wts'] = int(time.time())
    q = urllib.parse.urlencode([(k, re.sub(r"[!'()*]", '', str(v))) for k, v in sorted(p.items())])
    p['w_rid'] = hashlib.md5((q + MK).encode()).hexdigest()
    return urllib.parse.urlencode(p)


print('=== UP card (mid 13787349) ===')
st, body = get('https://api.bilibili.com/x/web-interface/card?mid=13787349')
try:
    d = json.loads(body)['data']['card']
    print('name:', d.get('name'))
    print('sign:', d.get('sign'))
    print('fans:', json.loads(body)['data'].get('follower'))
except Exception as e:
    print('fail', e, (body or '')[:200])

time.sleep(3)
print()
print('=== UP videos with desc (first 20) ===')
st, body = get('https://api.bilibili.com/x/space/wbi/arc/search?' + sign(
    {'mid': 13787349, 'ps': 20, 'pn': 1, 'order': 'pubdate'}))
try:
    j = json.loads(body)
    vlist = (((j.get('data') or {}).get('list') or {}).get('vlist') or [])
    for v in vlist:
        print('---', v.get('bvid'), v.get('title'))
        print('    desc:', str(v.get('description') or '')[:300].replace('\n', ' | '))
except Exception as e:
    print('fail', e, (body or '')[:300])

time.sleep(4)
print()
print('=== candidate voice-model videos ===')
for bv in ('BV1c7eE6VEMD', 'BV1n3Hf6xERq', 'BV1ZGeG6HENH', 'BV1BKYm6JEHf', 'BV1Cenc6hEtR', 'BV1Xf8P6VE4d'):
    st, body = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        d = json.loads(body)['data']
        print('---', bv, d.get('title'))
        print('    UP:', d.get('owner', {}).get('name'))
        print('    desc:', str(d.get('desc') or '')[:900].replace('\n', ' | '))
    except Exception as e:
        print('---', bv, 'fail', e)
    time.sleep(4)
