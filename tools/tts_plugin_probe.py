"""Inspect the DSH TTS plugins and hunt actually installable pretrained voice weights."""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\voice_release'
os.makedirs(OUT, exist_ok=True)


def get(url, headers=None, tries=2, wait=4, raw=False):
    for i in range(tries):
        try:
            h = {'User-Agent': UA, 'Accept': '*/*'}
            h.update(headers or {})
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=45) as r:
                b = r.read()
                return r.status, (b if raw else b.decode('utf-8', 'ignore'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(wait * (i + 3))
                continue
            try:
                eb = e.read()
            except Exception:
                eb = b''
            return e.code, (eb if raw else eb.decode('utf-8', 'ignore'))
        except Exception:
            time.sleep(wait)
    return None, (b'' if raw else '')


REPOS = ['wterwt/dsh-sovits-widget', 'fulan0721/dafish-voice-system',
         '18862258568qz-commits/deepseek-plugin-collection-bluefishovo',
         'zouxinhao594-alt/fatfish-qq-bot']
for repo in REPOS:
    print('=' * 70)
    print('REPO', repo)
    st, b = get(f'https://api.github.com/repos/{repo}',
                headers={'Accept': 'application/vnd.github+json'})
    if st == 200:
        j = json.loads(b)
        print('  stars', j.get('stargazers_count'), 'push', str(j.get('pushed_at'))[:10],
              'lang', j.get('language'), 'lic', (j.get('license') or {}).get('spdx_id'))
        print('  desc:', str(j.get('description'))[:200])
    else:
        print('  meta status', st, (b or '')[:150])
    for br in ('main', 'master'):
        st, rd = get(f'https://raw.githubusercontent.com/{repo}/{br}/README.md')
        if st == 200 and rd:
            open(os.path.join(OUT, repo.replace('/', '_') + '_README.md'), 'w',
                 encoding='utf-8').write(rd)
            print(f'  README/{br} len={len(rd)}')
            txt = re.sub(r'\n{3,}', '\n\n', rd)
            print(txt[:2600])
            break
    else:
        print('  no README found')
    time.sleep(3)

print()
print('#' * 70)
print('=== HF: released sovits/vits voice weights ===')
for q in ('sovits', 'gpt-sovits', 'zh voice sovits', 'vits chinese anime'):
    u = 'https://huggingface.co/api/models?' + urllib.parse.urlencode(
        {'search': q, 'limit': 12, 'sort': 'downloads', 'direction': '-1'})
    st, b = get(u)
    print(f'--- HF "{q}" status={st}')
    if st == 200 and b:
        for m in json.loads(b)[:12]:
            print(f"    {m.get('id'):58s} dl={m.get('downloads')} likes={m.get('likes')}")
    time.sleep(2)
