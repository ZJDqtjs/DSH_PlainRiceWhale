"""Gather everything Bilibili exposes about BV1NtJB6TE19 for the TTS provenance question."""
import json
import os
import sys
import time
import hashlib
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar

sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
BVID = 'BV1NtJB6TE19'
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
    print('cookies ok')


def mixin_key():
    st, body = get('https://api.bilibili.com/x/web-interface/nav')
    wbi = (json.loads(body or '{}').get('data') or {}).get('wbi_img') or {}
    ik = os.path.basename(wbi.get('img_url', '')).split('.')[0]
    sk = os.path.basename(wbi.get('sub_url', '')).split('.')[0]
    return ''.join((ik + sk)[i] for i in MIXIN_TAB)[:32]


MK = mixin_key()


def sign(params):
    p = dict(params)
    p['wts'] = int(time.time())
    q = urllib.parse.urlencode([(k, __import__('re').sub(r"[!'()*]", '', str(v))) for k, v in sorted(p.items())])
    p['w_rid'] = hashlib.md5((q + MK).encode()).hexdigest()
    return urllib.parse.urlencode(p)


# view (for aid/cid/desc/subtitle)
st, body = get(f'https://api.bilibili.com/x/web-interface/view?bvid={BVID}')
view = json.loads(body)
aid = view['data']['aid']
cid = view['data']['cid']
print('aid', aid, 'cid', cid)
print('subtitle key:', json.dumps(view['data'].get('subtitle'), ensure_ascii=False)[:300])

# tags
st, body = get(f'https://api.bilibili.com/x/tag/archive/tags?bvid={BVID}')
print('== tags status', st)
try:
    for t in json.loads(body).get('data') or []:
        print('   TAG', t.get('tag_name'), '| id', t.get('tag_id'), '| use', t.get('use'))
except Exception as e:
    print('   parse fail', e, body[:200])

# comments (top, hot)
for sort in (2, 0):
    st, body = get(f'https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&sort={sort}&ps=30&pn=1')
    body = body or ''
    print(f'== replies sort={sort} status={st} len={len(body)}')
    try:
        j = json.loads(body)
        print('   code', j.get('code'), j.get('message'))
        reps = (j.get('data') or {}).get('replies') or []
        print('   count', len(reps))
        for r in reps[:20]:
            msg = (r.get('content') or {}).get('message', '')
            print('   -', r.get('member', {}).get('uname'), ':', msg[:160].replace('\n', ' '))
    except Exception as e:
        print('   parse fail', e, body[:200])
    time.sleep(4)

# UP's video list
st, body = get('https://api.bilibili.com/x/space/wbi/arc/search?' + sign(
    {'mid': 13787349, 'ps': 10, 'pn': 1, 'order': 'pubdate'}))
print('== up arcs status', st)
try:
    j = json.loads(body)
    print('   code', j.get('code'), j.get('message'))
    vlist = (((j.get('data') or {}).get('list') or {}).get('vlist') or [])
    for v in vlist[:10]:
        print('   VID', v.get('bvid'), v.get('title'), '|', v.get('created'))
except Exception as e:
    print('   parse fail', e, body[:300])
