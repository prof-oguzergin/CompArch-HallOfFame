"""Retry GS fetch for missing/broken entries with improved regex."""
import urllib.request, urllib.parse, re, time, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def find_gs_id(name, aff):
    q = urllib.parse.quote(f'{name} {aff} google scholar')
    html = fetch(f'https://duckduckgo.com/html/?q={q}')
    # Strict: require exactly 12-char alphanumeric (GS ID format)
    ids = re.findall(r'user%3D([A-Za-z0-9_-]{12})(?:[^A-Za-z0-9_-]|$)', html)
    if not ids:
        ids = re.findall(r'user=([A-Za-z0-9_-]{12})(?:[^A-Za-z0-9_-]|$)', html)
    return ids[0] if ids else None

def fetch_metrics(gs_id):
    html = fetch(f'https://scholar.google.com/citations?user={gs_id}&hl=en')
    m = re.search(r'Citations.*?<td[^>]*>(\d+)</td>.*?h-index.*?<td[^>]*>(\d+)</td>.*?i10.*?<td[^>]*>(\d+)</td>', html, re.DOTALL)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def count_buckets(gs_id, thresholds=(100, 200, 400, 800, 1000)):
    counts = {t: 0 for t in thresholds}
    min_t = min(thresholds)
    cstart = 0
    while True:
        url = f'https://scholar.google.com/citations?user={gs_id}&hl=en&cstart={cstart}&pagesize=100&view_op=list_works&sortby=cited_by'
        html = fetch(url)
        cites = [int(x) for x in re.findall(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)</a>', html)]
        if not cites:
            break
        for c in cites:
            for t in thresholds:
                if c >= t:
                    counts[t] += 1
        if min(cites) < min_t:
            break
        cstart += 100
        if cstart >= 1000:
            break
        time.sleep(2)
    return counts

with open('gs_cache.json','r',encoding='utf-8') as f:
    cache = json.load(f)

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
aff_section = re.search(r'affiliations:\s*\{(.*?)\n\},', content, re.DOTALL).group(1)
affs = {}
for m in re.finditer(r'"([^"]+)":\s*\{inst:"([^"]*)"', aff_section):
    affs[m.group(1)] = m.group(2)

# Find entries needing retry
retry_list = [name for name, v in cache.items() if not v.get('metrics')]
print(f'Retrying {len(retry_list)} entries', file=sys.stderr)

for i, name in enumerate(retry_list):
    aff = affs.get(name, '')
    entry = cache.get(name, {})
    # Reset broken gs_id if too short
    if entry.get('gs_id') and len(entry['gs_id']) < 12:
        entry['gs_id'] = None

    try:
        if not entry.get('gs_id'):
            gs_id = find_gs_id(name, aff)
            entry['gs_id'] = gs_id
            time.sleep(3)
        gs_id = entry.get('gs_id')
        if gs_id:
            metrics = fetch_metrics(gs_id)
            if metrics:
                entry['metrics'] = {'cites': metrics[0], 'h': metrics[1], 'i10': metrics[2]}
            time.sleep(2)
            entry['buckets'] = count_buckets(gs_id)
            entry.pop('error', None)
        cache[name] = entry
        print(f'  [{i+1}] {name}: gs_id={entry.get("gs_id")} metrics={entry.get("metrics")}', file=sys.stderr)
    except Exception as e:
        print(f'  [{i+1}] ERR {name}: {e}', file=sys.stderr)
        entry['error'] = str(e)
        cache[name] = entry

    if (i+1) % 5 == 0:
        with open('gs_cache.json','w',encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
    time.sleep(3)

with open('gs_cache.json','w',encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

ok = sum(1 for v in cache.values() if v.get('metrics'))
print(f'\nFINAL: {ok}/{len(cache)} have metrics', file=sys.stderr)
