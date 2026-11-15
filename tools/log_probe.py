import os, re, io, sys

roots = [
    r"C:\Users\Administrator\.dsh",
    r"D:\code\DSH_PlainRiceWhale",
]
pat = re.compile(r"acp-proxy: compress (FAILED|REFUSED)")
hits = []
for root in roots:
    for dirpath, dirnames, filenames in os.walk(root):
        # skip node_modules except billion-context dist (too big otherwise)
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "assets")]
        for fn in filenames:
            if not fn.lower().endswith((".log", ".jsonl", ".txt", ".ndjson")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > 60 * 1024 * 1024:
                    continue
                with io.open(p, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if pat.search(line):
                            hits.append((p, i, line.strip()[:400]))
            except Exception as e:
                pass
print("hits:", len(hits))
for p, i, l in hits[-12:]:
    print("-" * 10, p, "line", i)
    print(l)
