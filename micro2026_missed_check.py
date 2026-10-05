# -*- coding: utf-8 -*-
"""Second pass for MICRO 2026 entrants: look for anyone the first pass could have missed.
A. dblp splits one person over several PIDs (each PID < 8, together >= 8)
B. nickname first names (Bill/William, Bob/Robert, ...) and other first-name variants with the same surname
C. reversed name order (Chinese names written family-name first)
D. industry-track papers: would counting them push anyone to 8?
E. every program author with >= 3 MICRO 2026 papers, with all dblp persons of the same surname
Prints candidates for a manual look; nothing is written."""
import json, re, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
src = open("micro2026_match.py", encoding="utf-8").read(); ns = {}; exec(src.split("sessions = json.load")[0], ns)
fold, key = ns["fold"], ns["key"]
ns2 = {}; exec(open("dblp_verify.py", encoding="utf-8").read().split("hof = json.load")[0], ns2); classify = ns2["classify"]
C = json.load(open("micro2026_candidates.json", encoding="utf-8"))
papers = C["papers"]
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D.micro.map(e=>e.name)))']).decode("utf-8"))
members = {key(n) for n in D}
DBM = json.load(open("dblp_sparql/micro.json", encoding="utf-8"))
cnt, nm = {}, {}
for r in DBM:
    if classify("micro", r) != "MAIN": continue
    for p in r["persons"]:
        cnt[p["pid"]] = cnt.get(p["pid"], 0) + 1; nm[p["pid"]] = p["name"]
def toks(n): return [w for w in re.split(r"\s+", fold(n).replace("-", " ")) if w]
prog = {}   # key -> list of (name, aff, title, industry)
for p in papers:
    for n, aff in p["authors"]:
        if toks(n): prog.setdefault(key(n), []).append((n, aff, p["title"][:60], p["industry"]))
def n26(k, industry=False): return len({t for _, _, t, ind in prog.get(k, []) if industry or not ind})

print("A. same name key over several dblp PIDs, together >= 8 (no single PID >= 8):")
by_key = {}
for pid, n in nm.items(): by_key.setdefault(key(n), []).append(pid)
for k, pids in by_key.items():
    if k in members or k not in prog or len(pids) < 2: continue
    tot = sum(cnt[p] for p in pids) + n26(k)
    if tot >= 8 and all(cnt[p] + n26(k) < 8 for p in pids):
        print(f"   {' '.join(k)}: " + ", ".join(f"{p}={cnt[p]}" for p in pids) + f" + 2026 {n26(k)}")
        for x in prog[k]: print("        2026:", x[:3])

NICK = {"bill": "william", "will": "william", "bob": "robert", "rob": "robert", "bert": "robert", "rick": "richard", "dick": "richard",
        "rich": "richard", "ted": "edward", "ed": "edward", "jim": "james", "jimmy": "james", "tom": "thomas", "mike": "michael",
        "dave": "david", "steve": "steven", "stephen": "steven", "andy": "andrew", "drew": "andrew", "chris": "christopher",
        "dan": "daniel", "danny": "daniel", "ron": "ronald", "tim": "timothy", "nick": "nicholas", "alex": "alexander",
        "alexandros": "alexander", "ben": "benjamin", "sam": "samuel", "matt": "matthew", "greg": "gregory", "josh": "joshua",
        "pat": "patrick", "joe": "joseph", "jon": "jonathan", "tony": "anthony", "liz": "elizabeth", "beth": "elizabeth",
        "kate": "katherine", "cathy": "catherine", "peggy": "margaret", "maggie": "margaret", "hank": "henry", "harry": "henry",
        "chuck": "charles", "charlie": "charles", "fred": "frederic", "frederick": "frederic", "phil": "philip", "ken": "kenneth",
        "larry": "lawrence", "jerry": "gerald", "gus": "augustus", "vijay": "vijaykumar", "sudha": "sudhakar", "raj": "rajeev"}
canon = lambda f: NICK.get(f, f)
print("\nB/C. dblp persons with >= 2 pre-2026 MICRO papers matched by nickname, surname-only or reversed name:")
prog_last = {}
for k, xs in prog.items():
    for n, *_ in xs:
        t = toks(n); prog_last.setdefault(t[-1], set()).add(n)
seen = set()
for pid, c in sorted(cnt.items(), key=lambda x: -x[1]):
    if c < 2: continue
    k = key(nm[pid])
    if k in members or k in prog: continue
    t = toks(nm[pid])
    if len(t) < 2: continue
    first, last = t[0], t[-1]
    hits = []
    for n in prog_last.get(last, ()):          # same surname, first name equal after nickname folding
        pt = toks(n)
        if canon(pt[0]) == canon(first) or (pt[0][0] == first[0] and (pt[0].startswith(first) or first.startswith(pt[0]))):
            hits.append(("nickname/short", n))
    for n in prog_last.get(first, ()):          # reversed order: program "Last First"
        if toks(n)[0] == last: hits.append(("reversed", n))
    for how, n in hits:
        kk = key(n)
        if (pid, n) in seen: continue
        seen.add((pid, n))
        print(f"   {nm[pid]} ({pid}, {c} before) <-{how}-> {n}: 2026 {n26(kk)} => {c + n26(kk)}")

print("\nD. counting the industry-track session too, who would reach 8?")
for k, xs in prog.items():
    if k in members: continue
    ind = n26(k, True) - n26(k)
    if not ind: continue
    for pid in by_key.get(k, []):
        if cnt[pid] + n26(k) < 8 <= cnt[pid] + n26(k, True):
            print(f"   {nm[pid]} ({pid}): {cnt[pid]} + {n26(k)} regular + {ind} industry")
print("   (done)")

print("\nE. program authors with >= 3 MICRO 2026 papers who are not MICRO members, with every dblp person of that surname:")
for k, xs in sorted(prog.items(), key=lambda kv: -n26(kv[0])):
    if k in members or n26(k) < 3: continue
    same_last = [(pid, nm[pid], cnt[pid]) for pid in cnt if toks(nm[pid]) and toks(nm[pid])[-1] == k[1] and toks(nm[pid])[0][0] == k[0][0]]
    print(f"   {xs[0][0]} ({xs[0][1][:40]}): 2026 {n26(k)} | dblp: " + ", ".join(f"{n} {p}={c}" for p, n, c in sorted(same_last, key=lambda x: -x[2])[:4]))
