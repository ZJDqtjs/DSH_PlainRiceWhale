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
                     ('Accept-Language', 'zh-CN,zh;q=0.9')]

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

def mixin_key():
    st, body = get('https://api.bilibili.com/x/web-interface/nav')
    nav = json.loads(body or '{}')
    wbi = (nav.get('data') or {}).get('wbi_img') or {}
    ik = os.path.basename(wbi.get('img_url', '')).split('.')[0]
    sk = os.path.basename(wbi.get('sub_url', '')).split('.')[0]
    return ''.join((ik + sk)[i] for i in MIXIN_TAB)[:32]

MK = mixin_key()
def sign(params):
    p = dict(params); p['wts'] = int(time.time())
    q = urllib.parse.urlencode([(k, re.sub(r"[!'()*]", '', str(v))) for k, v in sorted(p.items())])
    p['w_rid'] = hashlib.md5((q + MK).encode()).hexdigest()
    return urllib.parse.urlencode(p)

URL_RE = re.compile(r'(?:https?:)?//[a-z0-9.]+(?:hdslb|biliimg)\.com/[^"\\\s\?]+')

bvs = ['BV1FWpj63E92', 'BV1SHnc6zEPP', 'BV1P4Je6HE36', 'BV1aEnA6JECB', 'BV1JyaT6ME5i', 'BV1q2nW6DEaf']
for bv in bvs:
    st, body = get(f'https://api.bilibili.com/x/web-interface/view?bvid={bv}')
    try:
        j = json.loads(body or '{}')
    except Exception:
        print(bv, 'parse fail', st); continue
    d = j.get('data') or {}
    desc = str(d.get('desc') or '')
    print(f'== {bv} code={j.get("code")} title={d.get("title")}')
    print('   desc:', desc[:600].replace('\n', ' | '))
    links = re.findall(r'https?://[^\s，。、）)]+', desc)
    if links:
        print('   LINKS:', links[:10])
    time.sleep(3)
print('done')
