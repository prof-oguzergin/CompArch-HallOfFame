# -*- coding: utf-8 -*-
"""MICRO 2026, second pass (micro2026_missed_check.py): one more entrant the first pass missed.

Xinyu Chen (HKUST(GZ)): dblp splits his MICRO papers over 96/3374-1 (ReGraph 2022, X-SET 2025) and the
undisambiguated 96/3374 (AxCore 2025); 2026 program: 5 papers, all "Xinyu Chen (HKUST(GZ))". Same person:
NUS PhD with Bingsheng He (ReGraph co-authors), the HKUST(GZ) students of AxCore/UniCore appear on his
2026 papers, and RidgeBridge 2026 joins both groups. 3 + 5 = 8. Other venues from the same two PIDs:
HPCA 2026 RidgeWalker (96/3374-1), ISCA 2026 UniCore (96/3374).
"""
import re
P = "data.js"
d = open(P, encoding="utf-8").read()

def block_bounds(head, close):
    a = d.index("\n" + head); b = d.index(close, a); return a, b
# MICRO entry
a, b = block_bounds("micro: [", "\n]")
blk = d[a:b].rstrip()
assert 'name:"Xinyu Chen"' not in blk
blk = blk + (",\n" if not blk.endswith(",") else "\n") + '  {name:"Xinyu Chen",total:8,y:{2022:1,2025:2,2026:5}}'
d = d[:a] + blk + d[b:]
# crossvenue, affiliation, Scholar
def insert_after(head, line):
    global d
    i = d.index("\n" + head) + len("\n" + head)
    d = d[:i] + "\n" + line + d[i:]
insert_after("crossvenue: {", '  "Xinyu Chen": {hpca:1,isca:1},')
insert_after("affiliations: {", '  "Xinyu Chen": {inst:"HKUST (GZ)",pid:"96/3374-1"},')
insert_after("gs: {", '  "Xinyu Chen":{gs:"h4kJ1UwAAAAJ",h:10,i10:10,c:596,b:[2,0,0,0,0]},')
# changelog: 22 -> 23 entrants, 148 -> 149
old = re.search(r'\{date:"5 Oct 2026",text:"MICRO 2026 added[^\n]*\n', d).group(0)
new = (old.replace("22 researchers crossed", "23 researchers crossed")
          .replace("A. Giray Yağlıkçı.", "A. Giray Yağlıkçı, Xinyu Chen.")
          .replace("MICRO Hall of Fame now 148", "MICRO Hall of Fame now 149"))
assert new != old and "Xinyu Chen" in new and "149" in new
d = d.replace(old, new)
open(P, "w", encoding="utf-8", newline="").write(d)
print("Xinyu Chen added; changelog updated")
