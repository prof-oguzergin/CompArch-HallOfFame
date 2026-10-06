# -*- coding: utf-8 -*-
"""ASPLOS Hall of Fame: check the counts against a fresh dblp pull and the ASPLOS 2026 conference program.

dblp is the counting basis, so the risk is dblp's author disambiguation, worst for the newest papers.
The program (asplos26_sessions.json, curl'ed raw HTML) gives every author's affiliation, which lets us
see whether a 2026 paper dblp gives to a member's PID really is that person, and whether a member's
2026 paper sits under some other PID.

1. data.js vs fresh dblp, per member (total and per year)
2. program <-> dblp title match (ASPLOS'26 vol 1-2, and ASPLOS'25 vol 3, which was presented in 2026)
3. every 2026 paper on a member's PID, with the affiliation the program prints for that author
4. program authors whose name matches a member but whose dblp PID is a different one
5. possible new members: one PID >= 8, or one name split over several PIDs that together reach 8
Prints a report; writes nothing except dblp_sparql/asplos2026_check.json."""
import json, re, sys, subprocess, difflib
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ns = {}; exec(open("dblp_verify.py", encoding="utf-8").read().split("hof = json.load")[0], ns)
classify, norm = ns["classify"], ns["norm"]
FRESH = sys.argv[1] if len(sys.argv) > 1 else "dblp_sparql/asplos_20261006.json"
R = json.load(open(FRESH, encoding="utf-8"))
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify({asplos:D.asplos,aff:D.affiliations,cv:D.crossvenue,'
    'all:[...new Set([].concat(D.isca,D.micro,D.asplos,D.hpca).map(e=>e.name))]}))']).decode("utf-8"))

# ---- dblp per PID ----
main = [r for r in R if classify("asplos", r) == "MAIN"]
cnt, years, nm, recs_of = defaultdict(int), defaultdict(lambda: defaultdict(int)), {}, defaultdict(list)
name_pids = defaultdict(set)
for r in main:
    for p in r["persons"]:
        cnt[p["pid"]] += 1; years[p["pid"]][r["year"]] += 1; nm[p["pid"]] = p["name"]; recs_of[p["pid"]].append(r)
        name_pids[norm(p["name"])].add(p["pid"])
for r in R:
    for p in r["persons"]:
        nm.setdefault(p["pid"], p["name"]); name_pids[norm(p["name"])].add(p["pid"])
def conf_year(r):          # ASPLOS'23 vol 1 is dated 2022 in dblp
    return 2023 if (r["year"] == 2022 and r["venue"] == "ASPLOS (1)") else r["year"]

# ---- member -> PID (same rule as dblp_verify.py: affiliation PID, else the only PID with that name) ----
affpid = {norm(k): v.get("pid") for k, v in D["aff"].items()}
def pid_for(name):
    k = norm(name); p = affpid.get(k)
    if p and (p in cnt or p in nm): return p, "aff"
    c = name_pids.get(k, set())
    if len(c) == 1: return next(iter(c)), "name"
    return None, f"UNRESOLVED({len(c)})"
members = {e["name"]: e for e in D["asplos"]}
everyone = set(D["all"])                      # all 271 researchers (crossvenue ASPLOS counts too)
pid_of_person = {n: pid_for(n) for n in everyone}
person_of_pid = {p: n for n, (p, _) in pid_of_person.items() if p}

print("1. data.js vs fresh dblp (ASPLOS members)")
bad = 0
for n, e in members.items():
    p, how = pid_of_person[n]
    dy = {conf_year_y: c for conf_year_y, c in sorted(years[p].items())} if p else {}
    # merge the 2022 vol-1 records into 2023 the way the site does
    dy2 = defaultdict(int)
    for r in recs_of.get(p, []): dy2[conf_year(r)] += 1
    hy = {int(y): c for y, c in e["y"].items()}
    if sum(dy2.values()) != e["total"] or dict(dy2) != hy:
        bad += 1
        print(f"   {n} ({p}, {how}): site {e['total']} {hy} | dblp {sum(dy2.values())} {dict(sorted(dy2.items()))}")
print(f"   {len(members)} members, {bad} differ")
print("   non-members' ASPLOS counts (crossvenue):")
cvbad = 0
for n in sorted(everyone - set(members)):
    p, how = pid_of_person[n]
    site = D["cv"].get(n, {}).get("asplos", 0)
    db = cnt.get(p, 0) if p else 0
    if site != db:
        cvbad += 1; print(f"      {n} ({p}, {how}): site {site} | dblp {db}")
print(f"      {len(everyone - set(members))} non-members, {cvbad} differ")

