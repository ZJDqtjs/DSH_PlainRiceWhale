"""Danmaku + all UP videos: hunt for an explicit voice/配音 credit."""
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


def get(u, tries=3, wait=4, raw=False):
    for i in range(tries):
        try:
            with op.open(u, timeout=40) as r:
                data = r.read()
                return r.status, (data if raw else data.decode('utf-8', 'ignore'))
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1))
                continue
            return e.code, (b'' if raw else '')
        except Exception:
            time.sleep(wait)
    return None, (b'' if raw else '')


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


print('=== danmaku (cid 42826662862) ===')
for seg in (1, 2, 3):
    st, data = get(f'https://api.bilibili.com/x/v2/dm/web/seg.so?type=1&oid=42826662862&segment_index={seg}', raw=True)
    print('seg', seg, 'status', st, 'bytes', len(data or b''))
    if data:
        open(os.path.join(OUT, f'dm_{seg}.bin'), 'wb').write(data)
    time.sleep(2)

# also the legacy xml endpoint
st, data = get('https://api.bilibili.com/x/v1/dm/list.so?oid=42826662862', raw=True)
print('legacy xml status', st, 'bytes', len(data or b''))
if data:
    txt = data.decode('utf-8', 'ignore')
    open(os.path.join(OUT, 'dm.xml'), 'w', encoding='utf-8').write(txt)
    texts = re.findall(r'<d [^>]*>([^<]*)</d>', txt)
    print('danmaku count', len(texts))
    for t in texts[:40]:
        print('   DM', t[:120])

print()
print('=== all UP videos (pages 1-3), grep voice words ===')
for pn in (1, 2, 3):
    st, b = get('https://api.bilibili.com/x/space/wbi/arc/search?' + sign(
        {'mid': 13787349, 'ps': 30, 'pn': pn, 'order': 'pubdate'}))
    try:
        j = json.loads(b)
        vlist = (((j.get('data') or {}).get('list') or {}).get('vlist') or [])
    except Exception as e:
        print('page', pn, 'fail', e)
        continue
    print(f'-- page {pn}: {len(vlist)} videos')
    for v in vlist:
        desc = str(v.get('description') or '')
        title = str(v.get('title') or '')
        blob = title + ' ' + desc
        if re.search(r'配音|音源|音色|声线|TTS|语音|声音|调音|合成', blob):
            print('   HIT', v.get('bvid'), '|', title[:50])
            print('       ', desc.replace('\n', ' | ')[:400])
    time.sleep(5)
