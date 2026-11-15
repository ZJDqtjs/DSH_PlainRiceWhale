import json, os, sys, urllib.request, urllib.error, time

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\repo_out'
RAW = 'https://raw.githubusercontent.com/PC2005-cloud/dsh-pet/main/'

def fetch(url, tries=3, binary=False):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b''
            time.sleep(4)
        except Exception:
            time.sleep(4)
    return None, b''

d = json.load(open(os.path.join(OUT, 'PC2005-cloud_dsh-pet.json'), encoding='utf-8'))
files = d['files']
for cand in ('README.md', 'LICENSE', 'dsh-pet/README.md', 'LICENSE.md', 'NOTICE'):
    if cand in files:
        st, body = fetch(RAW + cand)
        print(f'== {cand} status={st} len={len(body)}')
        if cand == 'LICENSE' or cand == 'LICENSE.md':
            print(body[:600].decode('utf-8', 'ignore'))
        time.sleep(2)

# look for manifest describing animations
man = [f for f in files if f.lower().endswith(('.json', '.yaml', '.yml', '.ts', '.js', '.md'))]
print('--- candidate manifests ---')
for f in man:
    if any(k in f.lower() for k in ('manifest', 'animation', 'preview', 'asset', 'config', 'README', 'anim')):
        print('  ', f)

# download one gif to check
test = 'dsh-pet/assets/preview/chi-baifan.gif'
st, body = fetch(RAW + test)
print('test gif', st, len(body))
if body:
    open(os.path.join(OUT, 'chi-baifan.gif'), 'wb').write(body)
