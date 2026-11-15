"""Check the two most likely voice-model sources + the channel's own statements."""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_voice'
os.makedirs(OUT, exist_ok=True)


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


print('=== github: 2177302423qqcom-byte/whale-voice ===')
for path in ('', '/readme', '/contents'):
    u = 'https://api.github.com/repos/2177302423qqcom-byte/whale-voice' + path
    st, b = get(u, headers={'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
    print(' ', path or '(root)', 'status', st, 'len', len(b or ''))
    if st == 200 and path == '':
        try:
            j = json.loads(b)
            print('   desc:', j.get('description'))
            print('   stars:', j.get('stargazers_count'), 'updated:', j.get('updated_at'))
            print('   default_branch:', j.get('default_branch'))
        except Exception as e:
            print('   parse', e)

st, b = get('https://raw.githubusercontent.com/2177302423qqcom-byte/whale-voice/main/README.md')
print('README status', st, 'len', len(b or ''))
if b:
    open(os.path.join(OUT, 'whale-voice-README.md'), 'w', encoding='utf-8').write(b)
    print(b[:1500])

print()
print('=== github search: whale voice / 大肥鱼 ===')
for q in ('whale-voice deepseek', '大肥鱼 语音', 'deepseek 音色 训练', 'dsh tts whale'):
    u = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode({'q': q, 'sort': 'updated', 'per_page': 6})
    st, b = get(u, headers={'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
    print(f'-- {q} status={st}')
    try:
        for it in (json.loads(b).get('items') or [])[:6]:
            print('   ', it['full_name'], '★', it['stargazers_count'], '|', str(it.get('description'))[:100])
    except Exception as e:
        print('   fail', e, (b or '')[:120])
    time.sleep(3)
