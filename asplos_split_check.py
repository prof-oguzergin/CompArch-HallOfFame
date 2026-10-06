# -*- coding: utf-8 -*-
"""ASPLOS: look for papers dblp files under another identity of the same person (split PIDs), all years.

The 30 Sep verification counted by PID and fixed splits only where they were spotted by hand
(apply_dblp_verified.py PID / EXTRA_PUBL). Two were missed and surfaced in asplos2026_check.py:
Scott A. Mahlke (ASPLOS 2026 SNIP under the new 429/0057) and Quan Chen (ASPLOS'25 vol.3 Voyager
under 40/3858-1). This pass does it systematically:

A. every researcher on the site: other dblp PIDs with a loosely equal name (first + last token,
   middle initials and the 4-digit suffix dropped, nicknames folded, reversed order) that have
   ASPLOS main papers; each such paper is scored by co-author overlap with the researcher's
   co-authors in all four venues (dblp_sparql/{isca,micro,hpca}.json + fresh ASPLOS pull)
B. recent papers (2024-2026) on a researcher's own PID that share no co-author with anything else
   of theirs (possible homonym merged into the PID)
C. people not on the site: loose-name groups of PIDs that together reach 8 ASPLOS papers
Prints candidates for a manual decision; writes nothing."""
import json, re, sys, subprocess
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
src = open("apply_dblp_verified.py", encoding="utf-8").read(); ns = {}
exec(src.split("changes = []")[0], ns)
classify, norm, PIDMAP = ns["classify"], ns["norm"], ns["PID"]
FRESH = "dblp_sparql/asplos_20261006.json"
DB = {"asplos": json.load(open(FRESH, encoding="utf-8"))}
for v in ["isca", "micro", "hpca"]: DB[v] = json.load(open(f"dblp_sparql/{v}.json", encoding="utf-8"))
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D))']).decode("utf-8"))

NICK = {"bill": "william", "will": "william", "bob": "robert", "rob": "robert", "rick": "richard", "rich": "richard",
        "ted": "edward", "ed": "edward", "jim": "james", "tom": "thomas", "mike": "michael", "dave": "david",
        "steve": "steven", "stephen": "steven", "andy": "andrew", "chris": "christopher", "christos": "christoforos",
        "dan": "daniel", "ron": "ronald", "tim": "timothy", "nick": "nicholas", "alex": "alexander", "ben": "benjamin",
        "sam": "samuel", "matt": "matthew", "greg": "gregory", "joe": "joseph", "jon": "jonathan", "tony": "anthony",
        "ken": "kenneth", "larry": "lawrence", "phil": "philip", "hank": "henry", "fred": "frederic", "frederick": "frederic",
        "ram": "ramachandran", "babak": "babak", "josh": "joshua", "pat": "patrick"}
def loose(name):
    t = [w for w in norm(name).split() if len(w) > 1]
    if not t: return None
    return (NICK.get(t[0], t[0]), t[-1]) if len(t) > 1 else (t[0], t[0])

# ---- per-PID ASPLOS main records, co-author sets over all venues ----
asp = [r for r in DB["asplos"] if classify("asplos", r) == "MAIN"]
recs = defaultdict(list); pname = {}
for r in asp:
    for p in r["persons"]: recs[p["pid"]].append(r); pname[p["pid"]] = p["name"]
coauth = defaultdict(set)          # pid -> set of co-author PIDs (all venues, main + other records)
for v, rs in DB.items():
    for r in rs:
        ps = [p["pid"] for p in r["persons"]]
        for p in r["persons"]:
            pname.setdefault(p["pid"], p["name"])
            coauth[p["pid"]].update(q for q in ps if q != p["pid"])
by_loose = defaultdict(set)
for pid, n in pname.items():
    k = loose(n)
    if k: by_loose[k].add(pid); by_loose[(k[1], k[0])].add(pid)    # reversed order too

