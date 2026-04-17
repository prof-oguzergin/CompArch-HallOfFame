import re, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js','r',encoding='utf-8') as f:
    content = f.read()

start = content.find('toppicks_papers: [')
end = content.find('\n],', start)
section = content[start:end+3]

authors_tp = {}
authors_hm = {}
pat = re.compile(r'type:"(TP|HM)"[^{}]*authors:\[((?:"[^"]*"(?:,"[^"]*")*)?)\]')
for m in pat.finditer(section):
    ptype = m.group(1)
    auth = re.findall(r'"([^"]*)"', m.group(2))
    d = authors_tp if ptype == 'TP' else authors_hm
    for a in auth:
        d[a] = d.get(a, 0) + 1

names = ['Jovan Stojkovic', 'Chunao Liu', 'Muhammad Shahbaz', 'Josep Torrellas',
         'Pouya Dormiani', 'Saiful A. Mojumder', 'Joseph Zuckerman', 'Luca P. Carloni', 'Martha A. Kim']

print(f"{'Author':<28} {'TP':>4} {'HM':>4} {'Total':>6}")
print('-'*50)
for n in names:
    tp = authors_tp.get(n, 0)
    hm = authors_hm.get(n, 0)
    print(f'{n:<28} {tp:>4} {hm:>4} {tp+hm:>6}')
