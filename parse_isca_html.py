# -*- coding: utf-8 -*-
"""Parse the FULL ISCA 2026 program from raw HTML (authoritative, vs truncated WebFetch).
Outputs author -> 2026 paper count, with affiliations."""
import re, html, json, unicodedata

HTML = r"isca_prog_raw.html"
raw = open(HTML, encoding='utf-8').read()

# Each paper: <div class="paper-title"> TITLE </div> ... <div class="paper-authors"> AUTHORS </div>
# Grab paper-authors blocks (the authoritative author lists)
author_blocks = re.findall(r'<div class="paper-authors">(.*?)</div>', raw, re.DOTALL)

def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)        # strip tags
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
def norm(s):
    s = strip_accents(s).lower().strip()
    s = re.sub(r'[.\-]', ' ', s); s = re.sub(r'\s+', ' ', s)
    return s

papers = []          # list of list of (name, aff)
author_count = {}     # norm -> count
disp = {}             # norm -> display name
for blk in author_blocks:
    txt = clean(blk)
    if not txt: continue
    # authors look like: Name (Affiliation), Name (Affiliation), ...
    authors = re.findall(r'([^,(][^(]*?)\s*\(([^)]*)\)', txt)
    plist = []
    seen = set()
    for nm, aff in authors:
        nm = nm.strip().strip(',').strip()
        if len(nm.split()) < 2: continue
        k = norm(nm)
        disp.setdefault(k, nm)
        plist.append((nm, aff.strip()))
        if k not in seen:
            author_count[k] = author_count.get(k, 0) + 1
            seen.add(k)
    if plist: papers.append(plist)

print(f"Parsed papers (with author blocks): {len(papers)}")
print(f"Unique authors: {len(author_count)}")

# Nika specifically
for k,c in author_count.items():
    if 'mansouri' in k or 'ghiasi' in k:
        print(f"  NIKA: {disp[k]} -> {c} paper(s) in ISCA 2026")

# dump full map for downstream use
json.dump({disp[k]: author_count[k] for k in author_count},
          open(r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/isca2026_full_authors.json",'w',encoding='utf-8'),
          ensure_ascii=False, indent=0)
print("Wrote isca2026_full_authors.json")
