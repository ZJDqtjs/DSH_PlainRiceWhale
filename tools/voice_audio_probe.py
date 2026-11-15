"""Extract the audio track from the target video and characterise the voice.

We cannot name the engine from audio alone, but we CAN tell whether it is
1) a TTS model (flat prosody, steady pitch, no breaths),
2) a real recorded voice, or
3) an RVC/SoVITS conversion (formant shifts, robotic tail).
This produces objective numbers to back the answer.
"""
import os
import subprocess
import sys
import wave

sys.stdout.reconfigure(encoding='utf-8')
FF = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.EXE'
SRC = r'D:\code\DSH_PlainRiceWhale\tools\bili_src'
OUT = r'D:\code\DSH_PlainRiceWhale\tools\bili_voice'
os.makedirs(OUT, exist_ok=True)
mp4 = os.path.join(SRC, 'BV1NtJB6TE19.mp4')

if not os.path.exists(mp4):
    import json
    import urllib.request

    UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    H = {'User-Agent': UA, 'Referer': 'https://www.bilibili.com/'}
    req = urllib.request.Request('https://api.bilibili.com/x/player/playurl?bvid=BV1NtJB6TE19&cid=42826662862&qn=32&fnval=0',
                                 headers=H)
    with urllib.request.urlopen(req, timeout=40) as r:
        url = json.loads(r.read().decode())['data']['durl'][0]['url']
    req2 = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req2, timeout=120) as r:
        data = r.read()
    open(mp4, 'wb').write(data)
    print('downloaded', len(data))

wav = os.path.join(OUT, 'target.wav')
rc = subprocess.run([FF, '-y', '-loglevel', 'error', '-i', mp4, '-ac', '1', '-ar', '16000', wav],
                    capture_output=True, text=True)
print('ffmpeg rc', rc.returncode, rc.stderr[-200:] if rc.returncode else '')

with wave.open(wav) as w:
    n = w.getnframes()
    sr = w.getframerate()
    print('wav frames', n, 'sr', sr, 'dur', round(n / sr, 2))

try:
    import numpy as np
    with wave.open(wav) as w:
        raw = w.readframes(w.getnframes())
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    print('samples', a.size, 'peak', round(float(np.abs(a).max()), 3), 'rms', round(float(np.sqrt((a ** 2).mean())), 4))
    # silence ratio
    frame = 400
    nf = a.size // frame
    rms = np.sqrt((a[:nf * frame].reshape(nf, frame) ** 2).mean(axis=1))
    print('silent frames (<0.01):', round(float((rms < 0.01).mean()), 3))
except ImportError:
    print('numpy missing')
