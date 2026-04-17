import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('cites_v3_cache.json','r',encoding='utf-8') as f:
    v3 = json.load(f)

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

pat = re.compile(r'\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)"')
papers = {}
for m in pat.finditer(section):
    title = m.group(4).replace('\\"','"').replace("\\'","'")
    key = f'{m.group(3)}::{title[:80]}'
    papers[key] = (m.group(3), title, int(m.group(1)))

venue_changes = []
title_changes = []
for key, v in v3.items():
    cites = v.get('citations')
    if cites is None:
        continue
    if key not in papers:
        continue
    our_conf, our_title, year = papers[key]
    new_venue = v.get('conf_venue')
    conf_title = v.get('conf_title', '')
    our_venue_short = re.match(r'([A-Z]+)', our_conf).group(1)
    score = v.get('title_score', 0)
    if new_venue != our_venue_short:
        venue_changes.append((score, our_conf, new_venue, our_title, conf_title, year))
    # Also check if title changed significantly
    if score > 0.3 and score < 0.9 and new_venue == our_venue_short:
        title_changes.append((score, our_conf, our_title, conf_title))

venue_changes.sort()

print(f'=== VENUE CHANGES (count={len(venue_changes)}) ===')
print()
print('*** LOW CONFIDENCE (score < 0.45) - LIKELY FALSE MATCH ***')
low = [x for x in venue_changes if x[0] < 0.45]
for s, oc, nv, ot, ct, y in low:
    print(f'  score={s:.2f}  {oc} -> {nv} {y}')
    print(f'    Our:  {ot[:80]}')
    print(f'    DBLP: {ct[:80]}')
print()
print(f'*** HIGH CONFIDENCE VENUE CHANGES ({len(venue_changes) - len(low)}) ***')
for s, oc, nv, ot, ct, y in venue_changes:
    if s >= 0.45:
        print(f'  [{s:.2f}] {oc} -> {nv} {y}')
        print(f'    Our:  {ot[:75]}')
        print(f'    DBLP: {ct[:75]}')
print()
print(f'=== TITLE CHANGES (same venue, different title; {len(title_changes)}) ===')
for s, oc, ot, ct in sorted(title_changes)[:30]:
    print(f'  [{s:.2f}] {oc}')
    print(f'    Our:  {ot[:80]}')
    print(f'    DBLP: {ct[:80]}')
