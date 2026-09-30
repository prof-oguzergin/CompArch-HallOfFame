# -*- coding: utf-8 -*-
"""Recompute crossvenue (counts <8 at venues where a HoF member is not listed) from dblp main-track
papers, by PID identity; canonicalize affiliation PIDs. Dry run unless --apply."""
import json, re, sys, subprocess
APPLY = "--apply" in sys.argv
src = open("dblp_verify.py", encoding="utf-8").read(); ns = {}
exec(src.split("hof = json.load")[0], ns); classify, norm = ns["classify"], ns["norm"]
ap = open("apply_dblp_verified.py", encoding="utf-8").read(); g = {}
exec("PID = " + ap.split("PID = ")[1].split("\nEXTRA_PUBL")[0], {}, g); PID = g["PID"]
VEN = ["hpca", "micro", "isca", "asplos"]
DB = {v: json.load(open(f"dblp_sparql/{v}.json", encoding="utf-8")) for v in VEN}
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");'
    'const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify({hpca:D.hpca,micro:D.micro,isca:D.isca,asplos:D.asplos,affiliations:D.affiliations,crossvenue:D.crossvenue}))'
]).decode("utf-8"))
stream_names = {}                                   # norm(name) -> set(pid) over all four streams
for v in VEN:
    for r in DB[v]:
        for p in r["persons"]: stream_names.setdefault(norm(p["name"]), set()).add(p["pid"])
all_pids = set(p for s in stream_names.values() for p in s)
def pids_of(name):
    if name in PID: return set(PID[name])
    a = next((x.get("pid") for k, x in D["affiliations"].items() if norm(k) == norm(name)), None)
    if a and a in all_pids: return {a}
    c = stream_names.get(norm(name), set())
    return c if len(c) == 1 else set()
def main_count(v, ps):
    return sum(1 for r in DB[v] if classify(v, r) == "MAIN" and any(p["pid"] in ps for p in r["persons"]))
# identity of every HoF member, and which venues they are listed in (by pid, so name variants merge)
member_venues = {}   # frozenset(pids) -> set(venues)
names_by_id = {}
people = set(e["name"] for v in VEN for e in D[v]) | set(D["crossvenue"].keys())
unres = []
for n in people:
    ps = pids_of(n)
    if not ps: unres.append(n); continue
    key = frozenset(ps)
    # merge identities that share any pid
    for k in list(member_venues):
        if k & key:
            key = frozenset(k | key); member_venues[key] = member_venues.pop(k) | member_venues.get(key, set())
            names_by_id[key] = names_by_id.pop(k, set()) | names_by_id.get(key, set())
    member_venues.setdefault(key, set()); names_by_id.setdefault(key, set()).add(n)
    for v in VEN:
        if any(e["name"] == n for e in D[v]): member_venues[key].add(v)
changes = []
for key, venues in member_venues.items():
    if not venues and not any(n in D["crossvenue"] for n in names_by_id[key]): continue
    # the crossvenue entry name: existing one if any, else the name used in the venue lists
    cvname = next((n for n in sorted(names_by_id[key]) if n in D["crossvenue"]), sorted(names_by_id[key])[0])
    new = {}
    for v in VEN:
        if v in venues: continue
        c = main_count(v, key)
        if c >= 8: print(f"  !! {cvname} has {c} main papers at {v} but is not listed there")
        if c: new[v] = c
    old = {k: int(x) for k, x in D["crossvenue"].get(cvname, {}).items()}
    if new != old: changes.append((cvname, old, new))
for n, o, w in sorted(changes): print(f"  {n:30s} {o} -> {w}")
print(len(changes), "crossvenue entries change;", "unresolved:", unres)
json.dump(changes, open("dblp_sparql/cv_changes.json", "w", encoding="utf-8"), ensure_ascii=False)
if APPLY:
    data = open("data.js", encoding="utf-8").read()
    cs = data.index("\ncrossvenue: {"); ce = data.index("\n},", cs) + 1
    lines = data[cs:ce].split("\n")
    fmt = lambda n, c: f'  "{n}": {{' + ",".join(f"{v}:{c[v]}" for v in VEN if v in c) + "},"
    for n, o, w in changes:
        idx = next((i for i, l in enumerate(lines) if l.startswith(f'  "{n}":')), None)
        if idx is not None:
            if w: lines[idx] = fmt(n, w)
            else: del lines[idx]
        elif w:
            lines.insert(2, fmt(n, w))
    data = data[:cs] + "\n".join(lines) + data[ce:]
    open("data.js", "w", encoding="utf-8", newline="").write(data)
    print("crossvenue written")
