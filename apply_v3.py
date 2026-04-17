"""
Apply v3 corrections to data.js.

Rules:
- High confidence (score >= 0.45): update venue + title + cites
- Same venue (any score): update title + cites
- Low confidence venue change (score < 0.45): LEAVE UNCHANGED, just list
- No match: leave unchanged
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('cites_v3_cache.json','r',encoding='utf-8') as f:
    v3 = json.load(f)

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()

start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

# Helper: escape title for JS string
def js_escape(s):
    return s.replace('\\','\\\\').replace('"','\\"')

# Pattern for matching paper entries
pat = re.compile(
    r'(\{year:(\d+),type:"(TP|HM)",conf:")([^"]+)(",title:")((?:[^"\\]|\\.)*)(",authors:\[)((?:"[^"]*"(?:,"[^"]*")*)?)(\])(?:,cites:(null|\d+))?\}'
)

updated = {'venue': 0, 'title': 0, 'cites': 0}
low_confidence_skipped = []

def replace_paper(m):
    pre, year, ptype, our_conf, mid1, our_title, mid2, authors, post1, old_cites = m.groups()
    our_title_clean = our_title.replace('\\"','"').replace("\\'","'")
    key = f'{our_conf}::{our_title_clean[:80]}'

    v3_entry = v3.get(key)
    if not v3_entry or v3_entry.get('citations') is None:
        return m.group(0)  # unchanged

    new_cites = v3_entry['citations']
    new_venue = v3_entry.get('conf_venue')
    new_title_raw = v3_entry.get('conf_title', '')
    score = v3_entry.get('title_score', 0)

    our_venue_short = re.match(r'([A-Z]+)', our_conf).group(1)
    conf_year_m = re.search(r'(\d{4})', our_conf)
    conf_year = conf_year_m.group(1) if conf_year_m else year

    venue_change = (new_venue != our_venue_short)

    # Skip low-confidence venue changes
    if venue_change and score < 0.45:
        low_confidence_skipped.append({
            'key': key,
            'score': score,
            'our': (our_conf, our_title_clean),
            'new': (new_venue, new_title_raw, new_cites)
        })
        # Still update cites and keep original venue+title
        updated['cites'] += 1
        return f'{pre}{year}{mid1}{our_conf}{mid2}{our_title}{post1}{authors}{m.group(9)},cites:{new_cites}}}'.replace(
            m.group(1), m.group(1)
        )

    # Apply venue change
    final_venue = f'{new_venue} {conf_year}' if venue_change else our_conf
    if venue_change:
        updated['venue'] += 1

    # Apply title change if significantly different (score < 0.9) and we have DBLP title
    final_title = our_title
    if new_title_raw and (score < 0.9 or venue_change):
        # Use DBLP title, but capitalize properly if it starts lowercase
        final_title_raw = new_title_raw
        # DBLP sometimes has trailing period
        final_title_raw = final_title_raw.rstrip('.')
        final_title = js_escape(final_title_raw)
        if final_title != our_title:
            updated['title'] += 1

    updated['cites'] += 1
    return f'{pre}{year},type:"{ptype}",conf:"{final_venue}",title:"{final_title}",authors:[{authors}],cites:{new_cites}}}'.replace(
        'pre', ''
    )

# Simpler re-implementation
def build_new_section():
    out = []
    last = 0
    for m in pat.finditer(section):
        out.append(section[last:m.start()])

        year = m.group(2)
        ptype = m.group(3)
        our_conf = m.group(4)
        our_title = m.group(6)  # escaped form
        our_title_clean = our_title.replace('\\"','"').replace("\\'","'")
        authors = m.group(8)
        old_cites = m.group(10)

        key = f'{our_conf}::{our_title_clean[:80]}'
        v3_entry = v3.get(key)

        if not v3_entry or v3_entry.get('citations') is None:
            # unchanged
            out.append(m.group(0))
            last = m.end()
            continue

        new_cites = v3_entry['citations']
        new_venue = v3_entry.get('conf_venue')
        new_title_raw = v3_entry.get('conf_title', '').rstrip('.')
        score = v3_entry.get('title_score', 0)

        our_venue_short = re.match(r'([A-Z]+)', our_conf).group(1)
        conf_year_m = re.search(r'(\d{4})', our_conf)
        conf_year = conf_year_m.group(1) if conf_year_m else year

        venue_change = (new_venue != our_venue_short)

        if venue_change and score < 0.45:
            low_confidence_skipped.append({
                'key': key, 'score': score,
                'our_conf': our_conf, 'our_title': our_title_clean,
                'new_venue': new_venue, 'new_title': new_title_raw, 'new_cites': new_cites
            })
            # Keep venue/title, only update cites
            final_venue = our_conf
            final_title = our_title
            updated['cites'] += 1
        else:
            final_venue = f'{new_venue} {conf_year}' if venue_change else our_conf
            if venue_change:
                updated['venue'] += 1
            # Update title when conf has real title available and score not near 1.0 (or venue changed)
            final_title = our_title
            if new_title_raw and (score < 0.9 or venue_change):
                new_escaped = js_escape(new_title_raw)
                if new_escaped != our_title:
                    final_title = new_escaped
                    updated['title'] += 1
            updated['cites'] += 1

        out.append(f'{{year:{year},type:"{ptype}",conf:"{final_venue}",title:"{final_title}",authors:[{authors}],cites:{new_cites}}}')
        last = m.end()

    out.append(section[last:])
    return ''.join(out)

new_section = build_new_section()
new_content = content[:start] + new_section + content[end+3:]

with open('data.js','w',encoding='utf-8') as f:
    f.write(new_content)

print(f'Applied: venue={updated["venue"]} title={updated["title"]} cites={updated["cites"]}')
print(f'\nLow-confidence venue changes SKIPPED ({len(low_confidence_skipped)}):')
for s in low_confidence_skipped:
    print(f'  score={s["score"]:.2f} {s["our_conf"]} -> {s["new_venue"]}')
    print(f'    Our:  {s["our_title"][:80]}')
    print(f'    DBLP: {s["new_title"][:80]}')
