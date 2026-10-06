# -*- coding: utf-8 -*-
"""ISCA / MICRO / HPCA re-check of 6 Oct 2026 (venue_split_check.py on fresh dblp pulls, plus the ISCA 2025-26
and HPCA 2025-26 programs and a review of every reduction the 30 Sep run made).

Papers dblp files under another person of the same name, each confirmed outside dblp:
- Rajiv Gupta, MICRO 1993 "Predictability of load/store instruction latencies" (with HP Labs): dblp puts it
  under 181/2697, a radiologist's profile; the ACM DL author profile on the paper is UC Riverside's Rajiv
  Gupta. The 30 Sep run had dropped it (15 -> 14); restored to 15.
- Michael C. Huang, ISCA 2025 "DS-TPU": dblp 87/6759; program "Michael Huang (Rochester)", five co-authors
  shared with him. 9 -> 10.
- Guangyu Sun, HPCA 2026 "Towards Compute-Aware In-Switch Computing ...": was under the undisambiguated
  29/6473 on 30 Sep, dblp has since moved it to his PID; program: Peking University. 12 -> 13.
- Jie Zhang (PKU), HPCA 2026 "TENET-v2": dblp 84/6889-177 (only this paper); the HPCA 2026 site links it to
  the same researchr profile (CHASE Lab, PKU, PC member) as his AutoGNN. 11 -> 12.
- Ang Li (PNNL), HPCA 2026 "Fully Parallelized BP Decoding for Quantum LDPC Codes ...": dblp 33/2805;
  program: Pacific Northwest National Laboratory. Crossvenue HPCA 4 -> 5.
Recorded in apply_dblp_verified.py EXTRA_PUBL (read by recompute_crossvenue.py too)."""
import re
P = "data.js"
d = open(P, encoding="utf-8").read()
def block(head):
    a = d.index("\n" + head); b = d.index("\n]", a); return a, b
def edit_member(venue, name, f):
    global d
    a, b = block(venue + ": [")
    blk = d[a:b]
    m = re.search(r'\{name:"' + re.escape(name) + r'",total:(\d+),y:\{([^}]*)\}\}', blk)
    assert m, (venue, name)
    total = int(m.group(1)); y = {int(k): int(v) for k, v in re.findall(r"(\d+):(\d+)", m.group(2))}
    total, y = f(total, y)
    assert total == sum(y.values()), (venue, name, total, y)
    new = '{name:"%s",total:%d,y:{%s}}' % (name, total, ",".join(f"{k}:{v}" for k, v in sorted(y.items())))
    d = d[:a] + blk[:m.start()] + new + blk[m.end():] + d[b:]
def add(year):
    def f(t, y):
        y = dict(y); y[year] = y.get(year, 0) + 1; return t + 1, y
    return f
edit_member("micro", "Rajiv Gupta", add(1993))
edit_member("isca", "Michael C. Huang", add(2025))
edit_member("hpca", "Guangyu Sun", add(2026))
edit_member("hpca", "Jie Zhang", add(2026))
# crossvenue Ang Li: hpca 4 -> 5
old = '"Ang Li": {hpca:4,asplos:7}'
assert d.count(old) == 1, d.count(old)
d = d.replace(old, '"Ang Li": {hpca:5,asplos:7}')
# changelog
anchor = 'updates: [\n'
assert d.count(anchor) == 1
d = d.replace(anchor, anchor + '  {date:"6 Oct 2026",text:"ISCA, MICRO and HPCA counts re-checked the same way: fresh DBLP pulls, a search for papers DBLP files under another person of the same name, and the ISCA and HPCA 2025-26 programs. Five papers were credited: Rajiv Gupta (MICRO 1993, back to 15; the 30 Sep check had dropped it), Michael C. Huang (ISCA 2025, now 10), Guangyu Sun (HPCA 2026, now 13), Jie Zhang (HPCA 2026, now 12) and Ang Li (HPCA 2026)."},\n', 1)
open(P, "w", encoding="utf-8", newline="").write(d)
print("data.js patched")
