import json, re, time, urllib.request, urllib.error, http.cookiejar, os, urllib.parse

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

result = {'users': [], 'videos': [], 'spaces': []}
kw = urllib.parse.quote('蓝色大肥鱼')

st, body = get(f'https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword={kw}&page=1')
j = json.loads(body or '{}')
for it in ((j.get('data') or {}).get('result') or [])[:12]:
    result['users'].append({'mid': it.get('mid'), 'uname': it.get('uname'), 'fans': it.get('fans'),
                            'videos': it.get('videos'), 'sign': re.sub(r'<[^>]+>', '', str(it.get('usign') or ''))[:100]})
time.sleep(3)

st, body = get(f'https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={kw}&page=1')
j = json.loads(body or '{}')
for it in ((j.get('data') or {}).get('result') or [])[:15]:
    result['videos'].append({'bvid': it.get('bvid'), 'title': re.sub(r'<[^>]+>', '', str(it.get('title'))),
                             'author': it.get('author'), 'mid': it.get('mid'), 'pic': it.get('pic'),
                             'aid': it.get('aid')})
time.sleep(3)

GIF_RE = re.compile(r'(?:https?:)?//[a-z0-9]+\.hdslb\.com/bfs/new_dyn/[0-9a-zA-Z]+\.gif')
ANY_IMG = re.compile(r'(?:https?:)?//[a-z0-9]+\.hdslb\.com/bfs/new_dyn/[^"\\]+')
for u in result['users']:
    mid = u['mid']
    st, body = get(f'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}')
    body = body or ''
    gifs = sorted(set(GIF_RE.findall(body)))
    entry = {'mid': mid, 'uname': u['uname'], 'status': st, 'len': len(body), 'gifs': gifs}
    if body and len(body) < 300:
        entry['body'] = body
    result['spaces'].append(entry)
    if gifs:
        open(os.path.join(OUT, f'feed_{mid}.json'), 'w', encoding='utf-8').write(body)
    time.sleep(4)

with open(os.path.join(OUT, 'probe6.json'), 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print('written', os.path.join(OUT, 'probe6.json'))
