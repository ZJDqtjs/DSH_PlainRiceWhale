import io, os, json

P = r"C:\Users\Administrator\.dsh\profiles\desktop\node_modules\billion-context\dist\index.js"
s = io.open(P, encoding="utf-8", errors="replace").read()
lines = s.split("\n")
cum = []
n = 0
for i, ln in enumerate(lines, 1):
    cum.append(n)
    n += len(ln) + 1

def lineno(off):
    lo, hi = 0, len(cum) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if cum[mid] <= off:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1

for label, off in [
    ("zone fatal (Range is entirely within the protected zone)", 1492636),
    ("batch reject (failed during application)", 1525642),
    ("batch reject (summary-length validation)", 1523205),
    ("currentRefsSnapshot hint", 3485862),
]:
    print(label, "-> dist/index.js line", lineno(off))
print("total lines in bundle:", len(lines))

W = r"D:\code\DSH_PlainRiceWhale\whale-aside"
for root, dirs, files in os.walk(W):
    dirs[:] = [d for d in dirs if d not in ("node_modules",)]
    for f in files:
        p = os.path.join(root, f)
        try:
            st = os.stat(p)
        except Exception:
            continue
        if os.path.basename(p) == ".DS_Store":
            continue
        rel = os.path.relpath(p, W)
        extra = ""
        if f.endswith((".js", ".json", ".md", ".yml")):
            extra = " lines=%d" % io.open(p, encoding="utf-8", errors="replace").read().count("\n")
        print("%-46s %9d B%s %s" % (rel, st.st_size, extra, json.__class__ and ""))
