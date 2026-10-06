# -*- coding: utf-8 -*-
"""Apply the DBLP PID-based verification (30 Sep 2026) to data.js.
Main-track full papers only: no editorship, keynote, panel, corrigendum, memorial, workshop,
25-Years-ISCA retrospective/reprint, one-page abstract. Decisions below are explicit and
documented; run with --apply to write data.js, otherwise dry run."""
import json, re, sys
sys.argv += [] ; APPLY = "--apply" in sys.argv
src = open("dblp_verify.py", encoding="utf-8").read(); ns = {}
exec(src.split("hof = json.load")[0], ns); classify, norm = ns["classify"], ns["norm"]
H = json.load(open("dblp_sparql/hof_snapshot.json", encoding="utf-8"))
DB = {v: json.load(open(f"dblp_sparql/{v}.json", encoding="utf-8")) for v in ["asplos","isca","micro","hpca"]}

# name -> canonical dblp pid(s); extra pids are split identities of the same person (verified by hand)
PID = {
 "Jim Smith": ["17/1987-1", "17/1987"], "James E. Smith": ["17/1987-1", "17/1987"],
 "Scott Mahlke": ["m/SAMahlke"], "Scott A. Mahlke": ["m/SAMahlke"],
 "Mahmut Kandemir": ["k/MahmutTKandemir"], "Mahmut T. Kandemir": ["k/MahmutTKandemir"], "Mahmut Taylan Kandemir": ["k/MahmutTKandemir"],
 "Trevor Mudge": ["m/TrevorNMudge"], "Trevor N. Mudge": ["m/TrevorNMudge"],
 "Todd Austin": ["a/ToddMAustin"], "Todd M. Austin": ["a/ToddMAustin"],
 "Natalie Enright Jerger": ["61/5482"], "Natalie D. Enright Jerger": ["61/5482"],
 "John P. Shen": ["99/1477"], "John Paul Shen": ["99/1477"],
 "Mateo Valero Cortés": ["v/MateoValero"], "Mateo Valero": ["v/MateoValero"],
 "Christos Kozyrakis": ["k/ChristoforosEKozyrakis"], "Christoforos E. Kozyrakis": ["k/ChristoforosEKozyrakis"],
 "Rakesh Kumar": ["98/4371-2"], "John Kim": ["39/6945-1"], "Anand Sivasubramaniam": ["72/3356"],
 "Dean M. Tullsen": ["t/DeanMTullsen", "405/7873"],          # MICRO 2025 OneAdapt filed under "Dean Tullsen"
 "Guangyu Sun": ["29/6473-3"], "Hai Helen Li": ["30/5330-1"],
 "Tony Nowatzki": ["58/11098"], "Yu Feng": ["30/4550-7"],
 "Yuanyuan Zhou": ["99/2747-1", "99/2747"],                  # ASPLOS 2004 paper under undisambiguated 99/2747
}
EXTRA_PUBL = {  # single papers of the same person filed under an undisambiguated dblp id
 ("isca", "Guangyu Sun"): ["Graph.hls"],                     # ISCA 2026, PKU, program lists him
 ("isca", "Arvind"): ["A Multiprocessor Data Flow Machine that Supports Generalized Procedures"],
     # ISCA 1981 pp. 291-302 by Arvind and Vinod Kathail; dblp merged the two into one author "Arvind V. Kathail" (95/2819)
 ("asplos", "Scott A. Mahlke"): ["SNIP: An Adaptive Mixed Precision Framework"],
    # ASPLOS 2026, Michigan; dblp opened 429/0057 for it (6 Oct 2026, apply_asplos_splits.py)
 ("asplos", "Quan Chen"): ["Voyager: Input-Adaptive Algebraic Transformations"],
    # ASPLOS'25 vol.3, SJTU; dblp filed it under 40/3858-1, a remote-sensing Quan Chen (6 Oct 2026)
 # ISCA/MICRO/HPCA re-check, 6 Oct 2026 (venue_split_check.py, apply_other_venue_splits.py):
 ("micro", "Rajiv Gupta"): ["Predictability of load/store instruction latencies"],
    # MICRO 1993 with HP Labs; dblp files it under 181/2697 (a radiologist), the ACM DL author profile is
    # UC Riverside's Rajiv Gupta; the 30 Sep run had dropped it (15 -> 14), restored
 ("isca", "Michael C. Huang"): ["DS-TPU: Dynamical System for on-Device Lifelong Graph Learning"],
    # ISCA 2025; dblp 87/6759; program: Michael Huang (Rochester), five co-authors shared with him
 ("hpca", "Guangyu Sun"): ["Towards Compute-Aware In-Switch Computing"],
    # HPCA 2026; under undisambiguated 29/6473 in the 30 Sep pull, moved to his PID by dblp since; program: PKU
 ("hpca", "Jie Zhang"): ["TENET-v2"],
    # HPCA 2026; dblp 84/6889-177; researchr links it to the same profile (CHASE Lab, PKU) as his AutoGNN
 # crossvenue (recompute_crossvenue.py reads these too):
 ("hpca", "Ang Li"): ["Fully Parallelized BP Decoding for Quantum LDPC Codes"],
    # HPCA 2026; dblp 33/2805; program: Ang Li (Pacific Northwest National Laboratory)
 ("isca", "Xinyu Chen"): ["UniCore: A Bit-Width Scalable GEMM Unit"],          # ISCA 2026 under 96/3374
 ("micro", "Xinyu Chen"): ["AxCore: A Quantization-Aware Approximate GEMM Unit"], # MICRO 2025 under 96/3374
}
# keep the official count as is (reason): old-year dblp gaps, author-confirmed splits, year labels only
KEEP = {
 ("micro","Yale N. Patt"): "MICRO 1983 absent from dblp (0 records); official SIGMICRO count kept",
 ("micro","Robert A. Mueller"): "MICRO 1983 absent from dblp; official count kept",
 ("micro","John P. Shen"): "dblp +1 is a 3-page 1988 item; official count kept",
 ("hpca","Yuan Xie"): "2 HPCA papers under undisambiguated 157/8128, author-confirmed 20 May 2026",
 ("isca","G. Jack Lipovski"): "same total, dblp labels 1974 papers as 1975",
 ("asplos","Xuehai Qian"): "same total, ASPLOS'23 volume-year label only",
 ("asplos","Christina Delimitrou"): "same total, volume-year label only",
 ("asplos","Rajiv Gupta"): "same total, volume-year label only",
 ("hpca","Rakesh Kumar"): "same total, one paper labelled 2025 vs 2026 only",
}
ADD = {"isca": ["Tony Nowatzki", "Hai Helen Li", "Yu Feng"]}