# ---- the site's researchers and their canonical PIDs ----
names = sorted({e["name"] for v in ["isca", "micro", "asplos", "hpca"] for e in D[v]})
def canon(name):
    if name in PIDMAP: return set(PIDMAP[name])
    p = D["affiliations"].get(name, {}).get("pid")
    if p: return {p}
    for k, v in D["affiliations"].items():
        if norm(k) == norm(name) and v.get("pid"): return {v["pid"]}
    c = {q for q in by_loose.get(loose(name), set()) if norm(pname[q]) == norm(name)}
    return c if len(c) == 1 else set()
person = {}                         # frozenset(pids) -> list of site names (aliases grouped)
for n in names:
    ps = canon(n)
    if ps: person.setdefault(frozenset(ps), []).append(n)
unres = [n for n in names if not canon(n)]
site_asplos = {}
for ps, ns_ in person.items():
    m = [e for e in D["asplos"] if e["name"] in ns_]
    site_asplos[ps] = m[0]["total"] if m else max(D["crossvenue"].get(n, {}).get("asplos", 0) for n in ns_)

print(f"site researchers {len(names)}, grouped persons {len(person)}, unresolved names {unres}")
print("\nA. ASPLOS papers under another, loosely same-named PID (score = shared co-authors)")
for ps, ns_ in sorted(person.items(), key=lambda kv: kv[1][0]):
    mine_co = set().union(*(coauth[p] for p in ps))
    keys = {loose(n) for n in ns_} | {loose(pname[p]) for p in ps if p in pname}
    cands = set().union(*(by_loose.get(k, set()) for k in keys if k)) - set(ps)
    hits = []
    for q in cands:
        for r in recs.get(q, []):
            shared = {pname[x] for x in (p["pid"] for p in r["persons"]) if x in mine_co and x != q}
            hits.append((len(shared), r["year"], r["venue"], q, pname[q], r["title"][:60], sorted(shared)[:4]))
    if hits:
        cur = site_asplos[ps]; mx = max(h[0] for h in hits)
        print(f"   {' / '.join(ns_)} (site ASPLOS {cur}; PIDs {sorted(ps)})")
        for h in sorted(hits, key=lambda h: (-h[0], h[1])):
            if h[0] == 0 and mx == 0 and len(hits) > 6: continue        # long list of unrelated homonyms
            print(f"        shared {h[0]}: {h[1]} {h[2]:11} {h[3]} '{h[4]}' | {h[5]} | {', '.join(h[6])}")

print("\nB. 2024-2026 ASPLOS papers on a researcher's PID sharing no co-author with their other records")
for ps, ns_ in sorted(person.items(), key=lambda kv: kv[1][0]):
    for p in ps:
        for r in recs.get(p, []):
            if r["year"] < 2024: continue
            others = [x["pid"] for x in r["persons"] if x["pid"] != p]
            # co-authors seen with this person on some OTHER record
            other_recs_co = set()
            for v, rs in DB.items():
                for rr in rs:
                    if rr is r or rr["publ"] == r["publ"]: continue
                    if any(x["pid"] in ps for x in rr["persons"]):
                        other_recs_co.update(x["pid"] for x in rr["persons"])
            if not set(others) & other_recs_co:
                print(f"   {' / '.join(ns_)}: {r['year']} {r['venue']} {r['title'][:70]} | co: {', '.join(pname[x] for x in others)[:120]}")

print("\nC. not on the site: loose-name PID groups reaching 8 ASPLOS main papers together")
site_pids = set().union(*person.keys())
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
        # pairwise co-author overlap between the PIDs
        pl = sorted(pids)
        for i in range(len(pl)):
            for j in range(i + 1, len(pl)):
                sh = coauth[pl[i]] & coauth[pl[j]]
                if sh: print(f"        {pl[i]} ~ {pl[j]} share {len(sh)}: {', '.join(sorted(pname[x] for x in sh))[:150]}")
