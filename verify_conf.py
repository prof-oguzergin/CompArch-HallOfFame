"""Verify conference attribution for each Top Picks paper by querying DBLP
and comparing the actual venue with what's in data.js."""
import urllib.request, urllib.parse, json, re, time, sys, os
sys.stdout.reconfigure(encoding='utf-8')

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

papers = []
pat = re.compile(r'\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)"')
for m in pat.finditer(section):
    papers.append({
        'year': int(m.group(1)),
        'type': m.group(2),
        'conf': m.group(3),
        'title': m.group(4).replace('\\"','"').replace("\\'","'")
    })

print(f'Loaded {len(papers)} papers', file=sys.stderr)

cache_file = 'conf_verify_cache.json'
cache = {}
if os.path.exists(cache_file):
    with open(cache_file,'r',encoding='utf-8') as f:
        cache = json.load(f)

# Query DBLP for each paper
for i, p in enumerate(papers):
    key = f"{p['conf']}::{p['title'][:80]}"
    if key in cache:
        continue

    q = urllib.parse.quote(f'{p["title"]} {" ".join(p.get("authors",[])[:2])}')
    url = f'https://dblp.org/search/publ/api?q={q}&format=json&h=3'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        hits = data.get('result',{}).get('hits',{}).get('hit',[])
        if hits:
            info = hits[0].get('info',{})
            cache[key] = {
                'dblp_key': info.get('key',''),
                'dblp_venue': info.get('venue',''),
                'dblp_title': info.get('title',''),
                'dblp_year': info.get('year','')
            }
        else:
            cache[key] = {'dblp_key': None}
    except Exception as e:
        print(f'  [{i+1}] err {e}', file=sys.stderr)
        cache[key] = {'error': str(e)}

    if (i+1) % 20 == 0:
        with open(cache_file,'w',encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
        print(f'  [{i+1}/{len(papers)}]', file=sys.stderr)
    time.sleep(2)

with open(cache_file,'w',encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

# Now compare
print('\n\n=== CONFERENCE MISMATCHES ===')
def extract_venue(conf):
    return re.match(r'([A-Z]+)', conf).group(1) if re.match(r'([A-Z]+)', conf) else conf

mismatches = []
for p in papers:
    key = f"{p['conf']}::{p['title'][:80]}"
    c = cache.get(key, {})
    dblp_key = c.get('dblp_key')
    if not dblp_key:
        continue
    # Extract venue from dblp_key like conf/hpca/MutluSWP03
    m = re.search(r'conf/(\w+)/', dblp_key)
    if not m:
        continue
    dblp_venue_short = m.group(1).upper()
    # Map some variants
    if dblp_venue_short == 'HPCASIA': dblp_venue_short = 'HPCAsia'
    our_venue = extract_venue(p['conf'])
    if our_venue.lower() != dblp_venue_short.lower():
        # Skip if DBLP venue is unknown/weird
        mismatches.append((p, dblp_venue_short, c.get('dblp_title','')))

for p, dblp_v, dblp_t in mismatches:
    print(f'\nOur: {p["conf"]} - {p["title"][:70]}')
    print(f'  -> DBLP: {dblp_v} - {dblp_t[:70]}')

print(f'\n\nTotal: {len(mismatches)} mismatches out of {len(papers)}')
