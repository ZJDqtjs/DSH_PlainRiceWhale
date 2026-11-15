import json, re, time, urllib.request, urllib.error, http.cookiejar, os, sys

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_articles'
os.makedirs(OUT, exist_ok=True)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'),
                     ('Accept', 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]

def get(url, tries=3, wait=6):
    for i in range(tries):
        try:
            with opener.open(url, timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 2)); continue
            return e.code, b''
        except Exception as e:
            time.sleep(wait); continue
    return None, None

# bootstrap buvid
st, body = get('https://api.bilibili.com/x/frontend/finger/spi', tries=2)
print('spi', st)
if body:
    try:
        d = json.loads(body.decode('utf-8'))['data']
        for name in ('b_3', 'b_4'):
            c = http.cookiejar.Cookie(0, 'buvid' + ('3' if name == 'b_3' else '4'), d[name], None, False,
                                      '.bilibili.com', True, True, '/', True, False, None, True, None, None, {})
            cj.set_cookie(c)
        print('cookies ok')
    except Exception as e:
        print('spi parse fail', e)

ids = sys.argv[1:] or ['53430860']
for aid in ids:
    for form in (f'https://www.bilibili.com/read/cv{aid}', f'https://api.bilibili.com/x/article/view?id={aid}'):
        st, body = get(form)
        if not body:
            print(f'{aid} {form} -> {st} EMPTY'); continue
        txt = body.decode('utf-8', 'ignore')
        gifs = sorted(set(re.findall(r'(?:https?:)?//i\d\.hdslb\.com/bfs/new_dyn/[0-9a-f]+\.gif', txt)))
        imgs = sorted(set(re.findall(r'(?:https?:)?//i\d\.hdslb\.com/bfs/new_dyn/[0-9a-f]+\.(?:gif|png|jpg|webp)', txt)))
        print(f'== {aid} {form} status={st} len={len(txt)} gif={len(gifs)} img={len(imgs)}')
        if gifs:
            for g in gifs:
                print('   GIF', g)
        elif imgs:
            for g in imgs[:6]:
                print('   IMG', g)
        fn = os.path.join(OUT, f'{aid}_{"html" if "read/cv" in form else "api"}.txt')
        open(fn, 'w', encoding='utf-8').write(txt)
        time.sleep(8)
