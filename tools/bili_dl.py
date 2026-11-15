import json, re, time, urllib.request, urllib.error, http.cookiejar, os, sys

sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
DL = r'D:\code\DSH_PlainRiceWhale\tools\bili_src'
os.makedirs(DL, exist_ok=True)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]

def request_raw(url, tries=3, wait=4):
    for i in range(tries):
        try:
            with opener.open(urllib.request.Request(url), timeout=120) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1)); continue
            return e.code, b''
        except Exception:
            time.sleep(wait)
    return None, b''

st, body = request_raw('https://api.bilibili.com/x/frontend/finger/spi')
if body:
    d = json.loads(body)['data']
    for nm, key in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
        cj.set_cookie(http.cookiejar.Cookie(0, nm, d[key], None, False, '.bilibili.com', True, True, '/', True,
                                            False, None, True, None, None, {}))
    print('cookies ok')

V = {
    'BV1JyaT6ME5i': 42172287626,
    'BV1FWpj63E92': 42648145242,
    'BV1q2nW6DEaf': None,
    'BV1aEnA6JECB': None,
    'BV1SHnc6zEPP': None,
}
# resolve cids where missing
for bv, cid in list(V.items()):
    if cid is None:
        st, body = request_raw(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
        try:
            d = (json.loads(body or '{}').get('data') or {})
            V[bv] = (d.get('pages') or [{}])[0].get('cid')
            print(bv, 'cid', V[bv], str(d.get('title'))[:40])
        except Exception:
            print(bv, 'resolve fail')
        time.sleep(3)

for bv, cid in V.items():
    if not cid:
        continue
    st, body = request_raw(f'https://api.bilibili.com/x/player/playurl?bvid={bv}&cid={cid}&qn=32&fnval=0')
    try:
        u = json.loads(body)['data']['durl'][0]['url']
    except Exception:
        print(bv, 'no durl'); continue
    st2, data = request_raw(u)
    path = os.path.join(DL, f'{bv}.mp4')
    if data:
        open(path, 'wb').write(data)
        print(f'{bv}: {len(data)} bytes -> {path}')
    else:
        print(f'{bv}: download failed status={st2}')
    time.sleep(2)
