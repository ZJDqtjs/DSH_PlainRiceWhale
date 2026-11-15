"""Last sweep: does the channel or its co-creation group ever credit the TTS engine?"""
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
MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19,
             29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
             22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*')]


def get(u, tries=3, wait=4):
    for i in range(tries):
        try:
            with op.open(u, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1))
                continue
            return e.code, ''
        except Exception:
            time.sleep(wait)
    return None, ''


st, b = get('https://api.bilibili.com/x/frontend/finger/spi')
if b:
    d = json.loads(b)['data']
    for nm, k in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
        cj.set_cookie(http.cookiejar.Cookie(0, nm, d[k], None, False, '.bilibili.com', True, True, '/', True,
                                            False, None, True, None, None, {}))


def mk():
    _, b = get('https://api.bilibili.com/x/web-interface/nav')
    wbi = (json.loads(b or '{}').get('data') or {}).get('wbi_img') or {}
    ik = os.path.basename(wbi.get('img_url', '')).split('.')[0]
    sk = os.path.basename(wbi.get('sub_url', '')).split('.')[0]
    return ''.join((ik + sk)[i] for i in MIXIN_TAB)[:32]


MK = mk()


def sign(p):
    p = dict(p)
    p['wts'] = int(time.time())
    q = urllib.parse.urlencode([(k, re.sub(r"[!'()*]", '', str(v))) for k, v in sorted(p.items())])
    p['w_rid'] = hashlib.md5((q + MK).encode()).hexdigest()
    return urllib.parse.urlencode(p)


for kw in ('彼岸花Channel 制作', '鱼人众 语音 制作', 'DS娘 配音 教程', '大肥鱼 配音 教程'):
    st, b = get('https://api.bilibili.com/x/web-interface/search/type?' + sign(
        {'search_type': 'video', 'keyword': kw, 'page': 1}))
    print('==', kw, 'status', st)
    try:
        j = json.loads(b)
        res = ((j.get('data') or {}).get('result') or [])
        print('   code', j.get('code'), 'results', len(res))
        for it in res[:8]:
            t = re.sub(r'<[^>]+>', '', str(it.get('title')))
            print('   ', it.get('bvid'), t[:60], '| UP', it.get('author'))
    except Exception as e:
        print('   fail', e, (b or '')[:120])
    time.sleep(6)

print()
print('=== UP dynamics retry ===')
for feat in ('itemOpusStyle', ''):
    st, b = get('https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?' + sign(
        {'host_mid': 13787349, 'timezone_offset': -480, 'features': feat}))
    print(' features=', feat, 'status', st, 'len', len(b or ''))
    try:
        j = json.loads(b)
        print('   code', j.get('code'), 'items', len(((j.get('data') or {}).get('items') or [])))
    except Exception:
        pass
    time.sleep(4)
