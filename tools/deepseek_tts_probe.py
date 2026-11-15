"""Pin down the DeepSeek TTS voice: official read-aloud capture vs trained models."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_voice'
os.makedirs(OUT, exist_ok=True)

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

print('=== video descs ===')
for bv in ('BV1u7ng6PEvx', 'BV1BKYm6JEHf', 'BV1ZGeG6HENH', 'BV1DvHP6nEJk', 'BV1ggJe6AEiN'):
    st, b = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        d = json.loads(b)['data']
        print('---', bv, d.get('title'), '| UP', (d.get('owner') or {}).get('name'))
        print('    ', str(d.get('desc') or '').replace('\n', ' | ')[:700])
    except Exception as e:
        print('---', bv, 'fail', e)
    time.sleep(3)

print()
print('=== comments on key videos ===')
for bv, aid in (('BV1u7ng6PEvx', None), ('BV1BKYm6JEHf', None), ('BV1ZGeG6HENH', None), ('BV1J2nA6cE9y', None)):
    # resolve aid
    st, b = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        aid = json.loads(b)['data']['aid']
    except Exception:
        print('skip', bv)
        continue
    for sort in (2,):
        st, b = get(f'https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&sort={sort}&ps=20&pn=1')
        print(f'--- {bv} aid={aid} sort={sort} status={st} len={len(b or "")}')
        try:
            j = json.loads(b)
            print('    code', j.get('code'), str(j.get('message'))[:60])
            reps = (j.get('data') or {}).get('replies') or []
            for r in reps[:12]:
                msg = ((r.get('content') or {}).get('message') or '').replace('\n', ' ')
                print('    -', (r.get('member') or {}).get('uname'), ':', msg[:150])
        except Exception as e:
            print('    parse fail', e, (b or '')[:120])
    time.sleep(5)
