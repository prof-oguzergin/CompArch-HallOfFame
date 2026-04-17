"""
Re-fetch citations for each Top Picks paper using the DBLP key of the
CONFERENCE paper (not the IEEE Micro journal version).

Process:
1. Load each paper from data.js
2. Look up matching conference DBLP key from conf_verify_v2_cache.json
   (which was populated by searching author+year in DBLP)
3. Query Semantic Scholar by DBLP external ID: DBLP:conf/xxx/yyy
4. Get true conference paper citation count
5. Also capture the real conference title
6. Save to a new cache for merging

This fixes the issue where Kilo-NOC showed 13 cites (journal) instead of 169 (ISCA).
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

print(f'Loaded {len(papers)} papers, {len(v2_cache)} cached v2 entries', file=sys.stderr)

# Match v2 cache entries to papers
def find_dblp_match(paper, v2_entries):
    """Given a paper, find the best matching DBLP conference paper from v2 cache."""
    first_a = paper['authors'][0] if paper['authors'] else ''
    v2_key = f"{first_a}::{paper['year']}::{paper['title'][:60]}"
    entry = v2_entries.get(v2_key, {})
    venues = entry.get('venues', [])
    if not venues:
        return None

    # Find the best venue match
    our_venue = re.match(r'([A-Z]+)', paper['conf']).group(1).upper()
    # Prefer exact venue match
    for venue, dblp_title, dblp_key in venues:
        if venue == our_venue:
            return {'dblp_key': dblp_key, 'venue': venue, 'title': dblp_title, 'reason': 'venue-match'}

    # Fallback: best title similarity among arch venues
    arch_venues = {'HPCA','MICRO','ISCA','ASPLOS'}
    best_score = 0
    best = None
    for venue, dblp_title, dblp_key in venues:
        if venue not in arch_venues:
            continue
        score = difflib.SequenceMatcher(None, paper['title'].lower(), dblp_title.lower()).ratio()
        if score > best_score:
            best_score = score
            best = {'dblp_key': dblp_key, 'venue': venue, 'title': dblp_title, 'reason': f'title-match-{score:.2f}'}
    return best if best_score > 0.3 else None

# Build list of papers needing fetch
to_fetch = []
no_dblp = []
for p in papers:
    match = find_dblp_match(p, v2_cache)
    if match:
        to_fetch.append((p, match))
    else:
        no_dblp.append(p)

print(f'Have DBLP match for: {len(to_fetch)}, no match: {len(no_dblp)}', file=sys.stderr)

# Fetch from Semantic Scholar by DBLP external ID
cache_file = 'cites_v2_cache.json'
cache = {}
if os.path.exists(cache_file):
    with open(cache_file,'r',encoding='utf-8') as f:
        cache = json.load(f)

for i, (p, match) in enumerate(to_fetch):
    key = f"{p['conf']}::{p['title'][:80]}"
    if key in cache and cache[key].get('citations') is not None:
        continue

    dblp_key = match['dblp_key']
    url = f'https://api.semanticscholar.org/graph/v1/paper/DBLP:{dblp_key}?fields=title,year,citationCount,venue,externalIds'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0'})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            cache[key] = {
                'dblp_key': dblp_key,
                'conf_venue': match['venue'],
                'conf_title': match['title'],
                'citations': data.get('citationCount'),
                'ss_title': data.get('title'),
                'ss_venue': data.get('venue')
            }
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[key] = {'dblp_key': dblp_key, 'conf_venue': match['venue'], 'citations': None, 'error': '404'}
                break
            elif e.code == 429:
                wait = 20*(attempt+1)
                print(f'  [{i+1}] 429 wait {wait}s', file=sys.stderr)
                time.sleep(wait)
            else:
                print(f'  [{i+1}] HTTP {e.code}', file=sys.stderr)
                break
        except Exception as e:
            print(f'  [{i+1}] ERR {e}', file=sys.stderr)
            break

    if (i+1) % 20 == 0:
        with open(cache_file,'w',encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        matched = sum(1 for v in cache.values() if v.get('citations') is not None)
        print(f'  [{i+1}/{len(to_fetch)}] {matched} matched', file=sys.stderr)
    time.sleep(2.5)

with open(cache_file,'w',encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

# Report biggest differences vs old cache
with open('citations_cache.json','r',encoding='utf-8') as f:
    old_cache = json.load(f)

print('\n=== BIGGEST CITATION INCREASES (conf version vs journal) ===')
diffs = []
for key, v in cache.items():
    new_cites = v.get('citations')
    if new_cites is None:
        continue
    old_v = old_cache.get(key, {})
    old_cites = old_v.get('citations', 0) or 0
    if new_cites > old_cites:
        diffs.append((new_cites - old_cites, old_cites, new_cites, key))

diffs.sort(reverse=True)
for d, o, n, k in diffs[:30]:
    print(f'  +{d:>5} cites: {o:>5} -> {n:>5}  |  {k[:80]}')

matched = sum(1 for v in cache.values() if v.get('citations') is not None)
print(f'\n{matched}/{len(to_fetch)} papers got conf citations')
print(f'{len(no_dblp)} papers have no DBLP conf match - need manual')
