"""Audition set: same line, same pitch/rate, different Edge TTS voices."""
import subprocess, sys, os, time

PY = r"C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
OUT = r"D:\code\DSH_PlainRiceWhale\samples"
TEXT = "哼，才不是胖鲸鱼呢。主人要是想换个嗓子，就把这个名字改掉就好啦。"

VOICES = [
    ("zh-CN-XiaoyiNeural", "audition-xiaoyi-p22.mp3"),
    ("zh-CN-XiaoxiaoNeural", "audition-xiaoxiao-p22.mp3"),
    ("zh-CN-YunxiaNeural", "audition-yunxia-p22.mp3"),
    ("zh-CN-liaoning-XiaobeiNeural", "audition-xiaobei-p22.mp3"),
    ("zh-TW-HsiaoChenNeural", "audition-hsiaochen-p22.mp3"),
]

os.makedirs(OUT, exist_ok=True)
for voice, name in VOICES:
    target = os.path.join(OUT, name)
    if os.path.exists(target):
        os.remove(target)
    cmd = [PY, "-m", "edge_tts", "--voice", voice, "--pitch", "+22Hz",
           "--rate", "+0%", "--text", TEXT, "--write-media", target]
    last = "FAIL"
    for attempt in range(3):
        code = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if code == 0 and os.path.exists(target) and os.path.getsize(target) > 0:
            last = "OK  %s -> %-26s %7d B" % (voice, name, os.path.getsize(target))
            break
        last = "retry %d for %s (exit %s)" % (attempt + 1, voice, code)
        time.sleep(0.6)
    else:
        last = "FAIL %s" % voice
    print(last)
    time.sleep(0.4)
