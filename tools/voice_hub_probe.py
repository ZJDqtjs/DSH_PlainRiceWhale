"""Hunt released (already-trained) 大肥鱼 / DS娘 / DeepSeek TTS voices on model hubs.

Covers: Hugging Face model search, ModelScope, GitHub search, and a check of what
the local machine can actually run (GPU / RAM), because "用上" means inference here.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\voice_release'
os.makedirs(OUT, exist_ok=True)


def get(url, headers=None, tries=2, wait=3, raw=False):
    for i in range(tries):
        try:
            h = {'User-Agent': UA, 'Accept': '*/*'}
            h.update(headers or {})
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=45) as r:
                b = r.read()
                return r.status, (b if raw else b.decode('utf-8', 'ignore'))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(wait * (i + 2))
                continue
            try:
                eb = e.read()
            except Exception:
                eb = b''
            return e.code, (eb if raw else eb.decode('utf-8', 'ignore'))
        except Exception:
            time.sleep(wait)
    return None, (b'' if raw else '')


def hf_models(q, limit=15):
    u = 'https://huggingface.co/api/models?' + urllib.parse.urlencode(
        {'search': q, 'limit': limit, 'full': 'false', 'sort': 'downloads', 'direction': '-1'})
    st, b = get(u)
    print(f'--- HF "{q}" status={st}')
    if st != 200 or not b:
        print('    ', (b or '')[:200])
        return
    try:
        arr = json.loads(b)
    except Exception:
        print('    parse fail', b[:200])
        return
    if not arr:
        print('    (no results)')
    for m in arr[:limit]:
        print(f"    {m.get('id'):55s} dl={m.get('downloads')} likes={m.get('likes')} "
              f"updated={str(m.get('lastModified'))[:10]}")


def ms_models(q, limit=12):
    u = 'https://modelscope.cn/api/v1/dolphin/models?' + urllib.parse.urlencode(
        {'PageSize': limit, 'PageNumber': 1, 'Name': q})
    st, b = get(u, headers={'Accept': 'application/json', 'Referer': 'https://modelscope.cn/'})
    print(f'--- ModelScope "{q}" status={st}')
    if st != 200 or not b:
        print('    ', (b or '')[:200])
        return
    try:
        arr = (json.loads(b).get('Data') or {}).get('Model', {}).get('Models') or []
    except Exception:
        print('    parse fail', b[:200])
        return
    if not arr:
        print('    (no results)')
    for m in arr[:limit]:
        print(f"    {m.get('Path') or m.get('Name'):60s} dl={m.get('Downloads')} "
              f"| {str(m.get('Description'))[:70]}")


def gh_repos(q, limit=8):
    u = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode(
        {'q': q, 'sort': 'stars', 'per_page': limit})
    st, b = get(u, headers={'Accept': 'application/vnd.github+json'})
    print(f'--- GH "{q}" status={st}')
    if st != 200 or not b:
        print('    ', (b or '')[:200])
        return
    for r in (json.loads(b).get('items') or [])[:limit]:
        print(f"    {r['full_name']:45s} star={r.get('stargazers_count'):5d} "
              f"| {str(r.get('description'))[:80]}")


print('=== hardware ===')
try:
    r = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                       capture_output=True, text=True, timeout=25)
    print('  nvidia-smi rc', r.returncode, '|', (r.stdout or r.stderr or '').strip()[:300])
except Exception as e:
    print('  nvidia-smi unavailable:', e)
r = subprocess.run(['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory', '/value'],
                   capture_output=True, text=True, timeout=30)
print('  RAM:', (r.stdout or '').strip()[:120])
r = subprocess.run(['wmic', 'cpu', 'get', 'name,NumberOfCores,NumberOfLogicalProcessors', '/value'],
                   capture_output=True, text=True, timeout=30)
print('  CPU:', ' '.join((r.stdout or '').split())[:200])

print()
print('=== model hubs: 大肥鱼 / DS娘 / DeepSeek TTS ===')
for q in ('dafeiyu', '大肥鱼', 'ds娘', 'deepseek tts', 'gpt-sovits deepseek', 'indextts', 'whale voice'):
    hf_models(q)
    time.sleep(1)

for q in ('大肥鱼', 'DS娘', 'deepseek tts', 'gpt-sovits'):
    ms_models(q)
    time.sleep(1)

for q in ('大肥鱼 tts', 'deepseek 音色 gpt-sovits', 'dsh 大肥鱼 语音'):
    gh_repos(q)
    time.sleep(2)
