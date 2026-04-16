import re
with open('data.js','r',encoding='utf-8') as f:
    content = f.read()
for m in re.finditer(r'conf:"([^"]+)",title:"((?:[^"\\]|\\.)*)"[^}]*cites:null', content):
    print(f'{m.group(1)}: {m.group(2)[:80]}')
