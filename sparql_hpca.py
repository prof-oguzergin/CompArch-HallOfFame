"""
Use DBLP SPARQL endpoint to find HPCA authors with 8+ papers.
Much more reliable than REST API — disambiguated, filters keynotes via pagination.
"""
import json, urllib.request, urllib.parse, sys, re

SPARQL_ENDPOINT = "https://sparql.dblp.org/sparql"

QUERY = """
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?name ?affiliation (COUNT(DISTINCT ?publ) as ?freq) (?pers as ?dblp) (SAMPLE(?orcids) as ?orcid)
WHERE {
  VALUES ?stream {
    <https://dblp.org/streams/conf/hpca>
  }
  ?publ dblp:publishedInStream ?stream .
  ?publ dblp:publishedIn ?publishedin .
  ?publ dblp:authoredBy ?pers .
  ?pers rdfs:label ?name .
  ?publ dblp:pagination ?pagination .
  FILTER(REGEX(STR(?publishedin), "^HPCA"))
  FILTER(REGEX(STR(?pagination), "-"))
  OPTIONAL { ?pers dblp:primaryAffiliation ?affiliation . }
  OPTIONAL { ?pers dblp:orcid ?orcids . }
}
GROUP BY ?name ?affiliation ?pers
HAVING (?freq >= 7)
ORDER BY DESC(?freq)
"""

# Run SPARQL query
params = urllib.parse.urlencode({"query": QUERY, "format": "json"})
url = f"{SPARQL_ENDPOINT}?{params}"

print("Querying DBLP SPARQL endpoint...", file=sys.stderr)
req = urllib.request.Request(url, headers={
    "User-Agent": "CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)",
    "Accept": "application/sparql-results+json"
})

with urllib.request.urlopen(req, timeout=60) as resp:
    data = json.loads(resp.read().decode())

results = data.get("results", {}).get("bindings", [])
print(f"Got {len(results)} authors with 7+ HPCA papers\n", file=sys.stderr)

# Load existing HoF from data.js
with open("data.js", "r", encoding="utf-8") as f:
    content = f.read()

hof_names = set()
match = re.search(r'hpca:\s*\[(.*?)\],\s*\nmicro:', content, re.DOTALL)
if match:
    for nm in re.finditer(r'name:"([^"]+)"', match.group(1)):
        hof_names.add(nm.group(1))

# Also load affiliations to match by PID
aff_pids = {}
for m in re.finditer(r'"([^"]+)":\{[^}]*pid:"([^"]*)"', content):
    aff_pids[m.group(2)] = m.group(1)

print(f"Current HPCA HoF: {len(hof_names)} members", file=sys.stderr)
print(f"Known PIDs: {len(aff_pids)}", file=sys.stderr)

# Process results
print(f"\n{'='*80}")
print(f"DBLP SPARQL: HPCA authors with 7+ papers")
print(f"{'='*80}")
print(f"{'Papers':>6}  {'Name':<35} {'Affiliation':<40} {'In HoF?'}")
print(f"{'-'*6}  {'-'*35} {'-'*40} {'-'*7}")

new_candidates = []
for r in results:
    name = r["name"]["value"]
    freq = int(r["freq"]["value"])
    aff = r.get("affiliation", {}).get("value", "—")
    dblp_uri = r["dblp"]["value"]
    # Extract PID from URI: https://dblp.org/pid/XX/YYYY
    pid = dblp_uri.replace("https://dblp.org/pid/", "")

    # Check if in HoF (by name or PID)
    in_hof = name in hof_names or pid in aff_pids
    # Also check without disambiguation suffix
    clean_name = re.sub(r' \d{4}$', '', name)
    if clean_name in hof_names:
        in_hof = True

    marker = "YES" if in_hof else "*** NEW ***" if freq >= 8 else "close(7)"
    print(f"{freq:>6}  {name:<35} {aff:<40} {marker}")

    if not in_hof and freq >= 8:
        new_candidates.append({
            "name": name,
            "clean_name": clean_name,
            "freq": freq,
            "affiliation": aff,
            "pid": pid,
            "dblp_uri": dblp_uri
        })

print(f"\n{'='*80}")
print(f"NEW HPCA HOF CANDIDATES (8+ papers, not in current HoF):")
print(f"{'='*80}")
for c in new_candidates:
    print(f"  {c['freq']:>2} papers: {c['name']}")
    print(f"           Affiliation: {c['affiliation']}")
    print(f"           PID: {c['pid']}")
    print(f"           DBLP: {c['dblp_uri']}")
    print()

print(f"\nTotal: {len(new_candidates)} new candidates", file=sys.stderr)
