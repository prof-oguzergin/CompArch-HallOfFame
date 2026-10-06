# -*- coding: utf-8 -*-
"""Top Picks from the 2025 conferences, provisional (6 Oct 2026).

The selection was announced in April 2026 (129 submissions, 12 Top Picks, 11 Honorable Mentions); the
IEEE Micro issue (vol. 46 no. 5, Sep/Oct 2026) has not appeared yet. Eleven of the twelve papers are in
IEEE Xplore early access; they are added here under their conference titles, venues and author lists
from dblp (dblp_sparql/tp2025_records.json), with Semantic Scholar citation counts of the conference
versions. The twelfth paper and the Honorable Mentions come with the issue's Guest Editors' Introduction.
Journal title -> conference paper: "Bringing Distributed Ordering to Heterogeneous Memory Consistency"
-> CORD (ISCA 2025); "Accounting for Workload Churn in Design Space Exploration" -> Neoscope (ISCA 2025);
"Fast and Accurate CPU Performance Modeling ..." -> Concorde (ISCA 2025).
Author names: the Hall of Fame spelling when the dblp PID belongs to someone on the site, else the
spelling already used in the Top Picks list, else dblp's name without the homonym number."""
import json, re, subprocess, unicodedata
R = json.load(open("dblp_sparql/tp2025_records.json", encoding="utf-8"))
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
FIX = {"Ismail Emir Yuksel": "İsmail Emir Yüksel", "Ismail Emir Yüksel": "İsmail Emir Yüksel"}
def site_name(dblp_name, pid):
    base = re.sub(r"\s+\d{4}$", "", dblp_name)
    if base in FIX: return FIX[base]
    cands = [n for n in hof_by_pid.get(pid, []) if n in listed or n in D["crossvenue"]]
    if cands:
        in_tp = [n for n in cands if n in tp_names.values()]
        return (in_tp or sorted(cands, key=lambda n: (n not in D["affiliations"], -len(n))))[0]
    return tp_names.get(fold(base), base)
CONF = {"MICRO": "MICRO 2025", "ASPLOS (1)": "ASPLOS 2025", "ASPLOS (2)": "ASPLOS 2025", "ISCA": "ISCA 2025", "HPCA": "HPCA 2025"}
ORDER = ["conf/micro/YukselOBLYM25", "conf/asplos/DineshZF25", "conf/micro/KalyanapuDAGCAA25", "conf/asplos/ApostolakisKLR25",
         "conf/asplos/AydogmusGZGTOT25", "conf/isca/YuOK25", "conf/micro/XuW0CLZW25", "conf/isca/RogersESJ25",
         "conf/isca/0001M25", "conf/hpca/TschandRIGH0ABC25", "conf/isca/Nasr-EsfahanyAL25"]
entries = []
for k in ORDER:
    r = R[k]
    title = r["title"].rstrip(".")
    authors = [site_name(n, pid) for n, pid in r["authors"]]
    entries.append((CONF[r["venue"]], title, authors, r["cites"]))
    print(f"{CONF[r['venue']]:11} {title[:70]}\n    {', '.join(authors)} | cites {r['cites']}")
def js(s): return s.replace("\\", "\\\\").replace('"', '\\"')
lines = "".join('  {year:2025,type:"TP",conf:"%s",title:"%s",authors:[%s],cites:%s},\n'
                % (c, js(t), ",".join('"' + js(a) + '"' for a in au), "null" if ci is None else ci) for c, t, au, ci in entries)
P = "data.js"
d = open(P, encoding="utf-8").read()
anchor = "\ntoppicks_papers: [\n"
assert d.count(anchor) == 1 and "year:2025,type:\"TP\"" not in d
d = d.replace(anchor, anchor + lines, 1)
open(P, "w", encoding="utf-8", newline="").write(d)
print("inserted", len(entries))
