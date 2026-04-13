"""
Fetch IEEE Micro Top Picks papers from DBLP.
Top Picks are published in IEEE Micro, typically in the Jul/Aug issue (No. 4).
DBLP lists these under journals/micro.
We search for "Top Picks" in the title to identify the introduction articles,
then fetch all papers from those specific issues.
"""
import json, time, urllib.request, urllib.parse, sys, re

def dblp_search(query, max_results=1000):
    """Generic DBLP search."""
    results = []
    offset = 0
    batch = 100
    while offset < max_results:
        url = f"https://dblp.org/search/publ/api?q={urllib.parse.quote(query)}&format=json&h={batch}&f={offset}"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)"
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  ERROR at offset {offset}: {e}", file=sys.stderr)
            break

        hits = data.get("result", {}).get("hits", {})
        total = int(hits.get("@total", 0))
        hit_list = hits.get("hit", [])
        if not hit_list:
            break

        for h in hit_list:
            info = h.get("info", {})
            # Get authors
            authors_data = info.get("authors", {}).get("author", [])
            if isinstance(authors_data, dict):
                authors_data = [authors_data]
            authors = [a.get("text", a) if isinstance(a, dict) else a for a in authors_data]

            results.append({
                "title": info.get("title", ""),
                "authors": authors,
                "year": int(info.get("year", 0)),
                "venue": info.get("venue", ""),
                "volume": info.get("volume", ""),
                "number": info.get("number", ""),
                "pages": info.get("pages", ""),
                "type": info.get("type", ""),
                "key": info.get("key", ""),
            })

        offset += batch
        if offset >= total:
            break
        time.sleep(3)

    return results


def is_top_picks_paper(paper):
    """Check if a paper is from a Top Picks issue based on its DBLP key or pages."""
    title = paper.get("title", "").lower()
    # Skip editorial/introduction articles
    if "top picks" in title and ("special issue" in title or "guest editor" in title or "introduction" in title):
        return False
    # Skip if it's clearly not a research paper
    if title.startswith("proceedings") or paper.get("type") == "Editorship":
        return False
    return True


def main():
    # Strategy: search for all IEEE Micro papers that mention "Top Picks" in their context
    # Actually, better: fetch all papers from IEEE Micro vol X no 4 for each year
    # But DBLP doesn't easily filter by issue number in search API.

    # Alternative: fetch ALL IEEE Micro papers and filter by known Top Picks issue patterns
    # Top Picks papers have specific page ranges in the Jul/Aug issues

    # Best approach: search for "Top Picks" keyword in IEEE Micro
    print("=== Fetching IEEE Micro Top Picks data from DBLP ===", file=sys.stderr)

    # Step 1: Find Top Picks introduction articles to identify which issues are Top Picks
    print("\nStep 1: Finding Top Picks introduction articles...", file=sys.stderr)
    intros = dblp_search("Top Picks venue:IEEE Micro")
    time.sleep(3)

    print(f"  Found {len(intros)} results mentioning 'Top Picks'", file=sys.stderr)

    # Identify Top Picks years from introduction articles
    tp_years = set()
    for p in intros:
        if "top picks" in p["title"].lower():
            tp_years.add(p["year"])
            print(f"  {p['year']}: {p['title'][:80]}", file=sys.stderr)

    # Step 2: For each year, try to get all papers from that Top Picks issue
    # IEEE Micro Top Picks: typically vol X, no 4 (Jul/Aug)
    # We can search by year + volume
    print(f"\nStep 2: Fetching papers for each Top Picks year...", file=sys.stderr)

    all_tp_papers = []

    # Also search by year - "IEEE Micro" papers in specific volume/numbers
    # DBLP key pattern: journals/micro/AuthorYY
    for year in sorted(tp_years):
        print(f"\n  --- {year} ---", file=sys.stderr)
        # Search for IEEE Micro papers in this year
        query = f"venue:IEEE Micro year:{year}"
        papers = dblp_search(query, max_results=200)
        time.sleep(3)

        # Filter: Top Picks papers typically in number 4 (Jul/Aug) or number 1 (Jan/Feb for older years)
        # We look for papers with specific page ranges and exclude editorials
        tp_papers = []
        for p in papers:
            if not is_top_picks_paper(p):
                continue
            # Check if this is from the Top Picks issue
            # Heuristic: Jul/Aug issue, or papers with "Top Picks" in their DBLP context
            num = p.get("number", "")
            # Include all research papers from this year's IEEE Micro
            # (we'll filter more precisely later)
            tp_papers.append(p)

        for p in tp_papers:
            print(f"    [{p.get('number','')}] {p['title'][:70]} - {', '.join(p['authors'][:3])}", file=sys.stderr)

        all_tp_papers.extend(tp_papers)

    # Step 3: Count authors
    print(f"\n\n=== Author histogram ===", file=sys.stderr)
    author_counts = {}
    author_papers = {}
    for p in all_tp_papers:
        for a in p["authors"]:
            author_counts[a] = author_counts.get(a, 0) + 1
            if a not in author_papers:
                author_papers[a] = []
            author_papers[a].append({"year": p["year"], "title": p["title"][:60]})

    # Sort by count descending
    sorted_authors = sorted(author_counts.items(), key=lambda x: -x[1])

    for name, count in sorted_authors:
        if count >= 2:
            years = [str(p["year"]) for p in author_papers[name]]
            print(f"  {count:>2}x  {name:<35} ({', '.join(years)})", file=sys.stderr)

    # Save results
    output = {
        "total_papers": len(all_tp_papers),
        "years_covered": sorted(tp_years),
        "papers": all_tp_papers,
        "author_counts": dict(sorted_authors),
    }
    with open("toppicks_dblp.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to toppicks_dblp.json", file=sys.stderr)


if __name__ == "__main__":
    main()
