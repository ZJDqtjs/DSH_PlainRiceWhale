"""Decisive test: drive the plugin's own voice route the way the Client half does."""
import json, time, urllib.request, sys, os, hashlib

PORT = sys.argv[1] if len(sys.argv) > 1 else "50418"
BASE = "http://127.0.0.1:%s/whale-aside/voice" % PORT
CACHE = os.path.join(os.path.expanduser("~"), ".dsh", "whale-audio")

LINES = [
    ("呜…主人想换我的嗓子？先让我照照镜子看看现在用的是哪副声带", "shy"),
    ("测试线路一：鲸鱼娘的喉咙检查", "tsun"),
    ("测试线路二：鲸鱼娘的喉咙检查", "panic"),
    ("测试线路三：鲸鱼娘的喉咙检查", "sweet"),
]


def post(text, mood):
    body = json.dumps({"text": text, "mood": mood}).encode("utf-8")
    req = urllib.request.Request(BASE, data=body, headers={"content-type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            dt = time.time() - t0
            return resp.status, payload, dt
    except Exception as error:
        dt = time.time() - t0
        try:
            detail = error.read().decode("utf-8", "replace")
        except Exception:
            detail = ""
        return getattr(error, "code", "ERR"), detail or str(error), dt


for text, mood in LINES:
    status, payload, dt = post(text, mood)
    tag = "OK " if status == 200 and isinstance(payload, dict) and payload.get("ok") else "BAD"
    print("%s %s %-6s %5.2fs  %s" % (tag, mood, status, dt, json.dumps(payload, ensure_ascii=False)[:300]))
    time.sleep(0.8)

print()
print("GET 健康检查:", end=" ")
with urllib.request.urlopen(BASE, timeout=20) as r:
    print(r.status, r.read().decode("utf-8"))
