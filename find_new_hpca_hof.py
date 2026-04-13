"""
Find potential new HPCA HoF entrants from HPCA 2026.
1. Parse HPCA 2026 author list
2. Remove known HoF members
3. For remaining authors with 2+ HPCA 2026 papers, check DBLP for total HPCA count
4. Report anyone with 8+ total
"""
import json, time, urllib.request, urllib.parse, sys, re

# Parse data.js to get existing HPCA HoF names
with open("data.js", "r", encoding="utf-8") as f:
    content = f.read()

hof_names = set()
for m in re.finditer(r'hpca:\s*\[(.*?)\]', content, re.DOTALL):
    for nm in re.finditer(r'name:"([^"]+)"', m.group(1)):
        hof_names.add(nm.group(1).lower().replace(".", "").strip())

# HPCA 2026 papers (from the DBLP listing user provided)
hpca2026_raw = open("update_hpca2026.py", "r", encoding="utf-8").read()
# Extract from the raw string
start = hpca2026_raw.find('hpca2026_raw = """') + len('hpca2026_raw = """')
end = hpca2026_raw.find('"""', start)
lines = hpca2026_raw[start:end].strip().split('\n')

author_counts_2026 = {}
for line in lines:
    line = line.strip()
    if not line:
        continue
    authors = [a.strip() for a in line.split(',')]
    for a in authors:
        author_counts_2026[a] = author_counts_2026.get(a, 0) + 1

# Filter: not in HoF, with 2+ papers in 2026
candidates = []
for name, count in sorted(author_counts_2026.items(), key=lambda x: -x[1]):
    if name.lower().replace(".", "").strip() in hof_names:
        continue
    if count >= 2:
        candidates.append((name, count))

print(f"Candidates with 2+ HPCA 2026 papers (not in HoF): {len(candidates)}", file=sys.stderr)

def fetch_hpca_count(name):
    q = f'author:{name}: venue:HPCA'
    url = f"https://dblp.org/search/publ/api?q={urllib.parse.quote(q)}&format=json&h=100"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return -1, str(e)

    hits = data.get("result", {}).get("hits", {})
    hit_list = hits.get("hit", [])
    years = {}
    for h in hit_list:
        info = h.get("info", {})
        if "Editorship" in info.get("type", ""):
            continue
        title = info.get("title", "")
        if title.startswith("Proceedings of"):
            continue
        v = info.get("venue", "")
        if "HPCA" not in str(v):
            continue
        year = int(info.get("year", 0))
        if year > 0:
            years[year] = years.get(year, 0) + 1
    return sum(years.values()), years

# Check each candidate
print(f"\nChecking {len(candidates)} candidates on DBLP...\n", file=sys.stderr)
new_entrants = []
for name, count_2026 in candidates:
    total, years = fetch_hpca_count(name)
    if total < 0:
        print(f"  ERROR: {name}: {years}", file=sys.stderr)
        continue
    if total >= 7:  # Show 7+ as potential (might reach 8 with 2026)
        marker = "NEW HOF!" if total >= 8 else "close"
        print(f"  {marker}: {name}: {total} total HPCA papers ({count_2026} in 2026) {dict(sorted(years.items()))}", file=sys.stderr)
        if total >= 8:
            new_entrants.append({"name": name, "total": total, "years": years, "count_2026": count_2026})
    time.sleep(3)

print(f"\n=== NEW HPCA HOF ENTRANTS: {len(new_entrants)} ===", file=sys.stderr)
for e in new_entrants:
    ystr = ",".join(f"{y}:{c}" for y, c in sorted(e["years"].items()))
    print(f'  {{name:"{e["name"]}",total:{e["total"]},y:{{{ystr}}}}},', file=sys.stderr)
