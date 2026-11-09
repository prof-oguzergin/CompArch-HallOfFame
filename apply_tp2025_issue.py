# -*- coding: utf-8 -*-
"""Top Picks from the 2025 conferences, complete (9 Nov 2026), from the issue itself: IEEE Micro 46(5), Sep/Oct 2026,
Guest Editors' Introduction (Nam Sung Kim, Yingyan Lin; 10.1109/MM.2026.3730780): 12 Top Picks, 11 Honorable Mentions.

Adds what the provisional list (apply_tp2025_provisional.py) could not have: the twelfth Top Pick and the 11 Honorable
Mentions. Records: dblp_sparql/tp2025_issue_records.json (tp2025_issue_fetch.py).
- The Top Pick is listed under its conference title, venue and authors, like the other eleven. Journal title
  "NeuSight: Predicting the Performance of Future AI on Emerging GPUs" -> "Forecasting GPU Performance for Deep Learning
  Training and Inference" (ASPLOS 2025).
- Honorable Mentions use the titles and venues of the issue's Table 1, with the conference paper's authors from dblp.
Author names: the same rule as the provisional list (Hall of Fame spelling for a PID on the site, else the spelling
already in the Top Picks list, else dblp's name without the homonym number).
Run with --apply to write; otherwise prints the entries."""
import json, re, subprocess, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8")
APPLY = "--apply" in sys.argv
R = json.load(open("dblp_sparql/tp2025_issue_records.json", encoding="utf-8"))
assert len(R) == 12 and not any("missing" in r for r in R), "records incomplete"
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D))']).decode("utf-8"))
src = open("apply_dblp_verified.py", encoding="utf-8").read(); g = {}
exec("PID = " + src.split("PID = ")[1].split("\nEXTRA_PUBL")[0], {}, g); PIDMAP = g["PID"]
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s.lower().replace("ı", "i")) if unicodedata.category(c) != "Mn").replace(".", "").strip()
tp_names = {}
for p in D["toppicks_papers"]:
    for a in p["authors"]: tp_names.setdefault(fold(a), a)
hof_by_pid = {}
for n, v in D["affiliations"].items():
    if v.get("pid"): hof_by_pid.setdefault(v["pid"], []).append(n)
for n, ps in PIDMAP.items():
    for p in ps: hof_by_pid.setdefault(p, []).append(n)
listed = {e["name"] for v in ["isca", "micro", "asplos", "hpca"] for e in D[v]}
# Fan Chung (EMT, byline on the USENIX page): dblp ties this author to the mathematician Fan Chung Graham's PID.
FIX = {"Fan Chung Graham": "Fan Chung", "Doug Carmean": "Douglas M. Carmean"}
def site_name(dblp_name, pid):
    base = re.sub(r"\s+\d{4}$", "", dblp_name)
    if base in FIX: return FIX[base]
    cands = [n for n in hof_by_pid.get(pid, []) if n in listed or n in D["crossvenue"]]
    if cands:
        in_tp = [n for n in cands if n in tp_names.values()]
        return (in_tp or sorted(cands, key=lambda n: (n not in D["affiliations"], -len(n))))[0]
    return tp_names.get(fold(base), base)
def js(s): return s.replace("\\", "\\\\").replace('"', '\\"')
def line(r):
    title = r["title"] if r["type"] == "TP" else r["want_title"]
    authors = [site_name(n, pid) for n, pid in r["authors"]]
    conf = r["want_venue"] + " 2025"
    print(f"{r['type']} {conf:21} {title[:64]} | cites {r['cites']}\n    {', '.join(authors)}")
    return '  {year:2025,type:"%s",conf:"%s",title:"%s",authors:[%s],cites:%s},\n' % (
        r["type"], conf, js(title), ",".join('"' + js(a) + '"' for a in authors), "null" if r["cites"] is None else r["cites"])
lines = "".join(line(r) for r in R if r["type"] == "TP") + "".join(line(r) for r in R if r["type"] == "HM")
P = "data.js"
d = open(P, encoding="utf-8", newline="").read()
anchor = '  {year:2024,type:"TP"'
assert 'year:2025,type:"HM"' not in d
i = d.index(anchor)
d = d[:i] + lines + d[i:]
if APPLY:
    open(P, "w", encoding="utf-8", newline="").write(d)
    print("inserted", len(R))
