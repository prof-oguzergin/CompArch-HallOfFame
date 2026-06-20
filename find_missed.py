# -*- coding: utf-8 -*-
"""Find ISCA HoF members whose ISCA 2026 paper may have been MISSED due to
name-variant mismatch (e.g. 'A. Giray Yaglikci' vs 'Abdullah Giray Yaglikci')."""
import re, unicodedata

PROG = r"C:/Users/Z GAMES/.claude/projects/C--Users-Z-GAMES-Yapay-Zeka/fb8e0839-187f-44a2-9bc6-1a606f9f3ee9/tool-results/toolu_01JGtjoHxDpqfN9BTgFcUVot.txt"
DATA = r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/data.js"

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
def norm(s):
    s = strip_accents(s).lower().strip()
    s = re.sub(r'[.\-]', ' ', s); s = re.sub(r'\s+', ' ', s)
    return s

src = open(DATA, encoding='utf-8').read()
isca_block = src[src.index('\nisca: ['):src.index('\nasplos: [')]
# member -> already has 2026?
members = {}
for m in re.finditer(r'name:"([^"]+)",total:\d+,y:\{([^}]*)\}', isca_block):
    members[m.group(1)] = ('2026:' in m.group(2))

# program authors with affiliation
lines = open(PROG, encoding='utf-8').read().splitlines()
prog_authors = {}   # norm full -> (display, affiliation-ish)
for ln in lines:
    st = ln.strip()
    if not (st.startswith('- ') and '(' in st): continue
    # split into "name (aff)" chunks, but names may share a trailing (aff)
    body = st[2:]
    # capture each name and the nearest following affiliation
    segments = re.split(r'(\([^)]*\))', body)
    cur_aff = ''
    # process right-to-left so names inherit the next affiliation
    chunks = re.findall(r'([^()]+)(\([^)]*\))?', body)
    for names_part, aff in re.findall(r'([^()]+?)(\([^)]*\))', body):
        aff_clean = aff.strip('()')
        for nm in re.split(r'[;,]', names_part):
            nm = nm.strip()
            if len(nm.split()) >= 2:
                prog_authors[norm(nm)] = (nm, aff_clean)

# build lastname index of program authors (NO first-initial — catches Bill/William nicknames)
prog_by_last = {}
for k,(disp,aff) in prog_authors.items():
    toks = k.split()
    prog_by_last.setdefault(toks[-1], []).append((disp,aff))

COMMON_LAST = {'li','kim','chen','wang','zhang','liu','gao','sun','xie','guo','yang','zhao','wu','huang','jin','das','das','he','hu','lee','ho','luo','song','tang','yin','yu','ma','das'}

print("=== ISCA HoF members WITHOUT 2026, same RARE lastname author IN program (nickname-tolerant) ===\n")
hits = 0
for name, has2026 in members.items():
    if has2026: continue
    k = norm(name); toks = k.split()
    if len(toks) < 2: continue
    last = toks[-1]
    if last in COMMON_LAST: continue          # skip common surnames (too noisy without initial)
    cand = prog_by_last.get(last)
    if not cand: continue
    hits += 1
    print(f"HoF: {name}")
    for disp,aff in cand:
        print(f"     program: {disp} ({aff})")
print(f"\nTotal rare-surname matches to review: {hits}")
