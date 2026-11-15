import re, io, sys

P = r"C:\Users\Administrator\.dsh\profiles\desktop\node_modules\billion-context\dist\index.js"
s = io.open(P, encoding="utf-8", errors="replace").read()
pats = [
    "is entirely within the protected zone",
    "rejected before folding",
    "Compression FAILED",
    "Adjust startId/endId to older messages",
    "request only refs inside this span",
]
for pat in pats:
    hits = list(re.finditer(re.escape(pat), s))
    print("### pattern:", pat, "hits:", len(hits))
    for m in hits[:4]:
        a = max(0, m.start() - 1200)
        b = min(len(s), m.end() + 700)
        print("=" * 30, "offset", m.start())
        print(s[a:b])
        print()
