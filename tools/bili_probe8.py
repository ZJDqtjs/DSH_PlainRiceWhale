import json, re, time, urllib.request, urllib.error, http.cookiejar, os, sys, hashlib, urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_probe_out'
os.makedirs(OUT, exist_ok=True)

MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19,
             29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
             22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', UA), ('Referer', 'https://www.bilibili.com/'), ('Accept', '*/*'),
                     ('Accept-Language', 'zh-CN,zh;q=0.9'), ('Origin', 'https://www.bilibili.com')]

def get(url, tries=3, wait=4, raw=False):
    for i in range(tries):
        try:
            with opener.open(url, timeout=30) as r:
                data = r.read()
                return r.status, (data if raw else data.decode('utf-8', 'ignore'))
        except urllib.error.HTTPError as e:
            if e.code in (412, 429, 509):
                time.sleep(wait * (i + 1)); continue
            return e.code, (b'' if raw else '')
        except Exception:
            time.sleep(wait)
    return None, (b'' if raw else '')

st, body = get('https://api.bilibili.com/x/frontend/finger/spi')
if body:
    d = json.loads(body)['data']
    for nm, key in (('buvid3', 'b_3'), ('buvid4', 'b_4')):
        cj.set_cookie(http.cookiejar.Cookie(0, nm, d[key], None, False, '.bilibili.com', True, True, '/', True,
                                            False, None, True, None, None, {}))
    print('cookies ok')

st, body = get('https://api.bilibili.com/x/web-interface/nav')
nav = json.loads(body or '{}')
wbi = nav.get('data', {}).get('wbi_img', {})
img_key = os.path.basename(wbi.get('img_url', '')).split('.')[0]
sub_key = os.path.basename(wbi.get('sub_url', '')).split('.')[0]
print('nav code=', nav.get('code'), 'img_key=', bool(img_key), 'sub_key=', bool(sub_key))
orig = img_key + sub_key
mixin = ''.join(orig[i] for i in MIXIN_TAB)[:32]

def sign(params):
    params = dict(params)
    params['wts'] = int(time.time())
    items = sorted(params.items())
    q = urllib.parse.urlencode([(k, re.sub(r"[!'()*]", '', str(v))) for k, v in items])
    params['w_rid'] = hashlib.md5((q + mixin).encode()).hexdigest()
    return urllib.parse.urlencode(params)

kw = '蓝色大肥鱼'
probes = [
    ('wbi-video', 'https://api.bilibili.com/x/web-interface/wbi/search/type?' +
     sign({'search_type': 'video', 'keyword': kw, 'page': 1})),
    ('wbi-article', 'https://api.bilibili.com/x/web-interface/wbi/search/type?' +
     sign({'search_type': 'article', 'keyword': kw, 'page': 1})),
    ('wbi-dyn-search', 'https://api.bilibili.com/x/web-interface/wbi/search/type?' +
     sign({'search_type': 'video', 'keyword': kw, 'page': 1, 'order': 'pubdate'})),
    ('dyn-space-plain', 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid=14430149'),
    ('dyn-space-wbi', 'https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?' +
     sign({'host_mid': 14430149, 'offset': '', 'timezone_offset': -480, 'features': 'itemOpusStyle'})),
]

for name, url in probes:
    st, body = get(url)
    body = body or ''
    print(f'== {name} status={st} len={len(body)}')
    try:
        j = json.loads(body)
        print('   code=', j.get('code'), 'msg=', str(j.get('message'))[:60])
        data = j.get('data')
        if isinstance(data, dict) and isinstance(data.get('result'), list):
            print('   results=', len(data['result']))
        if isinstance(data, dict) and isinstance(data.get('items'), list):
            print('   items=', len(data['items']))
    except Exception:
        print('   body:', body[:200])
    time.sleep(4)
print('done')
