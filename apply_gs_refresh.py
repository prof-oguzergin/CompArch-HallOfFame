# -*- coding: utf-8 -*-
"""Write the refreshed Google Scholar metrics (refresh_gs.py -> gs_refresh_20261006.json) into data.js gs.

Every entry keeps its Scholar ID; h, i10, c and b are replaced when the profile was read without error.
Two researchers who had no Scholar data get their verified profiles (6 Oct 2026, profile name,
affiliation and top papers checked): Minesh Patel (Rutgers) om-NSbgAAAAJ, André Seznec (INRIA/IRISA)
BHupl5EAAAAJ. Not found or not usable: Gurindar S. Sohi, David H. Albonesi, Michel Dubois (the profiles
the search returned belong to other people), Luiz André Barroso (profile removed, 404), Edward S.
Davidson, Bob Ramakrishna Rau, Andrew R. Pleszkun, Michael Schlansker (no profile).
Run with --apply to write; otherwise prints the changes."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
APPLY = "--apply" in sys.argv
R = json.load(open("gs_refresh_20261006.json", encoding="utf-8"))
NEW = {"Minesh Patel": "om-NSbgAAAAJ", "André Seznec": "BHupl5EAAAAJ"}
# wrong profiles on the site since April (verify_gs.py): the ID belonged to someone else
REMOVE = {"G. Jack Lipovski": "o0yYm6kAAAAJ is Jack Kramer; no Scholar profile of his own found",
          "Christos A. Papachristou": "jmMI3eUAAAAJ is Christos Papachristos (robotics); no profile of his own found"}
REPLACE = {"Amir Roth": "X-HEAfgAAAAJ"}   # kLUQrrYAAAAJ is Aaron Roth (Penn, privacy); X-HEAfgAAAAJ is Amir Roth (now US DOE), checked
P = "data.js"
d = open(P, encoding="utf-8").read()
if "--only-fixes" in sys.argv:
    # Scholar blocked the refresh (HTTP 429): take only the wrong profiles off now; Amir Roth's own profile
    # (X-HEAfgAAAAJ) goes in with the full refresh, until then he shows no Scholar figures
    for n in list(REMOVE) + list(REPLACE):
        d, k = re.subn(r'\n  "%s":\{gs:"[^"]+",h:\d+,i10:\d+,c:\d+,b:\[[\d,]+\]\},' % re.escape(n), "", d)
        assert k == 1, n
    open(P, "w", encoding="utf-8", newline="").write(d)
    print("removed:", list(REMOVE) + list(REPLACE)); sys.exit()
for n, gid in REPLACE.items():      # entry taken off by --only-fixes -> comes back as a new one
    d, k = re.subn(r'(\n  "%s":\{gs:")[^"]+(")' % re.escape(n), lambda m: m.group(1) + gid + m.group(2), d)
    if k == 0: NEW[n] = gid
for n in REMOVE:                    # already gone after --only-fixes
    d, k = re.subn(r'\n  "%s":\{gs:"[^"]+",h:\d+,i10:\d+,c:\d+,b:\[[\d,]+\]\},' % re.escape(n), "", d)
a = d.index("\ngs: {"); b = d.index("\n}", a)
blk = d[a:b]
pat = re.compile(r'^(  "((?:[^"\\]|\\.)*)":\{gs:"([^"]+)",h:(\d+),i10:(\d+),c:(\d+),b:\[([\d,]+)\]\})', re.M)
changed, kept, out = 0, [], blk
rows = []
for m in pat.finditer(blk):
    line, name, gid = m.group(1), m.group(2), m.group(3)
    old = {"h": int(m.group(4)), "i10": int(m.group(5)), "c": int(m.group(6)), "b": [int(x) for x in m.group(7).split(",")]}
    r = R.get(gid)
    if not r or "error" in r:
        kept.append((name, gid, (r or {}).get("error", "not fetched"))); continue
    new_line = '  "%s":{gs:"%s",h:%d,i10:%d,c:%d,b:[%s]}' % (name, gid, r["h"], r["i10"], r["c"], ",".join(map(str, r["b"])))
    if new_line != line:
        out = out.replace(line, new_line, 1); changed += 1
    rows.append((name, old, r))
for name, gid in NEW.items():
    r = R.get(gid)
    if f'\n  "{name}":' in out: continue
    if not r or "error" in r:
        kept.append((name, gid, "new profile not fetched")); continue
    out += '\n  "%s":{gs:"%s",h:%d,i10:%d,c:%d,b:[%s]},' % (name, gid, r["h"], r["i10"], r["c"], ",".join(map(str, r["b"])))
    changed += 1
    rows.append((name, None, r))
print(f"entries changed: {changed}; kept as they were: {len(kept)}")
for k in kept: print("   kept:", k)
drops = [(n, o["c"], r["c"]) for n, o, r in rows if o and r["c"] < o["c"]]
print("citations went down (check the profile):", drops)
big = sorted((r["h"] - o["h"], n, o["h"], r["h"]) for n, o, r in rows if o)[-8:]
print("largest h-index rises:", [(n, f"{x}->{y}") for _, n, x, y in reversed(big)])
if APPLY:
    d = d[:a] + out + d[b:]
    open(P, "w", encoding="utf-8", newline="").write(d)
    print("data.js written")
