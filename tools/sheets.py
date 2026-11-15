import os, subprocess, sys, re

sys.stdout.reconfigure(encoding='utf-8')
FF = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.EXE'
SRC = r'D:\code\DSH_PlainRiceWhale\tools\bili_src'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_sheets'
os.makedirs(OUT, exist_ok=True)

def probe_duration(src):
    p = subprocess.run([FF, '-i', src], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', p.stderr)
    if not m:
        return 0.0
    h, mm, s = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(s)

def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if p.returncode != 0:
        print('  FAIL', p.stderr.strip()[-300:])
    return p.returncode

for fn in sorted(os.listdir(SRC)):
    if not fn.endswith('.mp4'):
        continue
    src = os.path.join(SRC, fn)
    dur = probe_duration(src)
    if dur <= 0:
        print(fn, 'duration unknown'); continue
    fps = max(16.0 / dur, 0.02)
    sheet = os.path.join(OUT, fn.replace('.mp4', '_sheet.jpg'))
    vf = f'fps={fps:.6f},scale=320:-1,tile=4x4:padding=4:color=black'
    rc = run([FF, '-y', '-loglevel', 'error', '-i', src, '-vf', vf, '-frames:v', '1', '-q:v', '4', sheet])
    print(f'{fn} dur={dur:.1f}s fps={fps:.4f} rc={rc} exists={os.path.exists(sheet)} '
          f'size={os.path.getsize(sheet) if os.path.exists(sheet) else 0}')
