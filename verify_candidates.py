"""
Verify ASPLOS HoF candidates using DBLP author: exact matching.
Uses "author:FirstName LastName:" (with trailing colon) for exact author entity match.
"""
import json, time, urllib.request, urllib.parse, sys

CANDIDATES = [
    "Jun Yang",
    "Yang Hu",
    "Minyi Guo",
    "Chao Li",
    "Hai Jin",
    "Yufei Ding",
    "Mingyu Gao",
    "Qi Guo",
    "Rajiv Gupta",
    "Ang Li",
    "Jae W. Lee",
    "Jingwen Leng",
    "Jian Huang",
    "Joel S. Emer",
    "Arvind",
    "Benjamin C. Lee",
    "G. Edward Suh",
    "Tao Li",
    "Anand Sivasubramaniam",
    "Henry M. Levy",
    "Jangwoo Kim",
    "Jung Ho Ahn",
    "Nael Abu-Ghazaleh",
    "Rajeev Balasubramonian",
    "Susan J. Eggers",
    "Xing Hu",
]

def fetch(name):
    # Use author:Name: for exact entity match
    q = f'author:{name}: venue:ASPLOS'
    url = f"https://dblp.org/search/publ/api?q={urllib.parse.quote(q)}&format=json&h=100"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ERROR {name}: {e}", file=sys.stderr)
        return None

    hits = data.get("result", {}).get("hits", {})
    hit_list = hits.get("hit", [])

    years = {}
    titles = []
    for h in hit_list:
        info = h.get("info", {})
        venue = info.get("venue", "")
        if "ASPLOS" not in str(venue):
            continue
        year = int(info.get("year", 0))
        title = info.get("title", "")
        # Get all author names to verify
        authors_data = info.get("authors", {}).get("author", [])
        if isinstance(authors_data, dict):
            authors_data = [authors_data]
        author_names = [a.get("text", a) if isinstance(a, dict) else a for a in authors_data]

        if year > 0:
            years[year] = years.get(year, 0) + 1
            titles.append(f"  [{year}] {title}")

    total = sum(years.values())
    return {"name": name, "total": total, "years": dict(sorted(years.items())), "titles": titles}


for name in CANDIDATES:
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  {name}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    r = fetch(name)
    if r:
        print(f"  TOTAL: {r['total']}", file=sys.stderr)
        print(f"  YEARS: {r['years']}", file=sys.stderr)
        for t in r['titles']:
            print(t, file=sys.stderr)
    time.sleep(1.5)
