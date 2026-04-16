"""
Re-query Semantic Scholar for each Top Picks paper, get author list,
and compare with data.js. Flag mismatches for manual review.
"""
import urllib.request, urllib.parse, json, re, time, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Parse toppicks_papers
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

papers = []
pattern = r'\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)",authors:\[((?:"[^"]*"(?:,"[^"]*")*)?)\]'
for m in re.finditer(pattern, section):
    year = int(m.group(1))
    ptype = m.group(2)
    conf = m.group(3)
    title = m.group(4).replace('\\"','"').replace("\\'","'")
    auth_str = m.group(5)
    authors = re.findall(r'"([^"]*)"', auth_str)
    papers.append({'year':year,'type':ptype,'conf':conf,'title':title,'authors':authors})

print(f'Loaded {len(papers)} papers', file=sys.stderr)

# Load author cache
cache_file = 'authors_cache.json'
cache = {}
if os.path.exists(cache_file):
    with open(cache_file,'r',encoding='utf-8') as f:
        cache = json.load(f)
    print(f'Loaded {len(cache)} cached', file=sys.stderr)

def normalize_name(n):
    """Normalize author name for comparison."""
    n = n.lower().strip()
    # Remove accents
    import unicodedata
    n = unicodedata.normalize('NFD', n)
    n = ''.join(c for c in n if unicodedata.category(c) != 'Mn')
    # Remove punctuation
    n = re.sub(r'[^\w\s]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def compare_authors(ours, theirs):
    """Returns overlap ratio 0-1 and details."""
    if not ours or not theirs:
        return 0.0
    ours_norm = set()
    for a in ours:
        tokens = normalize_name(a).split()
        if len(tokens) >= 2:
            # Use last name + first initial
            ours_norm.add((tokens[-1], tokens[0][:1]))
    theirs_norm = set()
    for a in theirs:
        tokens = normalize_name(a).split()
        if len(tokens) >= 2:
            theirs_norm.add((tokens[-1], tokens[0][:1]))
    if not ours_norm or not theirs_norm:
        return 0.0
    return len(ours_norm & theirs_norm) / max(len(ours_norm), len(theirs_norm))

# Re-query with authors
DELAY = 2.5
mismatches = []
for i, p in enumerate(papers):
    key = f"{p['conf']}::{p['title'][:80]}"
    if key not in cache:
        q = urllib.parse.quote(p['title'])
        url = f'https://api.semanticscholar.org/graph/v1/paper/search/match?query={q}&fields=title,authors.name,year'
        req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                hits = data.get('data', [])
                if hits:
                    h = hits[0]
                    cache[key] = {
                        'ss_title': h.get('title'),
                        'ss_authors': [a['name'] for a in h.get('authors',[])],
                        'year': h.get('year')
                    }
                else:
                    cache[key] = {'ss_title':None,'ss_authors':[]}
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    cache[key] = {'ss_title':None,'ss_authors':[],'error':'404'}
                    break
                elif e.code == 429:
                    wait = 15*(attempt+1)
                    print(f'  [{i+1}] 429, wait {wait}s', file=sys.stderr)
                    time.sleep(wait)
                else:
                    break
            except Exception as e:
                print(f'  [{i+1}] err {e}', file=sys.stderr)
                break
        time.sleep(DELAY)

    if (i+1) % 30 == 0:
        with open(cache_file,'w',encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        print(f'  [{i+1}/{len(papers)}] saved cache', file=sys.stderr)

with open(cache_file,'w',encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

# Now compare
print('\n\n=== AUTHOR MISMATCHES (overlap < 50%) ===')
for p in papers:
    key = f"{p['conf']}::{p['title'][:80]}"
    c = cache.get(key, {})
    ss_authors = c.get('ss_authors', [])
    if not ss_authors:
        continue
    overlap = compare_authors(p['authors'], ss_authors)
    if overlap < 0.5:
        print(f"\n{p['conf']}: {p['title'][:75]}")
        print(f"  Ours   ({len(p['authors'])}): {', '.join(p['authors'][:5])}{'...' if len(p['authors'])>5 else ''}")
        print(f"  SS     ({len(ss_authors)}): {', '.join(ss_authors[:5])}{'...' if len(ss_authors)>5 else ''}")
        print(f"  Overlap: {overlap:.0%}")
        mismatches.append(p)

print(f'\n\nTotal mismatches: {len(mismatches)}')
