"""Extract a voiced segment from the target video and characterise pitch/prosody.

Goal: give the user objective evidence about what kind of voice it is
(TTS model vs recorded vs converted), since the video itself credits no engine.
"""
import os
import sys
import wave
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
WAV = r'D:\code\DSH_PlainRiceWhale\tools\bili_voice\target.wav'

with wave.open(WAV) as w:
    sr = w.getframerate()
    raw = w.readframes(w.getnframes())
a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

# find the loudest 8-second window (likely dialogue/singing), then analyse it
win = sr * 8
hop = sr * 2
best, best_i = -1, 0
for i in range(0, max(1, a.size - win), hop):
    seg = a[i:i + win]
    e = float(np.sqrt((seg ** 2).mean()))
    if e > best:
        best, best_i = e, i
seg = a[best_i:best_i + win]
print(f'window at {best_i/sr:.1f}s  rms={best:.4f}')

# frame-wise pitch via autocorrelation, 40ms hop 20ms
frame = int(sr * 0.04)
hop_f = int(sr * 0.02)
f0s = []
for i in range(0, len(seg) - frame, hop_f):
    fr = seg[i:i + frame]
    if np.sqrt((fr ** 2).mean()) < 0.02:
        continue
    fr = fr - fr.mean()
    corr = np.correlate(fr, fr, mode='full')[frame - 1:]
    corr /= (corr[0] + 1e-9)
    lo = int(sr / 400)
    hi = int(sr / 70)
    if hi >= len(corr):
        continue
    peak = int(np.argmax(corr[lo:hi]) + lo)
    if corr[peak] > 0.3:
        f0s.append(sr / peak)

if f0s:
    f0 = np.array(f0s)
    print('voiced frames', len(f0))
    print('median F0 %.1f Hz  mean %.1f  p10 %.1f  p90 %.1f' % (np.median(f0), f0.mean(),
                                                               np.percentile(f0, 10), np.percentile(f0, 90)))
    semis = 12 * np.log2(f0 / np.median(f0))
    print('pitch spread (p90-p10 semitones) %.2f' % ((12 * np.log2(np.percentile(f0, 90) / np.percentile(f0, 10)))))
    print('frame-to-frame jitter (semitones) %.3f' % float(np.abs(np.diff(semis)).mean()))
else:
    print('no voiced frames')
