"""Hunt for publicly released (already-trained) 大肥鱼 / DS娘 voice models."""
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
OUT = r'D:\code\DSH_PlainRiceWhale\tools\voice_release'
os.makedirs(OUT, exist_ok=True)

MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19,
             29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
             22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                 ('Accept-Language', 'zh-CN,zh;q=0.9')]


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


print('=== 1) bowlroll 配布页（BV1ZGeG6HENH 简介里的音源包）===')
for u in ('https://bowlroll.net/file/360563',):
    st, b = get(u)
    print(' ', u, 'status', st, 'len', len(b or ''))
    if b:
        open(os.path.join(OUT, 'bowlroll_360563.html'), 'w', encoding='utf-8').write(b)
        txt = re.sub(r'<script[\s\S]*?</script>', ' ', b)
        txt = re.sub(r'<style[\s\S]*?</style>', ' ', txt)
        txt = re.sub(r'<[^>]+>', ' ', txt)
        txt = re.sub(r'\s+', ' ', txt)
        print('   TEXT:', txt[:700])
        for m in re.findall(r'href="([^"]*(?:download|file|dl)[^"]*)"', b)[:8]:
            print('   DL?', m[:140])

print()
print('=== 2) B站搜索：音源配布 / 模型下载 ===')
queries = ['大肥鱼 音源配布', 'DS娘 音源', '大肥鱼 GPT-SoVITS 模型', '大肥鱼 模型 下载',
           'DeepSeek 音源 配布', 'DS娘 soVITS 模型分享', '大肥鱼 声音模型']
for kw in queries:
    st, b = get('https://api.bilibili.com/x/web-interface/search/type?' + sign(
        {'search_type': 'video', 'keyword': kw, 'page': 1}))
    print(f'--- {kw} status={st}')
    try:
        j = json.loads(b)
        res = ((j.get('data') or {}).get('result') or [])
        for it in res[:10]:
            t = re.sub(r'<[^>]+>', '', str(it.get('title')))
            print('   ', it.get('bvid'), t[:62], '| UP', it.get('author'))
            d = str(it.get('description') or '').replace('\n', ' ')
            if re.search(r'配布|下载|模型|链接|github|网盘|huggingface', d, re.I):
                print('        DESC:', d[:200])
    except Exception as e:
        print('   fail', e, (b or '')[:120])
    time.sleep(6)
