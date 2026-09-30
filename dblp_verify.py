# -*- coding: utf-8 -*-
"""Classify dblp records (dblp_sparql/<v>.json) and compare HoF counts per PID.
MAIN = full paper in the main track. Everything else is listed with a reason and not counted.
Rules (project CLAUDE.md): no editorship, keynote/invited talk, panel, tutorial, retrospective,
workshop paper, corrigendum. Short papers before 2000 are real papers and are kept."""
import json, re, unicodedata, sys
from collections import defaultdict

MAIN_VENUES = {
    "asplos": {"ASPLOS", "ASPLOS (1)", "ASPLOS (2)", "ASPLOS (3)", "ASPLOS (4)"},
    "isca": {"ISCA"},
    "micro": {"MICRO", "MICRO (1)", "MICRO (2)", "MICRO Supplement"},  # 1974 supplement = real papers
    "hpca": {"HPCA"},
}
NONPAPER_TITLE = re.compile(
    r"\b(keynote|panel|panelists?|invited talk|debate|corrigendum|erratum|errata|retraction|"
    r"wild and crazy|waci|synopsis|message from|foreword|welcome|tutorial|in memoriam|tribute|"
    r"birds of a feather|program committee|steering committee|session (chair|summary)|"
    r"award (talk|lecture)|acceptance speech|opening remarks|closing remarks)\b", re.I)

WORKSHOP_SUMMARY = re.compile(r"(workshop|symposium) on|^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth) workshop", re.I)

def pages(pg):
    m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", pg or "")
    if not m:
        m1 = re.match(r"^\s*(\d+)\s*$", pg or "")
        return 1 if m1 else None
    a, b = int(m.group(1)), int(m.group(2))
    return b - a + 1 if b >= a else None

# real main-track papers that the rules below would drop (checked by hand, 30 Sep 2026):
# HPCA 2011 papers whose dblp page ranges are wrong (2 pages instead of 12)
FORCE_MAIN = {"conf/hpca/LeeSNY11", "conf/hpca/HowerDHW11", "conf/hpca/BhattacharjeeLM11"}

def classify(v, r):
    if r["type"] == "E":
        return "EDITOR"
    if r["publ"].split("/rec/")[-1] in FORCE_MAIN:
        return "MAIN"
    if r["venue"] not in MAIN_VENUES[v]:
        return "RETRO" if "Retrospectives" in r["venue"] else "WORKSHOP"
    p = pages(r["pages"])
    # title words only mark short items: "debate"/"errata" also occur in full-paper titles
    if NONPAPER_TITLE.search(r["title"]) and (p is None or p <= 4):
        return "NONPAPER_TITLE"
    if WORKSHOP_SUMMARY.search(r["title"]):
        return "WORKSHOP_SUMMARY"      # one-page summaries of co-located workshops, any year
    if p == 1:
        return "ONE_PAGE"              # abstracts/summaries, any year
    if p is not None and r["year"] >= 2000 and p <= 4:
        return "SHORT_MODERN"          # keynote/panel abstracts in the modern era; reviewed by hand
    return "MAIN"

def sa(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
def norm(s):
    s = s.lower().replace("ı", "i")
    s = sa(s); s = re.sub(r"\b\d{4}\b", "", s)       # dblp homonym suffix "0001"
    s = re.sub(r"[.\-]", " ", s); return re.sub(r"\s+", " ", s).strip()

hof = json.load(open("dblp_sparql/hof_snapshot.json", encoding="utf-8"))
aff = {norm(k): v.get("pid") for k, v in hof["affiliations"].items()}

report = {}
for v in ["asplos", "isca", "micro", "hpca"]:
    R = json.load(open(f"dblp_sparql/{v}.json", encoding="utf-8"))
    by_pid = defaultdict(lambda: {"main": defaultdict(int), "excluded": [], "name": None})
    name_to_pids = defaultdict(set)
    for r in R:
        c = classify(v, r)
        for pe in r["persons"]:
            d = by_pid[pe["pid"]]; d["name"] = pe["name"]
            name_to_pids[norm(pe["name"])].add(pe["pid"])
            if c == "MAIN":
                d["main"][r["year"]] += 1
            else:
                d["excluded"].append({"cls": c, "year": r["year"], "pages": r["pages"],
                                      "venue": r["venue"], "title": r["title"]})
    rows = []
    for e in hof[v]:
        k = norm(e["name"]); pid = aff.get(k)
        how = "aff"
        if not pid or pid not in by_pid:
            cands = name_to_pids.get(k, set())
            if len(cands) == 1:
                pid, how = next(iter(cands)), "name"
            elif not pid:
                pid, how = None, f"UNRESOLVED({len(cands)})"
            else:
                how = "aff-pid-has-no-records"
        d = by_pid.get(pid) if pid else None
        main_y = dict(sorted(d["main"].items())) if d else {}
        dt = sum(main_y.values())
        hy = {int(y): c for y, c in e["y"].items()}
        rows.append({"name": e["name"], "pid": pid, "how": how, "hof_total": e["total"],
                     "dblp_main": dt, "diff": e["total"] - dt, "hof_y": hy, "dblp_y": main_y,
                     "excluded": d["excluded"] if d else []})
    # dblp people with 8+ main papers who are NOT in the HoF list
    hof_pids = {r["pid"] for r in rows if r["pid"]}
    missing = []
    for pid, d in by_pid.items():
        t = sum(d["main"].values())
        if t >= 8 and pid not in hof_pids:
            missing.append({"pid": pid, "name": d["name"], "dblp_main": t,
                            "first": min(d["main"]), "last": max(d["main"])})
    report[v] = {"rows": rows, "missing": sorted(missing, key=lambda x: -x["dblp_main"])}
    same = sum(1 for r in rows if r["diff"] == 0)
    print(f"{v}: HoF {len(rows)} | same {same} | HoF higher {sum(1 for r in rows if r['diff']>0)} "
          f"| HoF lower {sum(1 for r in rows if r['diff']<0)} | unresolved {sum(1 for r in rows if not r['pid'] or r['how'].startswith(('UNRES','aff-pid')))} "
          f"| dblp 8+ not in HoF {len(missing)}")
json.dump(report, open("dblp_sparql/compare.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
