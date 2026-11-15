import json, os, sys, urllib.request, urllib.error, time

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
            if e.code == 403:
                time.sleep(10); continue
            return e.code, ''
        except Exception:
            time.sleep(5)
    return None, ''

repos = ['Alterssss/dsh-bili-whale', 'MerZlin/dsh-pet-indesktop', 'YOYOLnFu/dsh-bili-pond']
for rp in repos:
    st, body = get(f'https://api.github.com/repos/{rp}')
    print(f'== {rp} status={st}')
    if not body:
        continue
    try:
        j = json.loads(body)
        print('   default_branch=', j.get('default_branch'), 'size=', j.get('size'), 'desc=', str(j.get('description'))[:80])
    except Exception as e:
        print('   parse fail', e)
    time.sleep(2)

for rp in repos:
    for br in ('main', 'master'):
        st, body = get(f'https://api.github.com/repos/{rp}/git/trees/{br}?recursive=1')
        if st != 200 or not body:
            continue
        try:
            j = json.loads(body)
        except Exception:
            continue
        if 'tree' not in j:
            continue
        files = [t['path'] for t in j['tree'] if t.get('type') == 'blob']
        media = [f for f in files if f.lower().endswith(('.gif', '.png', '.webp', '.webm', '.apng'))]
        print(f'== {rp}@{br} files={len(files)} media={len(media)}')
        for m in media[:60]:
            print('    ', m)
        json.dump({'repo': rp, 'branch': br, 'files': files},
                  open(os.path.join(OUT, rp.replace('/', '_') + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        break
    time.sleep(2)
print('done')
