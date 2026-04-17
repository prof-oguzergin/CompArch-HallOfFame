"""
Stronger verification: for each paper, search DBLP by (first author + year)
and list all their 4-venue papers that year. If our declared venue doesn't
match any of them, flag as mismatch.

This catches cases where the title in our data is the journal version
(different from conference title), e.g. Kilo-NOC.
"""
import urllib.request, urllib.parse, json, re, time, sys, os
sys.stdout.reconfigure(encoding='utf-8')

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

papers = []
pat = re.compile(r'\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)",authors:\[((?:"[^"]*"(?:,"[^"]*")*)?)\]')
for m in pat.finditer(section):
    year = int(m.group(1))
    ptype = m.group(2)
    conf = m.group(3)
    title = m.group(4).replace('\\"','"').replace("\\'","'")
    authors = re.findall(r'"([^"]*)"', m.group(5))
    papers.append({'year': year, 'type': ptype, 'conf': conf, 'title': title, 'authors': authors})

print(f'Loaded {len(papers)} papers', file=sys.stderr)

cache_file = 'conf_verify_v2_cache.json'
cache = {}
if os.path.exists(cache_file):
    with open(cache_file,'r',encoding='utf-8') as f:
        cache = json.load(f)

def get_conf_short(s):
    m = re.match(r'([A-Za-z&]+)', s)
    return m.group(1).upper().replace('&','') if m else s.upper()

# For each paper, query DBLP by author + year and find all their venue papers that year
# Top Picks are published in the calendar year BEFORE the issue year typically
# So for Top Picks 2012 issue, papers are from 2011 conferences

mismatches = []
for i, p in enumerate(papers):
    if not p['authors']:
        continue
    first_author = p['authors'][0]
    key = f"{first_author}::{p['year']}::{p['title'][:60]}"

    if key not in cache:
        # Top Picks convention: "year" field is conference year
        # Since conf like "ISCA 2011" also has year, use that
        conf_year_m = re.search(r'\d{4}$', p['conf'])
        target_year = int(conf_year_m.group(0)) if conf_year_m else p['year']

        q = f'author:{first_author}: year:{target_year}'
        url = f'https://dblp.org/search/publ/api?q={urllib.parse.quote(q)}&format=json&h=50'
        req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            hits = data.get('result',{}).get('hits',{}).get('hit',[])
            venues = []
            for h in hits:
                info = h.get('info',{})
                dblp_key = info.get('key','')
                # extract venue from conf/xxx/yyy
                m = re.search(r'conf/(\w+)/', dblp_key)
                if m:
                    venues.append((m.group(1).upper(), info.get('title',''), dblp_key))
            cache[key] = {'target_year': target_year, 'venues': venues}
        except Exception as e:
            print(f'  [{i+1}] ERR {e}', file=sys.stderr)
            cache[key] = {'error': str(e)}
        time.sleep(2)

        if (i+1) % 15 == 0:
            with open(cache_file,'w',encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=1)
            print(f'  [{i+1}/{len(papers)}]', file=sys.stderr)

    entry = cache.get(key, {})
    venues = entry.get('venues', [])
    if not venues:
        continue

    our_venue = get_conf_short(p['conf'])
    venue_list = set(v[0] for v in venues)

    # Some venue aliases
    alias = {'USS':'USENIX', 'SP':'S&P', 'CCS':'CCS', 'NDSS':'NDSS'}
    venue_list_normalized = {alias.get(v, v) for v in venue_list}

    if our_venue not in venue_list and our_venue not in venue_list_normalized:
        # Check if any ARCH venue is in their papers
        arch_venues = {'HPCA','MICRO','ISCA','ASPLOS'}
        their_arch = venue_list & arch_venues
        if their_arch:
            mismatches.append({
                'paper': p,
                'our_venue': our_venue,
                'their_arch_venues': sorted(their_arch),
                'all_venues': sorted(venue_list),
                'all_titles': [v[1][:70] for v in venues if v[0] in arch_venues]
            })

with open(cache_file,'w',encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=1)

# Report
print(f'\n\n=== SUSPECTED WRONG VENUE ({len(mismatches)}) ===')
for m in mismatches:
    p = m['paper']
    print(f"\n{p['conf']}: {p['title'][:70]}")
    print(f"  Author: {p['authors'][0]}")
    print(f"  DBLP says they published at: {', '.join(m['their_arch_venues'])} in {p['year']}")
    for t in m['all_titles']:
        print(f"    - {t}")
