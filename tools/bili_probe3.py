import json, re, time, urllib.request, urllib.error, http.cookiejar, os, urllib.parse

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)
lf = open(os.path.join(OUT, 'probe3.log'), 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); lf.write(s + '\n'); lf.flush()

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
kw2 = urllib.parse.quote('大肥鱼')
EMOTE_RE = re.compile(r'(?:https?:)?//i\d\.hdslb\.com/bfs/emote/[0-9a-zA-Z]+\.(?:gif|png|webp)')
GIF_RE = re.compile(r'(?:https?:)?//i\d\.hdslb\.com/bfs/new_dyn/[0-9a-f]+\.gif')

probes = [
    ('emote-suggest', f'https://api.bilibili.com/x/emote/suggest?keyword={kw2}&type=0'),
    ('emote-package-index', f'https://api.bilibili.com/x/emote/package/index?business=reply'),
    ('emote-search', f'https://api.bilibili.com/x/emote/search?keyword={kw2}&page=1&page_size=50'),
    ('article-search-gif', f'https://api.bilibili.com/x/web-interface/wbi/search/type?search_type=article&keyword={kw2}%20gif&page=1'),
    ('dynamic-topic', f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/topic?topic_name={kw}&page=1'),
]
for name, u in probes:
    st, body = get(u)
    body = body or ''
    log(f'== {name} status={st} len={len(body)}')
    em = sorted(set(EMOTE_RE.findall(body)))
    gf = sorted(set(GIF_RE.findall(body)))
    log(f'   emotes={len(em)} new_dyn_gifs={len(gf)}')
    for x in em[:15]: log('   EMOTE', x)
    for x in gf[:15]: log('   GIF', x)
    if len(body) < 500:
        log('   body:', body)
    else:
        try:
            j = json.loads(body)
            log('   code=', j.get('code'), 'msg=', j.get('message'))
        except Exception:
            pass
    time.sleep(5)
log('DONE')
