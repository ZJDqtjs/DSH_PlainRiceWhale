"""Where does the DS娘 voice actually come from?

Bilibili's own read-aloud feature (DeepSeek 网页版朗读) has 4 built-in voices and is
the thing most 大肥鱼 videos sample. Verify the official site's TTS surface, and
collect the practical open engines people retrain from.
"""
import json
import re
import sys
import time
import urllib.parse
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


print('=== chat.deepseek.com TTS surface ===')
for path in ('/', '/api/v0/tts', '/api/v0/voice/list'):
    st, b = get('https://chat.deepseek.com' + path)
    print(' ', path, 'status', st, 'len', len(b or ''))
    if b and len(b) < 3000:
        print('    ', re.sub(r'\s+', ' ', b)[:400])

print()
print('=== known TTS repos (for the plan) ===')
repos = [
    'index-tts/IndexTTS',
    'RVC-Boss/GPT-SoVITS',
    'fishaudio/fish-speech',
    '2noise/ChatTTS',
    'Plachtaa/VALL-E-X',
]
for r in repos:
    u = 'https://api.github.com/repos/' + r
    st, b = get(u, headers={'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
    if st == 200:
        j = json.loads(b)
        print(f'  {r:26s} ★{j.get("stargazers_count"):>7} | {str(j.get("description"))[:110]}')
    else:
        print(f'  {r:26s} status={st}')
    time.sleep(2)
