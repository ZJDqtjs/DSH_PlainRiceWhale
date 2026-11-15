"""Find the voice source for the DeepSeek character in BV1NtJB6TE19.

Looks for explicit credits: video description, top comments, UP dynamics, and
related Bilibili videos that mention 音源 / 语音模型 / GPT-SoVITS / DS娘.
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


aid = 117457020783315
cid = 42826662862
BVID = 'BV1NtJB6TE19'

print('=== comments (wbi main) ===')
for mode in (3, 2):
    url = 'https://api.bilibili.com/x/v2/reply/wbi/main?' + sign(
        {'oid': aid, 'type': 1, 'mode': mode, 'pagination_str': json.dumps({'offset': ''}, separators=(',', ':')),
         'plat': 1, 'web_location': 1315875})
    st, body = get(url)
    print('mode', mode, 'status', st, 'len', len(body or ''))
    try:
        j = json.loads(body)
        print('  code', j.get('code'), str(j.get('message'))[:60])
        data = j.get('data') or {}
        replies = data.get('replies') or []
        print('  replies', len(replies))
        for r in replies[:15]:
            msg = ((r.get('content') or {}).get('message') or '').replace('\n', ' ')
            print('  -', (r.get('member') or {}).get('uname'), ':', msg[:180])
        top = data.get('top_replies') or []
        for r in top[:5]:
            msg = ((r.get('content') or {}).get('message') or '').replace('\n', ' ')
            print('  TOP', (r.get('member') or {}).get('uname'), ':', msg[:300])
    except Exception as e:
        print('  parse fail', e, (body or '')[:200])
    time.sleep(5)

print('=== search: 音源 related ===')
for kw in ('DS娘 音源', 'deepseek娘 音源', 'AI娘 音源 GPT-SoVITS', 'DS娘 语音模型'):
    q = urllib.parse.quote(kw)
    url = f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={q}&page=1'
    st, body = get(url)
    body = body or ''
    print(f'--- {kw} status={st} len={len(body)}')
    try:
        j = json.loads(body)
        res = ((j.get('data') or {}).get('result') or [])
        for it in res[:8]:
            title = re.sub(r'<[^>]+>', '', str(it.get('title')))
            print('   ', it.get('bvid'), title[:70], '| UP', it.get('author'), '| desc', str(it.get('description'))[:80].replace('\n', ' '))
    except Exception as e:
        print('   parse fail', e)
    time.sleep(6)
