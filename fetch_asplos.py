"""
Fetch ASPLOS paper counts per author from DBLP.
For each author in our existing ASPLOS HoF list, query DBLP to get their
full ASPLOS publication history including recent years (2021-2026).
"""
import json, time, urllib.request, urllib.parse, sys

# Current ASPLOS HoF authors (from data.js) - we check these + potentially new entrants
AUTHORS = [
    "Luis Ceze", "Christos Kozyrakis", "Shan Lu", "Xuehai Qian",
    "Josep Torrellas", "Kathryn S. McKinley", "Onur Mutlu", "Mark D. Hill",
    "Trevor N. Mudge", "Michael M. Swift", "Timothy Sherwood",
    "Margaret Martonosi", "Yuanyuan Zhou", "Scott A. Mahlke", "Anoop Gupta",
    "Ricardo Bianchini", "Gurindar S. Sohi", "Sarita V. Adve", "Babak Falsafi",
    "Parthasarathy Ranganathan", "Alvin R. Lebeck", "Steven Swanson",
    "Dan Tsafrir", "Keshav Pingali", "Doug Burger", "Brandon Lucia",
    "Todd C. Mowry", "Joseph Devietti", "Mark Horowitz", "Mendel Rosenblum",
    "Thomas F. Wenisch", "Frederic T. Chong", "David A. Wood",
    "Christina Delimitrou", "Henry Hoffmann", "Abhishek Bhattacharjee",
    "Satish Narayanasamy",
    # Also check authors from other HoFs who might have 8+ ASPLOS papers by now
    "Dean M. Tullsen", "Daniel Sanchez", "Lieven Eeckhout",
    "Jason Mars", "Lingjia Tang", "David I. August",
    "Frederic T. Chong", "Christopher W. Fletcher",
    "Hadi Esmaeilzadeh", "Moinuddin K. Qureshi",
    "Hyesoon Kim", "Natalie Enright Jerger",
    "Tushar Krishna", "Rakesh Kumar",
    "David Brooks", "Yuan Xie", "Nam Sung Kim",
    "Wen-mei W. Hwu", "Mahmut Kandemir",
    "Kunle Olukotun", "John L. Hennessy",
]

# Deduplicate
AUTHORS = list(dict.fromkeys(AUTHORS))

def fetch_author_asplos(name):
    """Query DBLP for an author's ASPLOS papers."""
    # DBLP search: author name + venue ASPLOS
    q = f'{name} venue:ASPLOS'
    url = f"https://dblp.org/search/publ/api?q={urllib.parse.quote(q)}&format=json&h=100"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CompArch-HallOfFame/1.0 (research project; contact: bilgi@oguzergin.net)"
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
        # Filter: only ASPLOS papers
        if "ASPLOS" not in str(venue):
            continue
        year = int(info.get("year", 0))
        if year > 0:
            years[year] = years.get(year, 0) + 1
            titles.append(f"  [{year}] {info.get('title','')}")

    total = sum(years.values())
    return {"name": name, "total": total, "years": dict(sorted(years.items())), "titles": titles}


def main():
    results = []
    for i, name in enumerate(AUTHORS):
        print(f"[{i+1}/{len(AUTHORS)}] {name}...", file=sys.stderr)
        r = fetch_author_asplos(name)
        if r:
            results.append(r)
            if r["total"] > 0:
                print(f"  -> {r['total']} papers: {r['years']}", file=sys.stderr)
        time.sleep(1.5)  # Be nice to DBLP

    # Sort by total descending
    results.sort(key=lambda x: -x["total"])

    # Print results
    print("\n=== ASPLOS Hall of Fame (DBLP data) ===\n", file=sys.stderr)
    print("// 8+ papers threshold", file=sys.stderr)
    for r in results:
        if r["total"] >= 5:  # Show 5+ for reference
            marker = "***" if r["total"] >= 8 else "   "
            print(f"{marker} {r['name']}: {r['total']} papers {r['years']}", file=sys.stderr)

    # Output JS format for 8+ papers
    print("\n// === JavaScript data (8+ papers) ===")
    for r in results:
        if r["total"] >= 8:
            ystr = ",".join(f"{y}:{c}" for y, c in sorted(r["years"].items()))
            print(f'  {{name:"{r["name"]}",total:{r["total"]},y:{{{ystr}}}}},')

    # Also output full JSON for analysis
    with open("asplos_dblp.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nFull data saved to asplos_dblp.json", file=sys.stderr)


if __name__ == "__main__":
    main()
