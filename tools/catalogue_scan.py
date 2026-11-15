"""Scan the channel's whole catalogue + co-creator for a pipeline/voice credit."""
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


KEYS = re.compile(r'教程|工作流|流程|制作|配音|音源|音色|声线|TTS|语音|AI配音|调音|声音|方法|思路')

for mid, label in ((13787349, '彼岸花Channel'), (13687439, '镜花Mirror?')):
    print(f'##### mid={mid} {label}')
    for pn in (1, 2, 3, 4):
        st, b = get('https://api.bilibili.com/x/space/wbi/arc/search?' + sign(
            {'mid': mid, 'ps': 30, 'pn': pn, 'order': 'pubdate'}))
        try:
            j = json.loads(b)
            vlist = (((j.get('data') or {}).get('list') or {}).get('vlist') or [])
        except Exception:
            print('  page', pn, 'fail', st)
            continue
        if not vlist:
            break
        print(f'  page {pn}: {len(vlist)} videos')
        for v in vlist:
            blob = str(v.get('title') or '') + ' ' + str(v.get('description') or '')
            if KEYS.search(blob):
                print('   HIT', v.get('bvid'), '|', str(v.get('title'))[:60])
                print('       ', str(v.get('description') or '').replace('\n', ' | ')[:500])
        time.sleep(5)
