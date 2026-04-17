"""Integrate GS cache into data.js as DATA.gs object."""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('gs_cache.json','r',encoding='utf-8') as f:
    cache = json.load(f)

with open('data.js','r',encoding='utf-8') as f:
    content = f.read()

# Build compact gs object
# Format: "Name": {gs:"id",h:N,i10:N,c:TOTAL,b:[100+,200+,400+,800+,1000+]}
gs_entries = []
for name, v in cache.items():
    if not v.get('metrics'):
        continue
    m = v['metrics']
    b = v.get('buckets', {})
    gs_id = v.get('gs_id', '')
    gs_entries.append((name, {
        'gs': gs_id,
        'h': m['h'],
        'i10': m['i10'],
        'c': m['cites'],
        'b': [b.get('100',0), b.get('200',0), b.get('400',0), b.get('800',0), b.get('1000',0)]
    }))

# Sort alphabetically by name for readability
gs_entries.sort(key=lambda x: x[0].lower())

# Build JS object
lines = ['gs: {']
for name, v in gs_entries:
    name_esc = name.replace('"','\\"')
    lines.append(f'  "{name_esc}":{{gs:"{v["gs"]}",h:{v["h"]},i10:{v["i10"]},c:{v["c"]},b:[{",".join(str(x) for x in v["b"])}]}},')
lines.append('}')
gs_js = '\n'.join(lines)

# Insert before closing };  — after acceptance:{...}
# Find end of acceptance object
m = re.search(r'acceptance:\s*\{.*?\n\}', content, re.DOTALL)
if not m:
    print('ERROR: acceptance object not found')
    sys.exit(1)

insert_pos = m.end()
# Insert gs object after acceptance, with leading comma
new_content = content[:insert_pos] + ',\n' + gs_js + content[insert_pos:]

with open('data.js','w',encoding='utf-8') as f:
    f.write(new_content)

print(f'Integrated {len(gs_entries)} GS entries into data.js')
