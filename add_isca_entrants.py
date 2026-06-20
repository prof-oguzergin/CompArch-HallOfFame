# -*- coding: utf-8 -*-
"""Add 11 verified new ISCA HoF members; clean their stale crossvenue isca; add missing affiliation."""
import re

DATA = r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/data.js"

# name -> (total, year-dict-string incl 2026)
NEW = [
    ("Mingyu Gao",            10, "{2016:1,2021:1,2022:1,2024:2,2025:2,2026:3}"),
    ("Jovan Stojkovic",       10, "{2023:2,2024:2,2025:1,2026:5}"),
    ("Ang Li",                 9, "{2022:1,2023:1,2024:1,2025:2,2026:4}"),
    ("Jingwen Leng",           9, "{2013:1,2021:1,2023:2,2024:2,2025:1,2026:2}"),
    ("Hai Jin",                9, "{2019:1,2021:1,2022:1,2023:2,2024:1,2025:1,2026:2}"),
    ("Haibo Chen",             8, "{2008:1,2015:1,2019:1,2021:1,2023:1,2024:1,2025:1,2026:1}"),
    ("Yun Liang",              8, "{2015:1,2021:2,2022:1,2025:2,2026:2}"),
    ("Benjamin C. Lee",        8, "{2009:1,2010:3,2012:1,2016:1,2025:1,2026:1}"),
    ("Yiran Chen",             8, "{2020:1,2022:1,2024:1,2025:4,2026:1}"),
    ("Xiaoyao Liang",          8, "{2008:1,2010:1,2013:1,2015:1,2016:1,2020:1,2024:1,2026:1}"),
    ("Alper Buyuktosunoglu",   8, "{2003:1,2008:1,2010:1,2020:1,2021:1,2022:1,2024:1,2026:1}"),
]

src = open(DATA, encoding='utf-8').read()

# --- 1. sanity: verify each year-dict sums to total ---
for name, tot, y in NEW:
    s = sum(int(v) for v in re.findall(r':(\d+)', y))
    assert s == tot, f"{name}: dict sums {s} != {tot}"

# --- 2. insert into isca array (before its closing ]) ---
i_start = src.index('\nisca: [')
i_end   = src.index('\nasplos: [')
seg = src[i_start:i_end]
close = seg.rindex(']')
entries = "".join(f'  {{name:"{n}",total:{t},y:{y}}},\n' for n,t,y in NEW)
seg = seg[:close] + entries + seg[close:]
src = src[:i_start] + seg + src[i_end:]

# --- 3. strip stale isca:N from crossvenue for these names ---
cv_s = src.index('crossvenue: {'); cv_e = src.index('toppicks_papers:')
cvseg = src[cv_s:cv_e]
for name,_,_ in NEW:
    m = re.search(r'("'+re.escape(name)+r'":\s*\{)([^}]*)(\})', cvseg)
    if not m: continue
    body = m.group(2)
    body2 = re.sub(r'isca:\d+,?', '', body).strip().strip(',')
    body2 = re.sub(r',\s*,', ',', body2)
    cvseg = cvseg[:m.start()] + m.group(1) + body2 + m.group(3) + cvseg[m.end():]
src = src[:cv_s] + cvseg + src[cv_e:]

# --- 4. add missing affiliation (Jovan Stojkovic) ---
if '"Jovan Stojkovic":' not in src:
    asrc = src.index('affiliations:')
    brace = src.index('{', asrc)
    src = src[:brace+1] + '\n  "Jovan Stojkovic": {inst:"UT Austin",pid:"252/3245"},' + src[brace+1:]

open(DATA,'w',encoding='utf-8',newline='').write(src)
print(f"Added {len(NEW)} ISCA HoF members, cleaned crossvenue, added Jovan Stojkovic affiliation.")
print("New ISCA totals:", ", ".join(f"{n}={t}" for n,t,_ in NEW))
