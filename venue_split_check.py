# -*- coding: utf-8 -*-
"""Split-identity check for any of the four venues on fresh dblp pulls (generalises asplos_split_check.py).
Usage: python venue_split_check.py isca [date]     (date of the dblp_sparql/<venue>_<date>.json pulls, default 20261006)

0. site vs dblp per researcher, aliases grouped by canonical PID (apply_dblp_verified.py PID map,
   EXTRA_PUBL titles and KEEP notes honoured; MICRO 2026 is provisional from the program and left out)
A. papers of the venue under another, loosely same-named PID, scored by co-authors shared with the
   researcher anywhere in the four venues
B. 2024-2026 papers on a researcher's own PID that share no co-author with anything else of theirs
C. people not on the site whose loosely same-named PIDs reach 8 together
Prints candidates for a manual decision; writes nothing."""
import json, re, sys, subprocess
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
V = sys.argv[1]; DATE = sys.argv[2] if len(sys.argv) > 2 else "20261006"
src = open("apply_dblp_verified.py", encoding="utf-8").read(); ns = {}
exec(src.split("changes = []")[0], ns)
classify, norm, PIDMAP, EXTRA, KEEP = ns["classify"], ns["norm"], ns["PID"], ns["EXTRA_PUBL"], ns["KEEP"]
DB = {v: json.load(open(f"dblp_sparql/{v}_{DATE}.json", encoding="utf-8")) for v in ["isca", "micro", "hpca", "asplos"]}
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D))']).decode("utf-8"))
SKIP_YEARS = {2026} if V == "micro" else set()        # MICRO 2026 not in dblp yet; site has it from the program

NICK = {"bill": "william", "will": "william", "bob": "robert", "rob": "robert", "rick": "richard", "rich": "richard",
        "ted": "edward", "ed": "edward", "jim": "james", "tom": "thomas", "mike": "michael", "dave": "david",
        "steve": "steven", "stephen": "steven", "andy": "andrew", "chris": "christopher", "christos": "christoforos",
        "dan": "daniel", "ron": "ronald", "tim": "timothy", "nick": "nicholas", "alex": "alexander", "ben": "benjamin",
        "sam": "samuel", "matt": "matthew", "greg": "gregory", "joe": "joseph", "jon": "jonathan", "tony": "anthony",
        "ken": "kenneth", "larry": "lawrence", "phil": "philip", "hank": "henry", "fred": "frederic", "frederick": "frederic",
        "ram": "ramachandran", "josh": "joshua", "pat": "patrick"}
def loose(name):
    t = [w for w in norm(name).split() if len(w) > 1]
    if not t: return None
    return (NICK.get(t[0], t[0]), t[-1]) if len(t) > 1 else (t[0], t[0])
def conf_year(r):
    return 2023 if (V == "asplos" and r["venue"] == "ASPLOS (1)" and r["year"] == 2022) else r["year"]

main = [r for r in DB[V] if classify(V, r) == "MAIN"]
recs = defaultdict(list); pname = {}
for r in main:
    for p in r["persons"]: recs[p["pid"]].append(r); pname[p["pid"]] = p["name"]
coauth = defaultdict(set)
for v, rs in DB.items():
    for r in rs:
        ps = [p["pid"] for p in r["persons"]]
        for p in r["persons"]:
            pname.setdefault(p["pid"], p["name"])
            coauth[p["pid"]].update(q for q in ps if q != p["pid"])
by_loose = defaultdict(set)
for pid, n in pname.items():
    k = loose(n)
    if k: by_loose[k].add(pid); by_loose[(k[1], k[0])].add(pid)

names = sorted({e["name"] for v in ["isca", "micro", "asplos", "hpca"] for e in D[v]})
def canon(name):
    if name in PIDMAP: return set(PIDMAP[name])
    p = D["affiliations"].get(name, {}).get("pid")
    if p: return {p}
    for k, v in D["affiliations"].items():
        if norm(k) == norm(name) and v.get("pid"): return {v["pid"]}
    c = {q for q in by_loose.get(loose(name), set()) if norm(pname[q]) == norm(name)}
    return c if len(c) == 1 else set()
person = {}
for n in names:
    ps = canon(n)
    if ps: person.setdefault(frozenset(ps), []).append(n)
unres = [n for n in names if not canon(n)]
members = {e["name"]: e for e in D[V]}

def dblp_years(ps, ns_):
    extra = [t for n in ns_ for t in EXTRA.get((V, n), [])]
    out = defaultdict(int); seen = set()
    for r in main:
        if r["publ"] in seen: continue
        if any(p["pid"] in ps for p in r["persons"]) or any(t in r["title"] for t in extra):
            seen.add(r["publ"]); out[conf_year(r)] += 1
    return {y: c for y, c in sorted(out.items()) if y not in SKIP_YEARS}

