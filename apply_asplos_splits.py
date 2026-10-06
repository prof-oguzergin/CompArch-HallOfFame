# -*- coding: utf-8 -*-
"""ASPLOS re-check of 6 Oct 2026 (asplos2026_check.py, asplos_split_check.py on a fresh dblp pull).

The site matched dblp for all 271 researchers; the two errors below are dblp's own author assignments,
confirmed with the ASPLOS 2026 program (affiliations) and dblp's full records:
- Scott A. Mahlke: ASPLOS 2026 "SNIP" (program: Scott Mahlke, University of Michigan; co-author Yunjie
  Pan, his student) sits under the new dblp PID 429/0057, which holds only this paper and its arXiv copy.
  11 -> 12 (2026: 1).
- Quan Chen (SJTU): ASPLOS'25 vol.3 "Voyager" (program: Quan Chen, Shanghai Jiao Tong University; six
  co-authors shared with his other papers) sits under 40/3858-1, a remote-sensing Quan Chen (soil
  moisture, SAR; 36 papers). 12 -> 13 (2025: 2).
Affiliations updated from the ASPLOS 2026 program: Barış Kaşıkçı (UW), Christopher W. Fletcher
(UC Berkeley), G. Edward Suh (Cornell / NVIDIA), Xu Liu (Google; SpecProto with his former NC State
student Qidong Zhao, also at Google).
The same papers are recorded in apply_dblp_verified.py EXTRA_PUBL so a later full re-run keeps them."""
import re
P = "data.js"
d = open(P, encoding="utf-8").read()
def sub1(old, new):
    global d
    assert d.count(old) == 1, (d.count(old), old)
    d = d.replace(old, new)
# ASPLOS list entries (the ASPLOS block has its own "Scott A. Mahlke" line; match on the exact year map)
sub1('{name:"Scott A. Mahlke",total:11,y:{1992:1,1994:1,2010:2,2011:1,2012:1,2014:1,2015:1,2017:1,2018:1,2024:1}}',
     '{name:"Scott A. Mahlke",total:12,y:{1992:1,1994:1,2010:2,2011:1,2012:1,2014:1,2015:1,2017:1,2018:1,2024:1,2026:1}}')
sub1('{name:"Quan Chen",total:12,y:{2016:1,2017:1,2022:3,2023:2,2024:3,2025:1,2026:1}}',
     '{name:"Quan Chen",total:13,y:{2016:1,2017:1,2022:3,2023:2,2024:3,2025:2,2026:1}}')
# affiliations
sub1('"Christopher W. Fletcher": {inst:"UIUC",', '"Christopher W. Fletcher": {inst:"UC Berkeley",')
sub1('"G. Edward Suh": {inst:"Cornell / Meta",', '"G. Edward Suh": {inst:"Cornell / NVIDIA",')
sub1('"Barış Kaşıkçı": {inst:"U Michigan",', '"Barış Kaşıkçı": {inst:"UW",')
sub1('"Xu Liu": {inst:"NC State",', '"Xu Liu": {inst:"Google",')
# changelog: the unpublished 5 Oct acceptance note goes out today; new data note on top
sub1('{date:"5 Oct 2026",site:true,text:"Acceptance rates:', '{date:"6 Oct 2026",site:true,text:"Acceptance rates:')
sub1('updates: [\n', 'updates: [\n  {date:"6 Oct 2026",text:"ASPLOS counts re-checked against a fresh DBLP pull and the ASPLOS 2026 program, author by author. Two papers that DBLP files under another person of the same name were added: Scott A. Mahlke (ASPLOS 2026, now 12) and Quan Chen (ASPLOS 2025, now 13). ASPLOS papers count in the year of their proceedings: the 16 papers of ASPLOS 2025 Volume 3, presented at ASPLOS 2026, are in the 2025 column."},\n')
open(P, "w", encoding="utf-8", newline="").write(d)
print("data.js patched")
