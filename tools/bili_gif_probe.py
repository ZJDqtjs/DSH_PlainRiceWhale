import json, re, time, urllib.request, urllib.error, http.cookiejar, os, sys

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, 'probe.log'), 'w', encoding='utf-8')

def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    LOG.write(s + '\n'); LOG.flush()

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'),
                     ('Accept', '*/*'), ('Accept-Language', 'zh-CN,zh;q=0.9')]

def get(url, tries=3, wait=5):
    for i in range(tries):
        try:
            with opener.open(url, timeout=30) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 2)); continue
            return e.code, ''
        except Exception:
            time.sleep(wait); continue
    return None, ''

st, body = get('https://api.bilibili.com/x/frontend/finger/spi', tries=2)
if body:
    try:
        d = json.loads(body)['data']
        for nm, key in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
            c = http.cookiejar.Cookie(0, nm, d[key], None, False, '.bilibili.com', True, True, '/', True,
                                      False, None, True, None, None, {})
            cj.set_cookie(c)
        log('cookies ok')
    except Exception as e:
        log('spi fail', e)

GIF_RE = re.compile(r'(?:https?:)?//i\d\.hdslb\.com/bfs/new_dyn/[0-9a-f]+\.gif')
results = {}

# A) dynamic space feeds of likely posters
mids = [11835542, 3546775719774786, 7907412, 209635482]
for mid in mids:
    for offset in ('', '&offset='):
        u = f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}{offset}'
        st, body = get(u)
        if not body:
            log(f'dyn feed {mid} -> {st} empty'); continue
        gifs = sorted(set(GIF_RE.findall(body)))
        log(f'dyn feed mid={mid} status={st} len={len(body)} gifs={len(gifs)}')
        for g in gifs[:40]:
            log('   GIF', g)
        if gifs:
            results.setdefault('dyn', []).extend(gifs)
        break
    time.sleep(6)

json.dump(results, open(os.path.join(OUT, 'results.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
log('DONE')
LOG.close()
