"""Verify ASPLOS 2025 editor counts vs real papers for each editor."""
import urllib.request, urllib.parse, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')

editors = [
    ('Lieven Eeckhout', 'e/LievenEeckhout'),
    ('Martha A. Kim', 'k/MarthaAKim'),
    ('Christopher J. Rossbach', '46/991'),
    ('Adrian Sampson', '72/9021'),
    ('Georgios Smaragdakis', '68/6243'),
    ('Kaitai Liang', 'l/KaitaiLiang'),
]

for name, pid in editors:
    q = f'''
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT (COUNT(DISTINCT ?publ) as ?cnt)
WHERE {{
  <https://dblp.org/pid/{pid}> ^dblp:authoredBy ?publ .
  ?publ dblp:publishedInStream <https://dblp.org/streams/conf/asplos> .
  ?publ dblp:publishedIn ?venue .
  ?publ dblp:pagination ?pg .
  ?publ dblp:yearOfPublication ?year .
  FILTER(REGEX(STR(?venue), "^ASPLOS"))
  FILTER(REGEX(STR(?pg), "-"))
  FILTER(?year = "2025")
}}
'''
    url = f'https://sparql.dblp.org/sparql?{urllib.parse.urlencode({"query":q,"format":"json"})}'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0','Accept':'application/sparql-results+json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode())
        cnt = int(d['results']['bindings'][0]['cnt']['value']) if d['results']['bindings'] else 0
        print(f'{name}: ASPLOS 2025 real papers = {cnt}')
    except Exception as e:
        print(f'{name}: ERR {e}')
    time.sleep(2)
