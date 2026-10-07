# -*- coding: utf-8 -*-
"""Write the refreshed Google Scholar metrics (refresh_gs.py -> gs_refresh_20261006.json) into data.js gs.
Can run while the refresh is still going: profiles not read yet keep their April 2026 figures.

Profile fixes (verify_gs.py: full name, top-cited titles against dblp, affiliation; 6-7 Oct 2026):
- REMOVE, no Scholar profile of their own (the stored one belonged to someone else) or the profile is gone
- REPLACE, the stored ID was someone else's and the right profile was found; until that profile has been
  read the person shows no figures (never the wrong person's)
- PENDING, the stored ID is someone else's and the right one is not settled yet: no figures for now
- NEW, researchers who had no Scholar data, profiles checked by hand
Not found or not usable at all: Gurindar S. Sohi, David H. Albonesi, Michel Dubois (search results were other
people), Luiz André Barroso (profile removed), Edward S. Davidson, Bob Ramakrishna Rau, Andrew R. Pleszkun,
Michael Schlansker.
Run with --apply to write; otherwise prints the changes."""
import json, re, sys, time
sys.stdout.reconfigure(encoding="utf-8")
APPLY = "--apply" in sys.argv
for _ in range(5):                       # the refresh may be rewriting the file right now
    try:
        R = json.load(open("gs_refresh_20261006.json", encoding="utf-8")); break
    except json.JSONDecodeError:
        time.sleep(2)
REMOVE = {
    "G. Jack Lipovski": "o0yYm6kAAAAJ is Jack Kramer",
    "Christos A. Papachristou": "jmMI3eUAAAAJ is Christos Papachristos (robotics)",
    "Jean-Loup Baer": "5pWnG_oAAAAJ is John S. Baer (psychology, UW)",
    "Amro Awad": "jDmd7AoAAAAJ answers 404 since 6 Oct 2026 (also in a browser)",
}
REPLACE = {
    "Amir Roth": "X-HEAfgAAAAJ",          # kLUQrrYAAAAJ is Aaron Roth (Penn, privacy); his own profile: US DOE
    "Jae W. Lee": "PA-QN6IAAAAJ",         # 6MspJJcAAAAJ is Jae Won Lee (Samsung Research, patents); his own: SNU
    "Jonathan M. Baker": "87cLl3gAAAAJ",  # Cn7wuysAAAAJ is Jonathan Baker (Met Office, climate); his own: UT Austin
    "Chao Li": "Yy-wQg4AAAAJ",            # gF8h0HMAAAAJ is Chao Li (Zhejiang Lab, edge AI); his own: SJTU, architecture
}
PENDING = {"Kang Chen": "rDXG570AAAAJ is Kang Chen (China University of Geosciences, geology); candidates being checked"}
NEW = {"Minesh Patel": "om-NSbgAAAAJ", "André Seznec": "BHupl5EAAAAJ"}
ENTRY = r'\n  "%s":\{gs:"[^"]+",h:\d+,i10:\d+,c:\d+,b:\[[\d,]+\]\},'
def line(name, gid, r):
    return '\n  "%s":{gs:"%s",h:%d,i10:%d,c:%d,b:[%s]},' % (name, gid, r["h"], r["i10"], r["c"], ",".join(map(str, r["b"])))
def ok(gid): return gid in R and "error" not in R[gid]

P = "data.js"
d = open(P, encoding="utf-8").read()
removed, added = [], []
for n in list(REMOVE) + list(PENDING):
    d, k = re.subn(ENTRY % re.escape(n), "", d)
    if k: removed.append(n)
for n, gid in REPLACE.items():
    d, k = re.subn(ENTRY % re.escape(n), "", d)          # the wrong person's figures go in every case
    if k: removed.append(n)
    if ok(gid): NEW[n] = gid                             # back in only with the right profile's figures
a = d.index("\ngs: {"); b = d.index("\n}", a)
blk = d[a:b]
pat = re.compile(r'\n  "((?:[^"\\]|\\.)*)":\{gs:"([^"]+)",h:(\d+),i10:(\d+),c:(\d+),b:\[([\d,]+)\]\},')
changed, kept, rows, out = 0, 0, [], blk
for m in pat.finditer(blk):
    name, gid = m.group(1), m.group(2)
    if not ok(gid): kept += 1; continue
    new = line(name, gid, R[gid])
    if new != m.group(0): out = out.replace(m.group(0), new, 1); changed += 1
    rows.append((name, {"h": int(m.group(3)), "c": int(m.group(5))}, R[gid]))
for n, gid in NEW.items():
    if f'\n  "{n}":' in out or not ok(gid): continue
    out += line(n, gid, R[gid]); added.append(n)
print(f"updated {changed}, still April figures {kept}, removed {removed}, added {added}")
drops = [(n, o["c"], r["c"]) for n, o, r in rows if r["c"] < o["c"]]
print("citations went down (check):", drops)
if APPLY:
    d = d[:a] + out + d[b:]
    open(P, "w", encoding="utf-8", newline="").write(d)
    print("data.js written")
