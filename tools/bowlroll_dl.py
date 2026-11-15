"""Resolve the real download URL for the UTAU Deepseek voicebank on BowlRoll.

BowlRoll gates downloads behind a POST that returns JSON {url, name}. Try the
documented-ish endpoints and report exactly what the server answers.
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\voice_release'
os.makedirs(OUT, exist_ok=True)
FILE_ID = '360563'
PAGE = f'https://bowlroll.net/file/{FILE_ID}'

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def req(url, data=None, headers=None, raw=False, tries=2, referer=PAGE):
    for i in range(tries):
        try:
            h = {'User-Agent': UA, 'Accept': '*/*',
                 'Accept-Language': 'ja,en-US;q=0.8,zh-CN;q=0.7',
                 'Referer': referer}
            h.update(headers or {})
            body = None
            if data is not None:
                body = urllib.parse.urlencode(data).encode()
                h['Content-Type'] = 'application/x-www-form-urlencoded'
            r = urllib.request.Request(url, data=body, headers=h)
            with op.open(r, timeout=40) as resp:
                b = resp.read()
                return resp.status, (b if raw else b.decode('utf-8', 'ignore'))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(3)
                continue
            try:
                eb = e.read()
            except Exception:
                eb = b''
            return e.code, (eb if raw else eb.decode('utf-8', 'ignore'))
        except Exception:
            time.sleep(3)
    return None, (b'' if raw else '')


print('=== step 1: fetch the page (sets cookies) ===')
st, b = req(PAGE)
print('page', st, 'len', len(b or ''))
for c in cj:
    print('  cookie', c.name, '=', (c.value or '')[:40])
if b:
    open(os.path.join(OUT, 'bowlroll_page.html'), 'w', encoding='utf-8').write(b)
    # look for csrf token / api hints
    import re
    for kw in ('csrf', 'token', '_token', 'dl_nonce', 'api', 'download', 'oneTime'):
        for m in re.finditer(kw, b, re.I):
            i = m.start()
            print(f'  [{kw}]', re.sub(r'\s+', ' ', b[max(0, i - 90):i + 120])[:220])
            break

print()
print('=== step 2: try download endpoints ===')
cands = [
    (f'https://bowlroll.net/file/{FILE_ID}/dl', None, {}),
    (f'https://bowlroll.net/file/{FILE_ID}/download', None, {}),
    ('https://bowlroll.net/file/download', {'id': FILE_ID}, {}),
    ('https://bowlroll.net/api/file/download', {'id': FILE_ID}, {}),
    (f'https://bowlroll.net/file/{FILE_ID}/dl', {}, {'X-Requested-With': 'XMLHttpRequest'}),
]
for url, data, extra in cands:
    st, b = req(url, data=data or ({} if data is not None else None), headers=extra)
    print(f'--- {url} data={data} -> {st} len={len(b or "")}')
    if b:
        print('    ', str(b)[:400].replace('\n', ' '))
    time.sleep(2)
