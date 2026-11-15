import json, re, time, urllib.request, urllib.error, http.cookiejar, os, sys

sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]

def get(url, tries=3, wait=4):
    for i in range(tries):
        try:
            with opener.open(url, timeout=30) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509): time.sleep(wait * (i + 1)); continue
            return e.code, ''
        except Exception: time.sleep(wait)
    return None, ''

st, body = get('https://api.bilibili.com/x/frontend/finger/spi')
if body:
    d = json.loads(body)['data']
    for nm, key in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
        cj.set_cookie(http.cookiejar.Cookie(0, nm, d[key], None, False, '.bilibili.com', True, True, '/', True,
                                            False, None, True, None, None, {}))

mids = [14430149, 11799230, 293026389, 396434305, 3546775719774786, 44748304]
URL_RE = re.compile(r'(?:https?:)?//[a-z0-9.]+(?:hdslb|biliimg)\.com/[^"\\\s\?]+')
summary = {}
for mid in mids:
    st, body = get(f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}')
    body = body or ''
    open(os.path.join(OUT, f'feed_{mid}.json'), 'w', encoding='utf-8').write(body)
    urls = sorted(set(URL_RE.findall(body)))
    gifs = [u for u in urls if u.lower().endswith('.gif')]
    summary[mid] = (st, len(body), len(urls), gifs)
    print(f'mid={mid} status={st} len={len(body)} urls={len(urls)} gifs={len(gifs)}')
    for g in gifs[:10]:
        print('   GIF', g)
    time.sleep(4)

json.dump({str(k): v for k, v in summary.items()}, open(os.path.join(OUT, 'probe7.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('done')
