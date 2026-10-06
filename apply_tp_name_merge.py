# -*- coding: utf-8 -*-
"""Top Picks: one spelling per person in toppicks_papers (6 Oct 2026).

The Top Picks ranking counts authors by the exact string, so "Dean Tullsen" (ASPLOS 2023) and
"Dean M. Tullsen" (ISCA 2011, 2018) showed up as two people with 1 and 2 Top Picks. 21 such pairs were
found by first + last name; 20 are the same person (checked against the papers' author lists), one is
not: "Jae Lee" of ILLIXR (IISWC 2021, a UIUC student) is not Jae W. Lee (SNU) and is left alone.
Canonical spelling: the one the Hall of Fame lists use, otherwise the fuller form."""
import re
P = "data.js"
d = open(P, encoding="utf-8").read()
MAP = {
    "Joel Emer": "Joel S. Emer", "Christopher Fletcher": "Christopher W. Fletcher", "Dean Tullsen": "Dean M. Tullsen",
    "Daniel Sánchez": "Daniel Sanchez", "Michael Chen": "Michael K. Chen", "David Patterson": "David A. Patterson",
    "David T. Blaauw": "David Blaauw", "Smruti Sarangi": "Smruti R. Sarangi", "Margaret R. Martonosi": "Margaret Martonosi",
    "Scott Mahlke": "Scott A. Mahlke", "Norman Jouppi": "Norman P. Jouppi", "William Dally": "William J. Dally",
    "Andrew Hilton": "Andrew D. Hilton", "Michael Papamichael": "Michael K. Papamichael", "Todd Millstein": "Todd D. Millstein",
    "Jason Oberg": "Jason K. Oberg", "Kim Hazelwood": "Kim M. Hazelwood", "Juan L. Aragon": "Juan Luis Aragon",
    "Yannis Tsividis": "Yannis P. Tsividis", "Sabrina Neuman": "Sabrina M. Neuman",
}
a = d.index("\ntoppicks_papers: ["); b = d.index("\n]", a)
blk = d[a:b]
n = 0
def fix_authors(m):
    global n
    names = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    new = [MAP.get(x, x) for x in names]
    n += sum(1 for x, y in zip(names, new) if x != y)
    return "authors:[" + ",".join('"' + x + '"' for x in new) + "]"
blk2 = re.sub(r"authors:\[([^\]]*)\]", fix_authors, blk)
assert n > 0
d = d[:a] + blk2 + d[b:]
for k in MAP: assert f'"{k}"' not in d[a:a + len(blk2)], k
open(P, "w", encoding="utf-8", newline="").write(d)
print("renamed", n, "author entries")
