"""Probe whale-audio cached clips: duration + voiced F0 median.

F0 of zh-CN-XiaoyiNeural at +22 Hz is ~340 Hz (docs/released-voice-models.md).
Windows Huihui (SAPI / Web Speech) sits far lower and rougher.
"""
import os, subprocess, tempfile, sys
import numpy as np

FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.EXE"
CACHE = os.path.join(os.path.expanduser("~"), ".dsh", "whale-audio")
SR = 16000


def load(path):
    tmp = tempfile.NamedTemporaryFile(suffix=".raw", delete=False).name
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR),
                    "-f", "s16le", tmp], check=True, capture_output=True)
    raw = open(tmp, "rb").read()
    os.unlink(tmp)
    x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    return x


def f0_of_frame(frame):
    """Autocorrelation pitch estimate for one 40 ms frame; None if unvoiced."""
    n = len(frame)
    if n < 400:
        return None
    sig = frame - frame.mean()
    rms = float(np.sqrt(np.mean(sig ** 2)))
    if rms < 0.012:
        return None
    sig = sig * np.hanning(n)
    ac = np.correlate(sig, sig, mode="full")[n - 1:]
    if ac[0] <= 0:
        return None
    ac = ac / ac[0]
    lo = int(SR / 500)   # 500 Hz ceiling
    hi = int(SR / 80)    # 80 Hz floor
    seg = ac[lo:hi]
    if seg.size == 0:
        return None
    peak = int(np.argmax(seg)) + lo
    if ac[peak] < 0.30:
        return None
    # parabolic interpolation
    if 0 < peak < len(ac) - 1:
        a, b, c = ac[peak - 1], ac[peak], ac[peak + 1]
        d = (a - 2 * b + c)
        shift = 0.5 * (a - c) / d if d != 0 else 0.0
        peak = peak + shift
    return SR / peak


def probe(path, label):
    if os.path.getsize(path) == 0:
        print("%-46s  EMPTY FILE (0 bytes) — 解码必然失败" % label)
        return
    try:
        x = load(path)
    except Exception as error:
        print("%-46s  DECODE FAILED: %s" % (label, error.__class__.__name__))
        return
    dur = len(x) / SR
    win = int(0.04 * SR)
    hop = int(0.02 * SR)
    vals = []
    for s in range(0, max(0, len(x) - win), hop):
        f = f0_of_frame(x[s:s + win])
        if f:
            vals.append(f)
    arr = np.array(vals) if vals else np.array([0.0])
    med = float(np.median(arr)) if vals else 0.0
    p25, p75 = (float(np.percentile(arr, 25)), float(np.percentile(arr, 75))) if vals else (0, 0)
    print("%-46s %5.1fs  bytes=%8d  voiced=%4d  F0 median=%6.1f Hz  p25-p75=%6.1f-%6.1f"
          % (label, dur, os.path.getsize(path), len(vals), med, p25, p75))


def main():
    files = []
    if os.path.isdir(CACHE):
        for fn in sorted(os.listdir(CACHE)):
            if fn.endswith(".mp3"):
                files.append((os.path.join(CACHE, fn), fn))
    print("== whale-audio cache (%s) ==" % CACHE)
    for path, fn in files:
        probe(path, fn[:40])
    extra = sys.argv[1:]
    if extra:
        print("== extra files ==")
        for p in extra:
            probe(p, os.path.basename(p))


main()
