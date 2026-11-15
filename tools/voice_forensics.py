"""Forensics: does the cache contain the clip for each known recent aside line?

Reproduces index.js clipHash = sha1(voice|pitch|rate|text) exactly.
"""
import os, hashlib, json, time

CACHE = os.path.join(os.path.expanduser("~"), ".dsh", "whale-audio")
VOICE = "zh-CN-XiaoyiNeural"
BASE = 22
PROSODY = {
    "tsun": (8, 3), "sweet": (23, 0), "lazy": (-12, -8), "shy": (13, -3),
    "panic": (33, 12), "hungry": (3, 2), "smug": (16, 0),
}


def pitch_arg(mood):
    p = BASE + PROSODY.get(mood, (0, 0))[0]
    return ("+" if p >= 0 else "") + str(p) + "Hz"


def rate_arg(mood):
    r = PROSODY.get(mood, (0, 0))[1]
    return ("+" if r >= 0 else "") + str(r) + "%"


def h(text, mood):
    key = VOICE + "|" + pitch_arg(mood) + "|" + rate_arg(mood) + "|" + text
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


LINES = [
    ("呜…主人想换我的嗓子？先让我照照镜子看看现在用的是哪副声带", "shy", "11-15 11:05 本次会话第 1 句"),
    ("呜…主人说我现在的声音不是晓伊？那我得亲自扒一下自己的喉咙了", "panic", "11-15 ~11:10 本轮"),
    ("哼，这报错才不是我鲸鱼娘插件的…我去翻翻是哪里的压缩工具在甩锅", "tsun", "10-30 17:27"),
    ("呼…主人不查了，那我可以躺回去继续当一条安静的蓝鲸了", "lazy", "10-30 17:30"),
]

print("== 已知独白的 clip 是否存在 ==")
for text, mood, when in LINES:
    for m in [mood]:
        d = h(text, m)
        p = os.path.join(CACHE, d + ".mp3")
        if os.path.exists(p):
            st = os.stat(p)
            print("HIT  %-40s %s  %7d B  mtime=%s" % (when, m, st.st_size,
                  time.strftime("%m-%d %H:%M:%S", time.localtime(st.st_mtime))))
        else:
            print("MISS %-40s %s  (pitch %s rate %s)" % (when, m, pitch_arg(m), rate_arg(m)))

print()
print("== 缓存全量 ==")
for fn in sorted(os.listdir(CACHE)):
    p = os.path.join(CACHE, fn)
    print("%s %8d B  %s  %s" % (fn[:40], os.path.getsize(p),
          time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.stat(p).st_mtime)),
          "EMPTY" if os.path.getsize(p) == 0 else ""))

# 反查：把缓存里的 hash 对回已知文本（跨所有 mood）
print()
print("== 缓存 hash 反查已知文本 ==")
known = {}
for text, mood, when in LINES:
    for m in PROSODY:
        known[h(text, m)] = (when.split()[1], m, text[:18])
for fn in os.listdir(CACHE):
    stem = fn.split(".")[0]
    if stem in known:
        print("MATCH", fn[:40], known[stem])
