import json, re, time, urllib.request, urllib.error, http.cookiejar, os, urllib.parse

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)
lf = open(os.path.join(OUT, 'probe5.log'), 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); lf.write(s + '\n'); lf.flush()

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]

def get(url, tries=3, wait=5):
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
    log('cookies ok')

kw = urllib.parse.quote('蓝色大肥鱼')
for search_type in ('bili_user', 'video'):
    u = f'https://api.bilibili.com/x/web-interface/search/type?search_type={search_type}&keyword={kw}&page=1'
    st, body = get(u)
    body = body or ''
    log(f'== search {search_type} status={st} len={len(body)}')
    try:
        j = json.loads(body)
        log('   code=', j.get('code'), j.get('message'))
        res = (j.get('data') or {}).get('result') or []
        for it in res[:10]:
            if search_type == 'bili_user':
                log('   USER mid=', it.get('mid'), 'uname=', it.get('uname'), 'sign=', str(it.get('usign'))[:60],
                    'fans=', it.get('fans'), 'videos=', it.get('videos'))
            else:
                t = re.sub(r'<[^>]+>', '', str(it.get('title')))
                log('   VID bvid=', it.get('bvid'), 'title=', t[:60], 'author=', it.get('author'), 'mid=', it.get('mid'))
    except Exception as e:
        log('   parse fail', e, body[:200])
    time.sleep(5)
log('DONE')
