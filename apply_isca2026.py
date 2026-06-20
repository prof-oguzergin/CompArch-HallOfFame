# -*- coding: utf-8 -*-
"""Apply ISCA 2026 program counts to data.js ISCA block (TEMPORARY, program-page based)."""
import re, json

DATA = r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/data.js"
res = json.load(open(r"C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/isca2026_matches.json", encoding='utf-8'))

# manual override: Yuan Xie HKUST = 2 (3rd hit is Tsinghua, likely different person)
res["Yuan Xie"] = 2

src = open(DATA, encoding='utf-8').read()
lines = src.splitlines(keepends=True)

# find ISCA block boundaries
start = next(i for i,l in enumerate(lines) if l.startswith('isca: ['))
end   = next(i for i,l in enumerate(lines) if l.startswith('asplos: ['))

applied = {}
for i in range(start, end):
    m = re.search(r'name:"([^"]+)"', lines[i])
    if not m:
        continue
    name = m.group(1)
    if name not in res:
        continue
    cnt = res[name]
    line = lines[i]
    # bump total
    def bump(mt):
        return f'total:{int(mt.group(1))+cnt}'
    line, n1 = re.subn(r'total:(\d+)', bump, line, count=1)
    # add 2026 key before the closing brace of the y:{...} dict
    # y:{...}}  -> insert ,2026:cnt before the first '}' that closes y
    line, n2 = re.subn(r'(y:\{[^}]*)\}', lambda mt: mt.group(1)+f',2026:{cnt}'+'}', line, count=1)
    assert n1==1 and n2==1, f"failed on {name}: {line}"
    lines[i] = line
    applied[name] = cnt

open(DATA, 'w', encoding='utf-8', newline='').write(''.join(lines))
print(f"Applied ISCA 2026 to {len(applied)} members:")
for k,v in sorted(applied.items(), key=lambda x:-x[1]):
    print(f"  {v}  {k}")
print(f"\nTotal new ISCA 2026 paper-slots added: {sum(applied.values())}")
