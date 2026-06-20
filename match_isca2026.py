# -*- coding: utf-8 -*-
"""Match ISCA 2026 program authors against current ISCA HoF members.
Temporary update from program page (not DBLP-verified)."""
import re, unicodedata, json, sys

PROG = r"C:/Users/Z GAMES/.claude/projects/C--Users-Z-GAMES-Yapay-Zeka/fb8e0839-187f-44a2-9bc6-1a606f9f3ee9/tool-results/toolu_01JGtjoHxDpqfN9BTgFcUVot.txt"
DATA = r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/data.js"

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def norm(s):
    s = strip_accents(s).lower().strip()
    s = re.sub(r'[.\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def collapse_middle(name):
    """David A. Wood -> david wood ; keep first + last token."""
    toks = norm(name).split()
    if len(toks) >= 2:
        return toks[0] + ' ' + toks[-1]
    return norm(name)

# --- 1. extract current ISCA HoF members from data.js ---
src = open(DATA, encoding='utf-8').read()
isca_block = src[src.index('\nisca: ['):src.index('\nasplos: [')]
members = re.findall(r'name:"([^"]+)"', isca_block)

# --- 2. extract author lines from program ---
lines = open(PROG, encoding='utf-8').read().splitlines()
# author lines are the "- ..." lines following a numbered title
author_lines = []
for ln in lines:
    st = ln.strip()
    if st.startswith('- ') and '(' in st:
        author_lines.append(st[2:])

# parse each author line into a set of author names (strip affiliations in parens)
def parse_authors(line):
    # remove (affiliation) groups
    no_aff = re.sub(r'\([^)]*\)', '', line)
    parts = re.split(r'[;,]', no_aff)
    names = []
    for p in parts:
        p = p.strip()
        if p and re.search(r'[A-Za-z]', p):
            names.append(p)
    return names

paper_authors = [parse_authors(l) for l in author_lines]

# build normalized author occurrence: for each paper, set of full-norm and collapsed-norm
paper_norm = []
for authors in paper_authors:
    full = set(norm(a) for a in authors)
    coll = set(collapse_middle(a) for a in authors)
    paper_norm.append((full, coll))

# --- 3. count matches ---
# common short names that risk false positives (first+last both common)
results = {}
for m in members:
    mf = norm(m)
    has_middle = len(mf.split()) >= 3   # e.g. "David A. Wood", "Nam Sung Kim"
    mc = collapse_middle(m)
    cnt = 0
    for full, coll in paper_norm:
        if mf in full:
            cnt += 1
        elif has_middle and mc in coll:   # only collapse-match multi-token HoF names
            cnt += 1
    if cnt > 0:
        results[m] = cnt

# flag risky common names (2-token, each token short/common)
COMMON = {'li','liu','wang','zhang','chen','kim','hu','sun','das','yin','wei','john','yang','zhao','xie','gao'}
def risky(name):
    toks = norm(name).split()
    return len(toks) == 2 and (toks[0] in COMMON or toks[1] in COMMON)

print(f"ISCA HoF members: {len(members)} | papers parsed: {len(paper_norm)}")
print(f"Members appearing in ISCA 2026: {len(results)}\n")
for name, cnt in sorted(results.items(), key=lambda x: -x[1]):
    flag = '  <-- COMMON NAME, verify' if risky(name) else ''
    print(f"{cnt}  {name}{flag}")

json.dump(results, open(r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/isca2026_matches.json",'w',encoding='utf-8'), indent=2, ensure_ascii=False)
