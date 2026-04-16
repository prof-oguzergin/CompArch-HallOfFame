"""
Fetch Semantic Scholar citation counts for Top Picks + HM papers.
Uses bulk match endpoint. 2s delay between requests to avoid rate limits.
"""
import urllib.request, urllib.parse, json, re, time, sys, os

# Parse toppicks_papers from data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the toppicks_papers array
start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

# Parse each paper with regex
papers = []
pattern = r'\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)",authors:\[((?:"[^"]*"(?:,"[^"]*")*)?)\]\}'
for m in re.finditer(pattern, section):
    year = int(m.group(1))
    ptype = m.group(2)
    conf = m.group(3)
    title = m.group(4).replace('\\"', '"').replace("\\'", "'")
    papers.append({'year': year, 'type': ptype, 'conf': conf, 'title': title})

print(f'Loaded {len(papers)} papers', file=sys.stderr)

# Load existing citations if any (for resume)
cache_file = 'citations_cache.json'
cache = {}
if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    print(f'Loaded {len(cache)} cached citations', file=sys.stderr)

# Fetch citations
DELAY = 2.5  # seconds between requests
errors = 0
for i, p in enumerate(papers):
    key = f"{p['conf']}::{p['title'][:80]}"
    if key in cache:
        continue

    q = urllib.parse.quote(p['title'])
    url = f'https://api.semanticscholar.org/graph/v1/paper/search/match?query={q}&fields=title,year,citationCount,externalIds'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)'})

    retries = 0
    while retries < 4:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            hits = data.get('data', [])
            if hits:
                h = hits[0]
                cache[key] = {
                    'citations': h.get('citationCount'),
                    'year': h.get('year'),
                    'ext': h.get('externalIds', {}),
                    'matched_title': h.get('title'),
                    'score': h.get('matchScore')
                }
            else:
                cache[key] = {'citations': None, 'matched_title': None}
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[key] = {'citations': None, 'matched_title': None, 'error': '404'}
                break
            elif e.code == 429:
                retries += 1
                wait = 15 * retries
                print(f'  [{i+1}/{len(papers)}] 429 rate limit, waiting {wait}s...', file=sys.stderr)
                time.sleep(wait)
            else:
                print(f'  [{i+1}/{len(papers)}] HTTP {e.code}: {p["title"][:60]}', file=sys.stderr)
                errors += 1
                break
        except Exception as e:
            print(f'  [{i+1}/{len(papers)}] Error: {e}', file=sys.stderr)
            errors += 1
            break

    # Save cache every 20 papers
    if (i+1) % 20 == 0:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        matched = sum(1 for v in cache.values() if v.get('citations') is not None)
        print(f'  [{i+1}/{len(papers)}] {matched} matched', file=sys.stderr)

    time.sleep(DELAY)

# Final save
with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

matched = sum(1 for v in cache.values() if v.get('citations') is not None)
print(f'\n=== DONE ===', file=sys.stderr)
print(f'Total: {len(papers)}, Matched: {matched}, Errors: {errors}', file=sys.stderr)