def aff_pid(name):
    for k, v in H["affiliations"].items():
        if norm(k) == norm(name): return v.get("pid")
CMP = json.load(open("dblp_sparql/compare.json", encoding="utf-8"))
RESOLVED = {(v, r["name"]): r["pid"] for v in CMP for r in CMP[v]["rows"]
            if r["pid"] and not r["how"].startswith(("UNRES", "aff-pid"))}
def pids_for(name, v=None):
    if name in PID: return PID[name]
    if v and (v, name) in RESOLVED: return [RESOLVED[(v, name)]]
    return [aff_pid(name)] if aff_pid(name) else []
def conf_year(v, r):
    if v == "asplos" and r["venue"] == "ASPLOS (1)" and r["year"] == 2022: return 2023   # ASPLOS'23 vol.1 printed Dec 2022
    return r["year"]
def main_years(v, name):
    ps = set(pids_for(name, v)); ys = {}; seen = set()
    extra = EXTRA_PUBL.get((v, name), [])
    for r in DB[v]:
        mine = any(p["pid"] in ps for p in r["persons"]) or any(t in r["title"] for t in extra)
        if mine and r["publ"] not in seen and classify(v, r) == "MAIN":
            seen.add(r["publ"]); y = conf_year(v, r); ys[y] = ys.get(y, 0) + 1
    return dict(sorted(ys.items()))

