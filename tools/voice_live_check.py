"""Live check against the running Host (no restart needed)."""
import json, time, urllib.request, sys

PORT = "50418"
BASE = "http://127.0.0.1:%s/whale-aside/voice" % PORT


def post(body):
    req = urllib.request.Request(BASE, data=json.dumps(body).encode("utf-8"),
                                 headers={"content-type": "application/json"}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8")), time.time() - t0
    except Exception as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8")), time.time() - t0
        except Exception:
            return "ERR", str(e), time.time() - t0


CASES = [
    ("害羞（负 rate 的老 bug）", {"text": "现场自检：害羞的小鲸鱼", "mood": "shy"}),
    ("慵懒（另一个负 rate）", {"text": "现场自检：好懒啊", "mood": "lazy"}),
    ("请求级换音色（云夏）", {"text": "现场自检：换个嗓子听听", "mood": "tsun", "voice": "zh-CN-YunxiaNeural", "basePitchHz": 30}),
    ("无语 meh", {"text": "现场自检：死鱼眼", "mood": "meh"}),
]

for label, body in CASES:
    status, payload, dt = post(body)
    ok = isinstance(payload, dict) and payload.get("ok") is True
    print("%s %-22s %5.2fs %s" % ("OK " if ok else "BAD", label, dt, json.dumps(payload, ensure_ascii=False)[:260]))
    if ok:
        url = "http://127.0.0.1:%s%s" % (PORT, payload["url"])
        with urllib.request.urlopen(url, timeout=30) as r:
            n = len(r.read())
            print("      clip %s %d B  content-type=%s" % (r.status, n, r.headers.get("content-type")))
    time.sleep(0.5)
