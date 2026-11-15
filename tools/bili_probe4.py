import json, re, time, urllib.request, urllib.error, http.cookiejar, os, urllib.parse, hashlib

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)
lf = open(os.path.join(OUT, 'probe4.log'), 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); lf.write(s + '\n'); lf.flush()

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]

def get(url, tries=2, wait=5):
    for i in range(tries):
        try:
            with opener.open(url, timeout=30) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509): time.sleep(wait); continue
            return e.code, ''
        except Exception: time.sleep(wait)
    return None, ''

st, body = get('https://api.bilibili.com/x/frontend/finger/spi')
if body:
    d = json.loads(body)['data']
    for nm, key in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
        cj.set_cookie(http.cookiejar.Cookie(0, nm, d[key], None, False, '.bilibili.com', True, True, '/', True,
                                            False, None, True, None, None, {}))
    log('cookies ok')

kw = urllib.parse.quote('蓝色大肥鱼')
GIF_RE = re.compile(r'(?:https?:)?//[a-z0-9]+\.hdslb\.com/[^"\s\\)]+?\.gif')
ANYOPT = re.compile(r'(?:https?:)?//[a-z0-9]+\.hdslb\.com/[^"\s\\)]+?\.(?:gif|webp|png|jpg)')

targets = [
    ('search-article-html', f'https://search.bilibili.com/article?keyword={kw}'),
    ('search-all-html', f'https://search.bilibili.com/all?keyword={kw}'),
    ('api-search-article', f'https://api.bilibili.com/x/web-interface/search/type?search_type=article&keyword={kw}&page=1'),
    ('api-search-video', f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={kw}&page=1'),
]
for name, u in targets:
    st, body = get(u)
    body = body or ''
    log(f'== {name} status={st} len={len(body)}')
    gifs = sorted(set(GIF_RE.findall(body)))
    log(f'   gif urls={len(gifs)}')
    for g in gifs[:20]: log('   GIF', g)
    if body and len(body) < 400:
        log('   body:', body)
    elif body:
        open(os.path.join(OUT, f'{name}.html'), 'w', encoding='utf-8').write(body)
        try:
            j = json.loads(body)
            log('   code=', j.get('code'), 'msg=', j.get('message'))
            data = j.get('data') or {}
            res = data.get('result') if isinstance(data, dict) else None
            if isinstance(res, list):
                for item in res[:12]:
                    log('    -', str(item.get('title', ''))[:70].replace('<em class="keyword">', '').replace('</em>', ''),
                        '| id=', item.get('id') or item.get('aid'), '| pic=', str(item.get('pic', ''))[:80])
        except Exception:
            log('   (not json)')
    time.sleep(6)
log('DONE')
