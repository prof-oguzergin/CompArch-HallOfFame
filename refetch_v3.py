"""
V3: Use the conference TITLE from DBLP (not the journal title) to query
Semantic Scholar's match endpoint. This gets the conference paper's cites.
"""
import json, re, urllib.request, urllib.parse, time, os, sys, difflib
sys.stdout.reconfigure(encoding='utf-8')

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

papers = []
pat = re.compile(r'\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)",authors:\[((?:"[^"]*"(?:,"[^"]*")*)?)\]')
for m in pat.finditer(section):
    papers.append({
        'year': int(m.group(1)),
        'type': m.group(2),
        'conf': m.group(3),
        'title': m.group(4).replace('\\"','"').replace("\\'","'"),
        'authors': re.findall(r'"([^"]*)"', m.group(5))
    })

with open('conf_verify_v2_cache.json','r',encoding='utf-8') as f:
    v2_cache = json.load(f)

def find_dblp_match(paper, v2_entries):
    first_a = paper['authors'][0] if paper['authors'] else ''
    v2_key = f"{first_a}::{paper['year']}::{paper['title'][:60]}"
    entry = v2_entries.get(v2_key, {})
    venues = entry.get('venues', [])
    if not venues:
        return None

    our_venue = re.match(r'([A-Z]+)', paper['conf']).group(1).upper()
    arch_venues = {'HPCA','MICRO','ISCA','ASPLOS'}

    # Strategy: find best title match among ALL arch venues
    best_score = 0
    best = None
    for venue, dblp_title, dblp_key in venues:
        if venue not in arch_venues:
            continue
        # Clean titles for comparison
        s = difflib.SequenceMatcher(None,
            paper['title'].lower().replace(':',''),
            dblp_title.lower().replace(':','').rstrip('.')).ratio()
        if s > best_score:
            best_score = s
            best = {'dblp_key': dblp_key, 'venue': venue, 'title': dblp_title.rstrip('.'), 'score': s}
    # Lower threshold — even if title changed significantly, match best
    return best if best and best_score > 0.25 else None

to_fetch = []
no_match = []
for p in papers:
    m = find_dblp_match(p, v2_cache)
    if m:
        to_fetch.append((p, m))
    else:
        no_match.append(p)

print(f'Matched: {len(to_fetch)}, No match: {len(no_match)}', file=sys.stderr)

cache_file = 'cites_v3_cache.json'
cache = {}
if os.path.exists(cache_file):
    with open(cache_file,'r',encoding='utf-8') as f:
        cache = json.load(f)

for i, (p, match) in enumerate(to_fetch):
    key = f"{p['conf']}::{p['title'][:80]}"
    if key in cache and cache[key].get('citations') is not None:
        continue

    # Query SS with DBLP-provided conf title
    q = urllib.parse.quote(match['title'])
    url = f'https://api.semanticscholar.org/graph/v1/paper/search/match?query={q}&fields=title,year,citationCount,venue,externalIds'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0'})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            hits = data.get('data', [])
            if hits:
                h = hits[0]
                cache[key] = {
                    'dblp_key': match['dblp_key'],
                    'conf_venue': match['venue'],
                    'conf_title': match['title'],
                    'title_score': match['score'],
                    'citations': h.get('citationCount'),
                    'ss_title': h.get('title'),
                    'ss_year': h.get('year'),
                    'ss_venue': h.get('venue')
                }
            else:
                cache[key] = {'dblp_key': match['dblp_key'], 'conf_venue': match['venue'], 'conf_title': match['title'], 'citations': None}
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[key] = {'dblp_key': match['dblp_key'], 'conf_venue': match['venue'], 'conf_title': match['title'], 'citations': None, 'error':'404'}
                break
            elif e.code == 429:
                wait = 20*(attempt+1)
                time.sleep(wait)
            else:
                break

    if (i+1) % 20 == 0:
        with open(cache_file,'w',encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        matched = sum(1 for v in cache.values() if v.get('citations') is not None)
        print(f'  [{i+1}/{len(to_fetch)}] {matched} matched', file=sys.stderr)
    time.sleep(2.5)

with open(cache_file,'w',encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

# Compare with old
with open('citations_cache.json','r',encoding='utf-8') as f:
    old_cache = json.load(f)

print('\n=== SIGNIFICANT CITATION DIFFERENCES (old -> new, conf paper) ===')
diffs = []
for key, v in cache.items():
    new_c = v.get('citations')
    if new_c is None:
        continue
    old_c = (old_cache.get(key, {}).get('citations') or 0)
    if abs(new_c - old_c) >= 20:
        diffs.append((new_c - old_c, old_c, new_c, key, v.get('conf_venue'), v.get('conf_title','')[:60]))

diffs.sort(reverse=True, key=lambda x: abs(x[0]))
for d, o, n, k, venue, ctitle in diffs[:40]:
    print(f'  {"+" if d>0 else ""}{d:>5}: {o:>5} -> {n:>5} [{venue}]  {k[:60]}')
    if ctitle:
        print(f'         conf title: {ctitle}')

matched = sum(1 for v in cache.values() if v.get('citations') is not None)
print(f'\n\n{matched}/{len(to_fetch)} conf citations fetched')
