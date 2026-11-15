import json, os, sys, urllib.request, urllib.error, time, re

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\repo_out'
os.makedirs(OUT, exist_ok=True)

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(10); continue
            return e.code, ''
        except Exception:
            time.sleep(5)
    return None, ''

# 1) full media list of MerZlin repo, grouped
p = os.path.join(OUT, 'MerZlin_dsh-pet-indesktop.json')
if os.path.exists(p):
    data = json.load(open(p, encoding='utf-8'))
    files = data['files']
    media = [f for f in files if f.lower().endswith(('.gif', '.webp', '.apng', '.webm', '.png'))]
    print('total media', len(media))
    tops = {}
    for f in media:
        key = '/'.join(f.split('/')[:3])
        tops[key] = tops.get(key, 0) + 1
    for k, v in sorted(tops.items(), key=lambda x: -x[1]):
        print(f'  {v:4d}  {k}')
    print('--- gif/webp/apng only (animated) ---')
    anim = [f for f in media if f.lower().endswith(('.gif', '.webp', '.apng'))]
    for f in anim[:100]:
        print('   ', f)
    print('--- whale/fish named ---')
    for f in files:
        if re.search(r'fish|whale|jing|yu', f, re.I):
            print('   ', f)
time.sleep(2)

for rp in ['PC2005-cloud/dsh-pet', 'Alterssss/dsh-bili-whale']:
    for br in ('main', 'master'):
        st, body = get(f'https://api.github.com/repos/{rp}/git/trees/{br}?recursive=1')
        if st != 200 or not body:
            print(rp, br, 'status', st); continue
        j = json.loads(body)
        if 'tree' not in j:
            print(rp, br, 'no tree', str(j)[:100]); continue
        files = [t['path'] for t in j['tree'] if t.get('type') == 'blob']
        media = [f for f in files if f.lower().endswith(('.gif', '.webp', '.apng', '.png', '.jpg'))]
        print(f'== {rp}@{br} files={len(files)} media={len(media)}')
        for m in media[:80]:
            print('    ', m)
        json.dump({'repo': rp, 'branch': br, 'files': files},
                  open(os.path.join(OUT, rp.replace('/', '_') + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        break
    time.sleep(3)
print('done')
