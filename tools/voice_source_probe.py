"""Find the DS娘 / DeepSeekTTS voice source: the fan project site + GitHub repos."""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'


def get(url, tries=2, wait=3, headers=None):
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


print('=== deepseekchan.com ===')
st, body = get('https://deepseekchan.com/')
print('status', st, 'len', len(body or ''))
if body:
    open(r'D:\code\DSH_PlainRiceWhale\tools\bili_voice\deepseekchan.html', 'w', encoding='utf-8').write(body)
    for kw in ('tts', 'TTS', '语音', '音色', 'voice', 'sovits', 'github'):
        idx = body.find(kw)
        if idx >= 0:
            print(f'  [{kw}] ...', re.sub(r'\s+', ' ', body[max(0, idx - 80):idx + 120])[:220])
    links = sorted(set(re.findall(r'https?://[^\s"\'<>]+', body)))
    print('  links:', len(links))
    for l in links[:25]:
        print('   ', l[:140])

print()
print('=== github search ===')
for q in ('deepseek chan voice tts', 'deepseekchan', 'DeepSeekTTS', 'DS娘'):
    u = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode({'q': q, 'sort': 'stars', 'per_page': 8})
    st, body = get(u, headers={'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
    print(f'--- {q} status={st}')
    try:
        j = json.loads(body)
        for it in (j.get('items') or [])[:8]:
            print('   ', it['full_name'], '★', it['stargazers_count'], '|', str(it.get('description'))[:110])
    except Exception as e:
        print('   parse fail', e, (body or '')[:160])
    time.sleep(3)
