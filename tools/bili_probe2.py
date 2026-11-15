import json, re, time, urllib.request, urllib.error, http.cookiejar, os

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)
log_f = open(os.path.join(OUT, 'probe2.log'), 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); log_f.write(s + '\n'); log_f.flush()

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*')]

def get(url, tries=2, wait=6):
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
GIF_RE = re.compile(r'(?:https?:)?//i\d\.hdslb\.com/bfs/new_dyn/[0-9a-f]+\.gif')
IMG_RE = re.compile(r'(?:https?:)?//i\d\.hdslb\.com/bfs/new_dyn/[0-9a-f]+\.(?:gif|jpg|png|webp)')

urls = [
    ('dyn-search-type', f'https://api.bilibili.com/x/polymer/web-dynamic/v1/search/type?keyword={kw}&search_type=video&page=1'),
    ('dyn-search-topic', f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/topic?topic_name={kw}&page=1'),
    ('opus-dyn', 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid=11835542&offset=&page=1'),
]
for name, u in urls:
    st, body = get(u)
    gifs = sorted(set(GIF_RE.findall(body or '')))
    log(f'{name} status={st} len={len(body or "")} gifs={len(gifs)}')
    if gifs:
        for g in gifs[:30]: log('  GIF', g)
    if body and len(body) < 600:
        log('   body:', body[:400])
    time.sleep(6)
log('DONE')
