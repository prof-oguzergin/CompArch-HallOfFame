"""Merge citation counts from citations_cache.json into data.js toppicks_papers."""
import json, re

with open('citations_cache.json','r',encoding='utf-8') as f:
    cache = json.load(f)

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()

def get_cite(conf, title):
    key = f'{conf}::{title[:80]}'
    v = cache.get(key)
    if not v:
        return None
    return v.get('citations')

# Find toppicks_papers section
start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

# Pattern to match each paper object
pattern = re.compile(
    r'(\{year:(\d+),type:"(TP|HM)",conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)",authors:\[(?:"[^"]*"(?:,"[^"]*")*)?\]\})'
)

updated = 0
no_match = 0

def replace_fn(m):
    global updated, no_match
    full = m.group(1)
    conf = m.group(4)
    title = m.group(5).replace('\\"','"').replace("\\'","'")
    cites = get_cite(conf, title)
    if cites is None:
        no_match += 1
        return full[:-1] + ',cites:null}'
    updated += 1
    return full[:-1] + f',cites:{cites}}}'

new_section = pattern.sub(replace_fn, section)
new_content = content[:start] + new_section + content[end+3:]

with open('data.js','w',encoding='utf-8') as f:
    f.write(new_content)

print(f'Updated {updated} papers with citations, {no_match} no match')