changes = []   # (venue, name, old_total, new_total, new_y or None=remove, note)
for v in ["hpca","micro","isca","asplos"]:
    for e in H[v]:
        old = {int(k): c for k, c in e["y"].items()}
        if (v, e["name"]) in KEEP: continue
        new = main_years(v, e["name"])
        if not new:
            changes.append((v, e["name"], e["total"], None, None, "NO DBLP RECORDS - check PID")); continue
        nt = sum(new.values())
        if new != old:
            changes.append((v, e["name"], e["total"], nt, new if nt >= 8 else None, "below 8: remove" if nt < 8 else ""))
    for name in ADD.get(v, []):
        new = main_years(v, name); changes.append((v, name, 0, sum(new.values()), new, "NEW"))

for c in changes:
    v, n, ot, nt, ny, note = c
    print(f"{v:6s} {n:28s} {ot:>3} -> {str(nt):>4}  {note}")
json.dump([list(c) for c in changes], open("dblp_sparql/changes.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"\n{len(changes)} changes; removals: {sum(1 for c in changes if c[4] is None)}")

if APPLY:
    data = open("data.js", encoding="utf-8").read()
    lines = data.split("\n")
    def block(v):
        a = next(i for i, l in enumerate(lines) if l.startswith(v + ": ["))
        b = next(i for i in range(a + 1, len(lines)) if lines[i].startswith("]"))
        return a, b
    def fmt(name, y):
        yy = ",".join(f"{k}:{c}" for k, c in sorted((int(k), c) for k, c in y.items()))
        return f'  {{name:"{name}",total:{sum(y.values())},y:{{{yy}}}}},'
    cv_add = {}                                   # name -> {venue: count}
    cv_del = []                                   # (name, venue)
    for v, name, ot, nt, ny, note in changes:
        a, b = block(v)
        idx = next((i for i in range(a, b) if f'{{name:"{name}",' in lines[i]), None)
        if note == "NEW":
            last = b - 1
            lines[last] = lines[last].rstrip(",") + ","
            lines.insert(b, fmt(name, ny).rstrip(","))
            cv_del.append((name, v))
        elif ny is None:
            assert idx is not None, (v, name); del lines[idx]
            cv_add.setdefault(name, {})[v] = nt
        else:
            assert idx is not None, (v, name)
            end = "," if lines[idx].rstrip().endswith(",") else ""
            lines[idx] = fmt(name, ny).rstrip(",") + end
    # a venue block must not end with a trailing comma before "]" (keep file style valid either way)
    data = "\n".join(lines)
    # crossvenue edits, strictly inside the crossvenue block (names also occur in affiliations/gs)
    import re as _re
    cs = data.index("\ncrossvenue: {"); ce = data.index("\n},", cs) + 1
    cv = data[cs:ce]
    def cv_get(name):
        return _re.search(r'\n  "' + _re.escape(name) + r'":\s*\{([^}]*)\},', cv)
    for name, add in cv_add.items():
        m = cv_get(name)
        if m:
            cur = dict(kv.split(":") for kv in m.group(1).split(",") if kv)
            cur.update({k: str(v) for k, v in add.items()})
            cv = cv[:m.start()] + '\n  "' + name + '": {' + ",".join(f"{k}:{v}" for k, v in cur.items()) + "}," + cv[m.end():]
        else:
            i = cv.index("crossvenue: {") + len("crossvenue: {")
            cv = cv[:i] + '\n  "' + name + '": {' + ",".join(f"{k}:{v}" for k, v in add.items()) + "}," + cv[i:]
    for name, v in cv_del:
        m = cv_get(name)
        if m:
            cur = [kv for kv in m.group(1).split(",") if kv and not kv.startswith(v + ":")]
            cv = cv[:m.start()] + '\n  "' + name + '": {' + ",".join(cur) + "}," + cv[m.end():]
    data = data[:cs] + cv + data[ce:]
    open("data.js", "w", encoding="utf-8", newline="").write(data)
    print("data.js written:", len(cv_add), "crossvenue additions,", len(cv_del), "crossvenue removals")
