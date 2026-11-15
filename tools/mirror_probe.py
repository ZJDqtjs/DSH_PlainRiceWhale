"""Check 镜花Mirror (co-developer) and the DS娘 site's 语音 section."""
import json
import re
import sys
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'


def get(url, headers=None, tries=2, wait=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {'User-Agent': UA, 'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(wait * (i + 2))
                continue
            return e.code, ''
        except Exception:
            time.sleep(wait)
    return None, ''


print('=== 蓝色大肥鱼.com ===')
for host in ('https://蓝色大肥鱼.com/', 'https://xn--0trq7pz0bhq8u.com/'):
    try:
        st, b = get(host)
        print(host, 'status', st, 'len', len(b or ''))
        if b:
            txt = re.sub(r'<script[\s\S]*?</script>', ' ', b)
            txt = re.sub(r'<style[\s\S]*?</style>', ' ', txt)
            txt = re.sub(r'<[^>]+>', ' ', txt)
            txt = re.sub(r'\s+', ' ', txt)
            print('  TEXT:', txt[:600])
            for kw in ('语音', '音源', 'TTS', '配音', '声音'):
                i = txt.find(kw)
                if i >= 0:
                    print(f'  [{kw}]', txt[max(0, i - 80):i + 120])
    except Exception as e:
        print(host, 'ERR', e)

print()
print('=== B站: 镜花Mirror 作品（找配音来源） ===')
# find mid via search
st, b = get('https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword=' +
            urllib.parse.quote('镜花Mirror'))
print('search status', st)
try:
    j = json.loads(b)
    for it in ((j.get('data') or {}).get('result') or [])[:5]:
        print('  USER', it.get('mid'), it.get('uname'), 'fans', it.get('fans'), '|', str(it.get('usign'))[:80])
except Exception as e:
    print('  fail', e)