print(f"{V}: site researchers {len(names)}, persons {len(person)}, unresolved {unres}")
print(f"\n0. site vs dblp ({'2026 left out' if SKIP_YEARS else 'all years'})")
nd = 0
for ps, ns_ in sorted(person.items(), key=lambda kv: kv[1][0]):
    d = dblp_years(ps, ns_)
    m = [members[n] for n in ns_ if n in members]
    if m:
        hy = {int(k): c for k, c in m[0]["y"].items() if int(k) not in SKIP_YEARS}
        if hy != d:
            nd += 1
            note = next((KEEP[(V, n)] for n in ns_ if (V, n) in KEEP), "")
            dif = {y: (hy.get(y, 0), d.get(y, 0)) for y in sorted(set(hy) | set(d)) if hy.get(y, 0) != d.get(y, 0)}
            print(f"   MEMBER {' / '.join(ns_)}: site {sum(hy.values())} dblp {sum(d.values())} | year (site, dblp) {dif}" + (f" | KEEP: {note}" if note else ""))
    else:
        s = max(D["crossvenue"].get(n, {}).get(V, 0) for n in ns_)
        if s != sum(d.values()):
            nd += 1; print(f"   CV {' / '.join(ns_)}: site {s} dblp {sum(d.values())} {d}")
print(f"   {nd} differ")

print("\nA. papers under another, loosely same-named PID (shared = co-authors shared with the researcher)")
for ps, ns_ in sorted(person.items(), key=lambda kv: kv[1][0]):
    mine_co = set().union(*(coauth[p] for p in ps))
    keys = {loose(n) for n in ns_} | {loose(pname[p]) for p in ps if p in pname}
    cands = set().union(*(by_loose.get(k, set()) for k in keys if k)) - set(ps)
    extra = [t for n in ns_ for t in EXTRA.get((V, n), [])]
    hits = []
    for q in cands:
        for r in recs.get(q, []):
            if any(t in r["title"] for t in extra): continue              # already credited by hand
            shared = {pname[x] for x in (p["pid"] for p in r["persons"]) if x in mine_co and x != q}
            hits.append((len(shared), r["year"], q, pname[q], r["title"][:58], sorted(shared)[:4]))
    if hits:
        mx = max(h[0] for h in hits)
        if mx == 0 and len(hits) > 6:
            print(f"   {' / '.join(ns_)}: {len(hits)} papers under other PIDs, none shares a co-author (skipped)")
            continue
        print(f"   {' / '.join(ns_)} (PIDs {sorted(ps)})")
        for h in sorted(hits, key=lambda h: (-h[0], h[1])):
            print(f"        shared {h[0]}: {h[1]} {h[2]} '{h[3]}' | {h[4]} | {', '.join(h[5])}")

print("\nB. 2024-2026 papers on a researcher's PID sharing no co-author with their other records")
for ps, ns_ in sorted(person.items(), key=lambda kv: kv[1][0]):
    other_co = defaultdict(set)
    for v, rs in DB.items():
        for rr in rs:
            if any(x["pid"] in ps for x in rr["persons"]):
                for x in rr["persons"]: other_co[x["pid"]].add(rr["publ"])
    for p in ps:
        for r in recs.get(p, []):
            if r["year"] < 2024: continue
            others = [x["pid"] for x in r["persons"] if x["pid"] not in ps]
            if not any(len(other_co[x] - {r["publ"]}) > 0 for x in others):
                print(f"   {' / '.join(ns_)}: {r['year']} {r['title'][:70]} | co: {', '.join(pname[x] for x in others)[:110]}")

print("\nC. not on the site: loose-name PID groups reaching 8 together (and single PIDs >= 8)")
site_pids = set().union(*person.keys())
for pid, rs in recs.items():
    if len(rs) >= 8 and pid not in site_pids: print(f"   single PID: {pname[pid]} {pid} = {len(rs)}")
seen = set()
for k, pids in by_loose.items():
    pids = {p for p in pids if p in recs}
    if len(pids) < 2 or pids & site_pids: continue
    fk = frozenset(pids)
    if fk in seen: continue
    seen.add(fk)
    tot = sum(len(recs[p]) for p in pids)
    if tot >= 8 and max(len(recs[p]) for p in pids) < 8:
        print(f"   {k}: " + ", ".join(f"{p} '{pname[p]}'={len(recs[p])}" for p in sorted(pids, key=lambda p: -len(recs[p]))))
        pl = sorted(pids)
        for i in range(len(pl)):
            for j in range(i + 1, len(pl)):
                sh = coauth[pl[i]] & coauth[pl[j]]
                if sh: print(f"        {pl[i]} ~ {pl[j]} share {len(sh)}: {', '.join(sorted(pname[x] for x in sh))[:150]}")
