# -*- coding: utf-8 -*-
"""Google Scholar citation counts for the 12 papers added from IEEE Micro 46(5) (9 Nov 2026).
Reads the Scholar profiles already stored in data.js gs, newest papers first, one request per profile, at most 3 profiles
per paper (last author first), 15-25 s apart. HTTP 429 or a captcha page stops the run at once; it never tries to get
around a block. A paper no profile lists keeps its current count. Progress: dblp_sparql/tp2025_issue_gs.json.
Run with --apply to write the counts found into data.js; without it, fetches and prints."""
import json, os, random, re, subprocess, sys, time, html as ihtml, urllib.error, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
OUT = "dblp_sparql/tp2025_issue_gs.json"
APPLY = "--apply" in sys.argv
R = json.load(open("dblp_sparql/tp2025_issue_records.json", encoding="utf-8"))
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D))']).decode("utf-8"))
def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())
papers = []
for r in R:
    keys = {norm(r["title"])[:24], norm(r["want_title"])[:24]}
    e = [p for p in D["toppicks_papers"] if p["year"] == 2025 and p["type"] == r["type"] and norm(p["title"])[:24] in keys]
    assert len(e) == 1, r["title"]
    papers.append((e[0], keys))
res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
class Blocked(Exception): pass
def profile(gid):
    url = f"https://scholar.google.com/citations?user={gid}&hl=en&sortby=pubdate&pagesize=100"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}), timeout=40) as r:
            h = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404: return []
        raise Blocked(f"HTTP {e.code}")
    if re.search(r"unusual traffic|gs_captcha|not a robot|recaptcha", h, re.I): raise Blocked("captcha page")
    rows = []
    for tr in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', h, re.S):
        t = re.search(r'class="gsc_a_at"[^>]*>([^<]+)<', tr)
        c = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d*)</a>', tr)
        if t: rows.append((ihtml.unescape(t.group(1)), int(c.group(1)) if c and c.group(1) else 0))
    return rows
# authors not in data.js gs, profiles found by search (the paper's title must be on the profile to count)
EXTRA = {"Gururaj Saileshwar": "0RnpQFcAAAAJ", "Dimitrios Skarlatos": "T_ZmDEAAAAAJ", "Hung-Wei Tseng": "j-Lk39cAAAAJ", "Emre Ozer": "gj6YLR0AAAAJ", "Amar Phanishayee": "HqGW4HIAAAAJ"}
cache = {}
try:
    for p, keys in papers:
        if p["title"] in res or APPLY: continue
        ids = [(a, EXTRA.get(a) or D["gs"][a]["gs"]) for a in reversed(p["authors"]) if a in EXTRA or (a in D["gs"] and D["gs"][a].get("gs"))][:3]
        print(f"{p['type']} {p['title'][:60]} | profiles: {[a for a, _ in ids]}", flush=True)
        for a, gid in ids:
            if gid not in cache:
                time.sleep(random.uniform(15, 25)); cache[gid] = profile(gid)
            hit = [c for t, c in cache[gid] if norm(t)[:24] in keys]
            if hit:
                res[p["title"]] = {"gs": max(hit), "via": a}; print(f"    Scholar {max(hit)} via {a}, was {p['cites']}", flush=True); break
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
except Blocked as e:
    print("STOPPED:", e, flush=True)
print("found", len(res), "of", len(papers), flush=True)
if APPLY:
    d = open("data.js", encoding="utf-8", newline="").read()
    for p, _ in papers:
        if p["title"] not in res: continue
        pat = re.compile(r'(\{year:2025,type:"%s",conf:"[^"]*",title:"%s",authors:\[[^\]]*\],cites:)(?:null|\d+)' % (p["type"], re.escape(p["title"].replace('"', '\\"'))))
        d, k = pat.subn(lambda m: m.group(1) + str(res[p["title"]]["gs"]), d)
        assert k == 1, p["title"]
    open("data.js", "w", encoding="utf-8", newline="").write(d)
    print("data.js written")