# ---- program ----
S = json.load(open("asplos26_sessions.json", encoding="utf-8"))
def split_authors(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(": depth += 1
        if ch == ")": depth -= 1
        if ch == "," and depth == 0: out.append(cur.strip()); cur = ""
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    res = []
    for a in out:
        m = re.match(r"^(.*?)\s*\((.*)\)\s*$", a)
        res.append((m.group(1).strip(), m.group(2).strip()) if m else (a, ""))
    return res
prog = []
for sess, papers in S:
    for t, au in papers:
        prog.append({"session": sess, "title": t, "authors": split_authors(au)})
tkey = lambda t: re.sub(r"[^a-z0-9]", "", ns["sa"](t.lower()))
cand = [r for r in main if (r["year"] == 2026) or (r["year"] == 2025 and r["venue"] == "ASPLOS (3)")]
by_t = {tkey(r["title"]): r for r in cand}
matched, unmatched = [], []
for p in prog:
    k = tkey(p["title"]); r = by_t.get(k)
    if not r:
        best = difflib.get_close_matches(k, list(by_t), n=1, cutoff=0.85)
        r = by_t.get(best[0]) if best else None
    (matched if r else unmatched).append((p, r))
print(f"\n2. program papers {len(prog)}, matched to dblp {len(matched)}, unmatched {len(unmatched)}")
for p, _ in unmatched: print("   NO DBLP:", p["session"][:30], "|", p["title"][:80])
used = {id(r) for _, r in matched}
for r in cand:
    if id(r) not in used: print("   dblp record not in program:", r["year"], r["venue"], r["title"][:80])
from collections import Counter
print("   matched by volume:", dict(Counter(f"{r['year']} {r['venue']}" for _, r in matched)))

# ---- align program authors to dblp persons inside each paper ----
def toks(n): return [w for w in norm(n).split() if w]
def sim(a, b):
    ta, tb = toks(a), toks(b)
    if not ta or not tb: return 0
    if ta == tb: return 1.0
    if ta[-1] == tb[-1] and ta[0][0] == tb[0][0]: return 0.8
    if set(ta) == set(tb): return 0.9                       # reversed order
    return difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio() * 0.7
align = []      # (paper, prog_name, prog_aff, pid, dblp_name, score)
for p, r in matched:
    persons = list(r["persons"]); taken = set()
    for n, aff in p["authors"]:
        best = max(((sim(n, q["name"]), i) for i, q in enumerate(persons) if i not in taken), default=(0, None))
        if best[1] is not None and best[0] >= 0.5:
            taken.add(best[1]); q = persons[best[1]]
            align.append((p, r, n, aff, q["pid"], q["name"], best[0]))
        else:
            align.append((p, r, n, aff, None, None, 0))
    for i, q in enumerate(persons):
        if i not in taken: align.append((p, r, None, None, q["pid"], q["name"], 0))
weak = [a for a in align if a[6] < 1.0]
print(f"   author alignment: {len(align)} slots, {len(weak)} not exact (listed if they touch a member)")

print("\n3. every 2026-program paper on a researcher's PID, with the program's affiliation")
inst = {n: D["aff"].get(n, {}).get("inst", "?") for n in everyone}
per = defaultdict(list)
for p, r, n, aff, pid, dn, sc in align:
    if pid in person_of_pid:
        per[person_of_pid[pid]].append((r["year"], r["venue"], n, aff, r["title"][:70], sc))
for who in sorted(per, key=lambda w: (w not in members, w)):
    tag = "ASPLOS member" if who in members else "other HoF"
    print(f"   {who} [{tag}; site inst: {inst[who]}]")
    for y, v, n, aff, t, sc in sorted(per[who]):
        flag = "" if sc == 1.0 else f"   <-- name '{n}' (score {sc:.2f})"
        print(f"        {y} {v:11} {aff[:45]:45} | {t}{flag}")

print("\n4. program authors named like a researcher but on another dblp PID (or no PID)")
keyset = {norm(n): n for n in everyone}
for p, r, n, aff, pid, dn, sc in align:
    if n is None: continue
    who = keyset.get(norm(n))
    if who and pid != pid_of_person[who][0]:
        print(f"   {n} ({aff[:50]}) -> dblp {pid} '{dn}' | researcher {who} is {pid_of_person[who][0]} ({inst[who]}) | {r['year']} {r['title'][:60]}")

print("\n5. possible new ASPLOS members")
mpids = {pid_of_person[n][0] for n in members}
for pid, c in sorted(cnt.items(), key=lambda x: -x[1]):
    if c >= 8 and pid not in mpids: print(f"   PID >= 8 not on the site: {nm[pid]} {pid} = {c}")
groups = defaultdict(list)
for pid in cnt: groups[norm(re.sub(r"\s+\d{4}$", "", nm[pid]))].append(pid)
for k, pids in groups.items():
    if len(pids) < 2: continue
    tot = sum(cnt[p] for p in pids)
    if tot >= 8 and not any(p in mpids for p in pids):
        recent = sum(years[p].get(y, 0) for p in pids for y in (2024, 2025, 2026))
        print(f"   name split: {k}: " + ", ".join(f"{p}={cnt[p]}" for p in pids) + f" (total {tot}, 2024-26: {recent})")
json.dump({"per": per}, open("dblp_sparql/asplos2026_check.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
