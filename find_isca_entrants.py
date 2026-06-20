# -*- coding: utf-8 -*-
"""Find ISCA 2026 program authors NOT yet in HoF who may now cross the 8-paper threshold."""
import re, unicodedata, json

PROG = r"C:/Users/Z GAMES/.claude/projects/C--Users-Z-GAMES-Yapay-Zeka/fb8e0839-187f-44a2-9bc6-1a606f9f3ee9/tool-results/toolu_01JGtjoHxDpqfN9BTgFcUVot.txt"
DATA = r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/data.js"

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
def norm(s):
    s = strip_accents(s).lower().strip()
    s = re.sub(r'[.\-]', ' ', s); s = re.sub(r'\s+', ' ', s)
    return s

src = open(DATA, encoding='utf-8').read()

# HoF ISCA members (already listed)
isca_block = src[src.index('\nisca: ['):src.index('\nasplos: [')]
hof_isca = {norm(n) for n in re.findall(r'name:"([^"]+)"', isca_block)}
# also any HoF member in any venue (so we know who's "known")
all_hof = set()
for vb in ['\nhpca: [','\nmicro: [','\nisca: [','\nasplos: [']:
    blk = src[src.index(vb): src.index(vb)+ src[src.index(vb):].index('\n]')]
    for n in re.findall(r'name:"([^"]+)"', blk):
        all_hof.add(norm(n))

# crossvenue ISCA counts
cv_block = src[src.index('crossvenue: {'):src.index('toppicks_papers:')]
cv_isca = {}
for m in re.finditer(r'"([^"]+)":\s*\{([^}]*)\}', cv_block):
    name, body = m.group(1), m.group(2)
    mi = re.search(r'isca:(\d+)', body)
    if mi: cv_isca[norm(name)] = int(mi.group(1))

# --- parse program authors (preserve a display name per normalized key) ---
lines = open(PROG, encoding='utf-8').read().splitlines()
disp = {}            # norm -> original display
paper_count = {}     # norm -> # of 2026 papers
for ln in lines:
    st = ln.strip()
    if not (st.startswith('- ') and '(' in st):
        continue
    no_aff = re.sub(r'\([^)]*\)', '', st[2:])
    seen = set()
    for p in re.split(r'[;,]', no_aff):
        p = p.strip()
        if not re.search(r'[A-Za-z]', p): continue
        k = norm(p)
        if len(k.split()) < 2: continue          # skip single tokens / noise
        disp.setdefault(k, p)
        if k not in seen:                          # count each author once per paper
            paper_count[k] = paper_count.get(k, 0) + 1
            seen.add(k)

# --- classify authors NOT already in ISCA HoF ---
strong = []   # crossvenue isca + 2026 >= 8  => should enter now
dblp_check = []  # not in crossvenue isca, but 2+ papers in 2026 (possible missed senior)
for k, n2026 in paper_count.items():
    if k in hof_isca:
        continue                                   # already listed for ISCA
    cv = cv_isca.get(k)
    if cv is not None:
        total = cv + n2026
        if total >= 8:
            strong.append((disp[k], cv, n2026, total))
        elif total >= 6:
            dblp_check.append((disp[k], f"cv_isca={cv}", n2026, total, 'near-threshold'))
    else:
        if n2026 >= 2:
            dblp_check.append((disp[k], "no cv record", n2026, None, 'prolific-unknown'))

print(f"Unique program authors: {len(paper_count)} | not in ISCA HoF: {len(paper_count)-sum(1 for k in paper_count if k in hof_isca)}")
print(f"\n=== STRONG entrants (crossvenue ISCA + 2026 >= 8, no DBLP needed) ===")
for d,cv,n,t in sorted(strong, key=lambda x:-x[3]):
    print(f"  {t}  {d}  (had {cv} + {n} new)")
if not strong: print("  (none)")

print(f"\n=== NEAR-THRESHOLD / DBLP-CHECK candidates ===")
for row in sorted(dblp_check, key=lambda x: -(x[3] or 0)):
    d, info, n, t, why = row
    print(f"  {d}  [{info}, +{n} in 2026 => {t}]  {why}")
if not dblp_check: print("  (none)")
