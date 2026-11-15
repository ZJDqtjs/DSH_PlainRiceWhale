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
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1)); continue
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

GIF_RE = re.compile(r'(?:https?:)?//[a-z0-9.]+hdslb\.com/[^"\\\s\?]+\.gif', re.I)
IMG_RE = re.compile(r'(?:https?:)?//[a-z0-9.]+hdslb\.com/bfs/new_dyn/[^"\\\s\?]+\.(?:gif|jpg|png|webp)', re.I)

# resolve aid and crawl comments
bvs = ['BV1JyaT6ME5i', 'BV1FWpj63E92', 'BV1aEnA6JECB', 'BV1SHnc6zEPP', 'BV1q2nW6DEaf', 'BV1P4Je6HE36',
       'BV1t6nu6bEsf', 'BV1ckn26XEr5']
collected = {}
for bv in bvs:
    st, body = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        j = json.loads(body or '{}')
        d = j.get('data') or {}
        aid = d.get('aid')
        print(f'== {bv} aid={aid} title={str(d.get("title"))[:48]}')
    except Exception:
        print(bv, 'view fail'); continue
    if not aid:
        continue
    for pn in (1, 2):
        st, body = get(f'https://api.bilibili.com/x/v2/reply?type=1&oid={aid}&sort=2&ps=49&pn={pn}')
        body = body or ''
        g = sorted(set(GIF_RE.findall(body)))
        im = sorted(set(IMG_RE.findall(body)))
        print(f'   reply pn={pn} status={st} len={len(body)} gif={len(g)} newdynimg={len(im)}')
        for x in g[:10]:
            print('      GIF', x)
        collected.setdefault(bv, {'aid': aid, 'gifs': [], 'imgs': []})
        collected[bv]['gifs'] += g
        collected[bv]['imgs'] += im
        time.sleep(3)
    time.sleep(3)

json.dump(collected, open(os.path.join(OUT, 'comments.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# tooling check
print('--- tooling ---')
try:
    import imageio_ffmpeg
    print('imageio_ffmpeg', imageio_ffmpeg.get_ffmpeg_exe())
except Exception as e:
    print('no imageio_ffmpeg:', e)
for mod in ('imageio', 'PIL', 'numpy'):
    try:
        m = __import__(mod)
        print(mod, getattr(m, '__version__', '?'))
    except Exception as e:
        print('no', mod, e)
import shutil
print('ffmpeg on PATH:', shutil.which('ffmpeg'))
print('done')
