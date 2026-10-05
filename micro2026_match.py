# -*- coding: utf-8 -*-
"""MICRO 2026 (MICRO-59) program -> Hall of Fame update candidates.

Reads micro59_sessions.json (parsed from the raw program HTML, never WebFetch), splits author
lists into (name, affiliation), then
  1. matches authors to current MICRO members (name tokens without initials + affiliation check),
  2. finds new entrants: every program author's pre-2026 MICRO main-paper count from the dblp
     SPARQL dump (dblp_sparql/micro.json, PID based) plus 2026 papers >= 8.
Name matches are only candidates; ambiguous or affiliation-mismatched ones are printed for a
manual check. Output: micro2026_candidates.json
"""
import json, re, subprocess, unicodedata, sys
sys.stdout.reconfigure(encoding="utf-8")

SKIP_SESSIONS = ("Opening Remarks", "PhD Jobs", "SRC Session", "Title TBA")

def fold(s):
    s = s.replace(".", " ").lower()
    for a, b in (("ğ", "g"), ("ı", "i"), ("ç", "c"), ("ş", "s"), ("ö", "o"), ("ü", "u")):
        s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z\- ]", " ", s)

def key(name):
    """first and last name tokens, initials and dblp number suffixes dropped"""
    t = [w for w in re.split(r"[\s]+", fold(name)) if len(w) > 1]
    return (t[0], t[-1]) if t else ("", "")

def split_top(a, sep=";"):
    """split on sep outside parentheses (affiliations may contain ';')"""
    parts, depth, cur = [], 0, ""
    for ch in a:
        depth += (ch == "(") - (ch == ")")
        if ch == sep and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    return parts + [cur]

def split_authors(a):
    out = []
    for grp in [g.strip() for g in split_top(a) if g.strip()]:
        m = re.match(r"^(.*?)\s*\((.*)\)\s*$", grp)
        names, aff = (m.group(1), m.group(2)) if m else (grp, "")
        for n in [x.strip() for x in names.split(",") if x.strip()]:
            out.append((n, aff))
    return out

sessions = json.load(open("micro59_sessions.json", encoding="utf-8"))
papers = []
for title, ps in sessions:
    if any(k in title for k in SKIP_SESSIONS):
        continue
    for t, a in ps:
        papers.append({"session": title, "title": t, "authors": split_authors(a),
                       "industry": "Industry" in title})
print(len(papers), "papers (", sum(p["industry"] for p in papers), "industry )")

D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");'
    'const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify({micro:D.micro,affiliations:D.affiliations,crossvenue:D.crossvenue}))']).decode("utf-8"))

# ---- 1. existing MICRO members ----
by_key = {}
for p in papers:
    for n, aff in p["authors"]:
        by_key.setdefault(key(n), []).append((p, n, aff))
members = {}
for e in D["micro"]:
    k = key(e["name"])
    hits = by_key.get(k, [])
    inst = (D["affiliations"].get(e["name"]) or {}).get("inst", "")
    if hits:
        members[e["name"]] = {"inst": inst, "papers": [(p["title"], n, aff, p["industry"]) for p, n, aff in hits]}
print("\n=== current MICRO members with MICRO 2026 papers:", len(members))
for name, v in sorted(members.items()):
    print(f"- {name} [{v['inst']}]: {len(v['papers'])}")
    for t, n, aff, ind in v["papers"]:
        print(f"     {'(industry) ' if ind else ''}{n} ({aff}) :: {t[:70]}")

# ---- 2. everybody else: pre-2026 dblp MICRO main count by name ----
exec(open("dblp_verify.py", encoding="utf-8").read().split("hof = json.load")[0])   # classify()
DBM = json.load(open("dblp_sparql/micro.json", encoding="utf-8"))
pid_count, pid_name = {}, {}
for r in DBM:
    if classify("micro", r) != "MAIN":
        continue
    for p in r["persons"]:
        pid_count[p["pid"]] = pid_count.get(p["pid"], 0) + 1
        pid_name[p["pid"]] = p["name"]
key_pids = {}
for pid, nm in pid_name.items():
    key_pids.setdefault(key(nm), set()).add(pid)
member_keys = {key(e["name"]) for e in D["micro"]}
cands = []
for k, hits in by_key.items():
    if k in member_keys:
        continue
    n2026 = len({id(p) for p, _, _ in hits})
    for pid in key_pids.get(k, ()):
        before = pid_count.get(pid, 0)
        if before + n2026 >= 8:
            cands.append({"key": " ".join(k), "pid": pid, "dblp_name": pid_name[pid], "before": before, "n2026": n2026,
                          "program": [(n, aff, p["title"][:70]) for p, n, aff in hits]})
print("\n=== possible new MICRO entrants (dblp count before 2026 + 2026 papers >= 8):", len(cands))
for c in sorted(cands, key=lambda c: -(c["before"] + c["n2026"])):
    print(f"- {c['dblp_name']} pid={c['pid']}: {c['before']} + {c['n2026']} = {c['before'] + c['n2026']}")
    for n, aff, t in c["program"]:
        print(f"     {n} ({aff}) :: {t}")
json.dump({"members": members, "candidates": cands, "papers": papers}, open("micro2026_candidates.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
