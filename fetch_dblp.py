"""
Fetch per-year paper counts and per-author yearly data from DBLP for
HPCA, MICRO, ISCA, ASPLOS conferences.
Outputs JSON data for the Hall of Fame page.
"""
import json
import time
import urllib.request
import urllib.parse
import sys

VENUES = {
    "hpca": "HPCA",
    "micro": "MICRO",
    "isca": "ISCA",
    "asplos": "ASPLOS",
}

def fetch_dblp(venue_key, max_results=5000):
    """Fetch all papers for a venue from DBLP API with pagination."""
    papers = []
    offset = 0
    batch = 1000
    while offset < max_results:
        url = f"https://dblp.org/search/publ/api?q=venue%3A{venue_key}&format=json&h={batch}&f={offset}"
        print(f"  Fetching {venue_key} offset={offset}...", file=sys.stderr)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CompArch-HallOfFame research project)"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  Error at offset {offset}: {e}", file=sys.stderr)
            break

        hits = data.get("result", {}).get("hits", {})
        total = int(hits.get("@total", 0))
        hit_list = hits.get("hit", [])
        if not hit_list:
            break

        for h in hit_list:
            info = h.get("info", {})
            year = int(info.get("year", 0))
            # Extract authors
            authors_data = info.get("authors", {}).get("author", [])
            if isinstance(authors_data, dict):
                authors_data = [authors_data]
            authors = [a.get("text", a) if isinstance(a, dict) else a for a in authors_data]
            papers.append({"year": year, "authors": authors, "title": info.get("title", "")})

        offset += batch
        if offset >= total:
            break
        time.sleep(2)  # Rate limiting

    return papers


def process_papers(papers):
    """Process papers into per-year counts and per-author yearly data."""
    year_counts = {}
    author_years = {}

    for p in papers:
        y = p["year"]
        year_counts[y] = year_counts.get(y, 0) + 1
        for a in p["authors"]:
            if a not in author_years:
                author_years[a] = {}
            author_years[a][y] = author_years[a].get(y, 0) + 1

    return {
        "yearly": dict(sorted(year_counts.items())),
        "authors": {
            name: {
                "total": sum(years.values()),
                "years": dict(sorted(years.items()))
            }
            for name, years in sorted(author_years.items(), key=lambda x: -sum(x[1].values()))
        }
    }


def main():
    all_data = {}
    for key, venue in VENUES.items():
        print(f"\n=== {venue} ===", file=sys.stderr)
        papers = fetch_dblp(venue)
        print(f"  Total papers fetched: {len(papers)}", file=sys.stderr)
        all_data[key] = process_papers(papers)
        time.sleep(3)  # Pause between venues

    # Write output
    with open("dblp_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\nData written to dblp_data.json", file=sys.stderr)

    # Print summary
    for key in VENUES:
        d = all_data[key]
        total = sum(d["yearly"].values())
        years = sorted(d["yearly"].keys())
        top5 = list(d["authors"].items())[:5]
        print(f"\n{VENUES[key]}: {total} papers, {years[0]}-{years[-1]}, {len(d['authors'])} authors", file=sys.stderr)
        for name, info in top5:
            print(f"  {name}: {info['total']}", file=sys.stderr)


if __name__ == "__main__":
    main()
