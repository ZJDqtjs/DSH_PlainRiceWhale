import json, os, sys, re

sys.stdout.reconfigure(encoding='utf-8')
OUT = r'D:\code\DSH_PlainRiceWhale\tools\repo_out'

p = os.path.join(OUT, 'PC2005-cloud_dsh-pet.json')
data = json.load(open(p, encoding='utf-8'))
files = data['files']
print('files', len(files))
anim = [f for f in files if f.lower().endswith(('.gif', '.webp', '.apng', '.webm', '.mp4', '.mov'))]
print('animated', len(anim))
for f in anim:
    print('  A', f)
print('--- dirs with counts ---')
tops = {}
for f in files:
    key = '/'.join(f.split('/')[:3])
    tops[key] = tops.get(key, 0) + 1
for k, v in sorted(tops.items(), key=lambda x: -x[1])[:40]:
    print(f'  {v:4d}  {k}')
