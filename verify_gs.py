# -*- coding: utf-8 -*-
"""Check that each Google Scholar profile in gs_refresh_20261006.json is the right person (6 Oct 2026).

Three wrong profiles had been on the site since April: G. Jack Lipovski -> "Jack Kramer", Christos A.
Papachristou -> "Christos Papachristos" (robotics), Amir Roth -> "Aaron Roth" (privacy). A last-name check
missed the last one, so this one asks for more:
  1. name: same last name AND a compatible first name (equal, an initial, a known short form, or our
     middle name, as in "G. Edward Suh" -> "Edward Suh")
  2. papers: how many of the profile's 10 most-cited titles are papers of this person in the four venues
     (dblp, canonical PIDs); 0 is not proof of a wrong profile (top papers can be journals) but is shown
  3. affiliation line of the profile next to the site's institution
Prints the profiles that fail 1, or have no paper match, for a manual look."""
import json, re, subprocess, sys, unicodedata
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
R = json.load(open("gs_refresh_20261006.json", encoding="utf-8"))
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify({gs:D.gs,aff:D.affiliations}))']).decode("utf-8"))
src = open("apply_dblp_verified.py", encoding="utf-8").read(); g = {}
exec("PID = " + src.split("PID = ")[1].split("\nEXTRA_PUBL")[0], {}, g); PIDMAP = g["PID"]
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower().replace("ı", "i")) if unicodedata.category(c) != "Mn")
def toks(s): return [w for w in re.sub(r"[^a-z ]", " ", re.sub(r"\(.*?\)|（.*?）", " ", fold(s).replace("-", ""))).split() if w]
SHORT = {"fred": "frederic", "chris": "christopher", "mike": "michael", "jim": "james", "tom": "thomas", "dave": "david",
         "bob": "robert", "bill": "william", "andy": "andrew", "dan": "daniel", "joe": "joseph", "ed": "edward", "ted": "edward",
         "guri": "gurindar", "steve": "steven", "stephen": "steven", "christos": "christoforos", "tim": "timothy", "ben": "benjamin",
         "nam": "nam", "hank": "henry", "rich": "richard", "rick": "richard", "greg": "gregory", "matt": "matthew"}
def name_ok(ours, theirs):
    a, b = toks(ours), toks(theirs)
    if not a or not b: return False
    if a[-1] != b[-1] and "".join(a[-2:]) != b[-1] and a[-1] != "".join(b[-2:]): return False
    firsts_a, fb = a[:-1] or a, b[0]
    canon = lambda w: SHORT.get(w, w)
    return any(canon(x) == canon(fb) or (len(x) == 1 and x == fb[0]) or (len(fb) == 1 and fb == x[0]) for x in firsts_a) or len(b) == 1
# dblp titles per canonical PID, all four venues
titles = defaultdict(set)
for v in ["isca", "micro", "hpca", "asplos"]:
    for r in json.load(open(f"dblp_sparql/{v}_20261006.json", encoding="utf-8")):
        t = re.sub(r"[^a-z0-9]", "", fold(r["title"]))[:40]
        for p in r["persons"]: titles[p["pid"]].add(t)
def pids(name):
    if name in PIDMAP: return set(PIDMAP[name])
    p = D["aff"].get(name, {}).get("pid")
    return {p} if p else set()
by_id = defaultdict(list)
for n, x in D["gs"].items(): by_id[x["gs"]].append(n)
for gid, n in {"om-NSbgAAAAJ": "Minesh Patel", "BHupl5EAAAAJ": "André Seznec", "X-HEAfgAAAAJ": "Amir Roth"}.items():
    by_id.setdefault(gid, [n])
bad = 0
for gid, r in sorted(R.items(), key=lambda kv: by_id.get(kv[0], ["?"])[0]):
    names = by_id.get(gid, ["?"])
    if "error" in r: print(f"ERROR   {names[0]} {gid}: {r['error']}"); continue
    ok = any(name_ok(n, r.get("gs_name")) for n in names)
    ps = set().union(*(pids(n) for n in names))
    mine = set().union(*(titles[p] for p in ps)) if ps else set()
    hits = sum(1 for t in r.get("titles", []) if re.sub(r"[^a-z0-9]", "", fold(t))[:40] in mine)
    inst = next((D["aff"][n]["inst"] for n in names if n in D["aff"]), "?")
    has_titles = bool(r.get("titles"))
    if not ok or (has_titles and hits == 0):
        bad += 1
        print(f"{'NAME' if not ok else 'PAPERS'}  {names[0]} [{inst}] -> '{r.get('gs_name')}' ({r.get('aff')}) {gid} | "
              f"top-10 titles in our venues: {hits if has_titles else 'n/a'} | {(r.get('titles') or [''])[0][:60]}")
print(f"{len(R)} profiles, {bad} to look at")
