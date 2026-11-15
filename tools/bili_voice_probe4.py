"""Full descriptions of the candidate voice-source videos + UP dynamics + repos."""
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


print('=== candidate voice videos: full desc ===')
for bv in ('BV1PPnr65EtU', 'BV1J2nA6cE9y', 'BV1Zph86oELe', 'BV18Dnb6WEk9', 'BV1yBH36aERh', 'BV1BKYm6JEHf'):
    st, b = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        d = json.loads(b)['data']
        print('---', bv, '|', d.get('title'))
        print('    UP:', d.get('owner', {}).get('name'))
        print('    DESC:', str(d.get('desc') or '').replace('\n', ' | ')[:1200])
    except Exception as e:
        print('---', bv, 'fail', e)
    time.sleep(4)

print()
print('=== UP dynamics (13787349) ===')
st, b = get('https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?' + sign(
    {'host_mid': 13787349, 'timezone_offset': -480, 'features': 'itemOpusStyle'}))
print('status', st, 'len', len(b or ''))
try:
    j = json.loads(b)
    print('code', j.get('code'), 'items', len(((j.get('data') or {}).get('items') or [])))
    for it in (((j.get('data') or {}).get('items') or []))[:10]:
        mod = it.get('modules', {}).get('module_dynamic', {})
        major = (mod.get('major') or {})
        txt = ''
        if major.get('opus'):
            txt = str((major['opus'].get('summary') or {}).get('text') or '')[:200]
        elif mod.get('desc'):
            txt = str(mod['desc'].get('text') or '')[:200]
        print('  -', str(it.get('id_str')), '|', txt.replace('\n', ' '))
except Exception as e:
    print('  fail', e, (b or '')[:200])
