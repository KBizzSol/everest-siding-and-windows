"""Download files listed in tools/missing.txt from the live site into mirror/,
then recursively fetch anything those CSS files reference."""
import os, re, urllib.request, urllib.parse
DOM = "everestsidingandwindows.com"
BASE = f"https://{DOM}/"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "mirror")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130"}
src = os.path.join(HERE, "missing.txt")
todo = [l.strip() for l in open(src) if l.strip()] if os.path.exists(src) else []
seen, ok, bad = set(), 0, []
while todo:
    p = todo.pop(0)
    if p in seen: continue
    seen.add(p)
    dest = os.path.join(ROOT, p, "index.html") if (p.endswith("/") or p == "") else os.path.join(ROOT, p)
    if os.path.exists(dest): continue
    try:
        data = urllib.request.urlopen(urllib.request.Request(BASE + urllib.parse.quote(p), headers=UA), timeout=60).read()
    except Exception as e:
        bad.append(f"{p} {e}"); continue
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(data); ok += 1
    if p.endswith(".css"):
        for u in re.findall(r'url\(["\']?([^"\')]+)["\']?\)', data.decode("utf-8", "ignore")):
            if u.startswith(("data:", "#")): continue
            if u.startswith("http"):
                if DOM not in u: continue
                q = urllib.parse.urlparse(u).path.lstrip("/")
            elif u.startswith("/"): q = u.lstrip("/")
            else: q = os.path.normpath(os.path.join(os.path.dirname(p), u))
            q = urllib.parse.unquote(q.split("?")[0].split("#")[0])
            if not q.startswith(".."): todo.append(q)
print("downloaded", ok, "failed", len(bad))
for b in bad[:80]: print("FAIL", b)
