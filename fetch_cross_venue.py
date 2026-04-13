"""
Cross-venue lookup: For every HoF member, fetch paper counts at ALL venues.
Uses DBLP author: exact match. Filters out proceedings/editorials.
Only queries venues where the person is NOT already in the HoF (saves queries).
"""
import json, time, urllib.request, urllib.parse, sys, re, os

VENUES = ["HPCA", "MICRO", "ISCA", "ASPLOS"]

def load_existing_data():
    """Parse data.js to get existing HoF members and their venue data."""
    with open("data.js", "r", encoding="utf-8") as f:
        content = f.read()

    authors = {}  # normalized_name -> {name, hpca, micro, isca, asplos}

    for venue in ["hpca", "micro", "isca", "asplos"]:
        # Find the venue array
        pattern = rf'{venue}:\s*\[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            continue
        block = match.group(1)
        # Parse each entry
        for m in re.finditer(r'\{name:"([^"]+)",total:(\d+),y:\{([^}]+)\}\}', block):
            name = m.group(1)
            total = int(m.group(2))
            years_str = m.group(3)
            years = {}
            for ym in re.finditer(r'(\d+):(\d+)', years_str):
                years[int(ym.group(1))] = int(ym.group(2))

            key = normalize(name)
            if key not in authors:
                authors[key] = {"name": name, "hpca": None, "micro": None, "isca": None, "asplos": None,
                                "hpca_hof": False, "micro_hof": False, "isca_hof": False, "asplos_hof": False}
            # Keep longest name
            if len(name) > len(authors[key]["name"]):
                authors[key]["name"] = name
            authors[key][venue] = {"total": total, "years": years}
            authors[key][f"{venue}_hof"] = True

    return authors


def normalize(name):
    return name.lower().strip().replace(".", "").replace("-", " ") \
        .replace("mateo valero cortés", "mateo valero") \
        .replace("mateo valero cortes", "mateo valero") \
        .replace("christoforos e kozyrakis", "christos kozyrakis") \
        .replace("jim smith", "james e smith") \
        .replace("scott mahlke", "scott a mahlke") \
        .replace("trevor mudge", "trevor n mudge") \
        .replace("natalie enright jerger", "natalie d enright jerger") \
        .replace("mahmut t kandemir", "mahmut taylan kandemir") \
        .replace("mahmut kandemir", "mahmut taylan kandemir") \
        .replace("daniel sánchez", "daniel sanchez") \
        .replace("andré seznec", "andre seznec") \
        .replace("per stenström", "per stenstrom") \
        .replace("a giray yaglikci", "abdullah giray yaglikci") \
        .replace("josé f martínez", "jose f martinez") \
        .replace("wen mei w hwu", "wen mei w hwu") \
        .replace("narayanan vijaykrishnan", "vijaykrishnan narayanan") \
        .replace("david t blaauw", "david blaauw") \
        .replace("josé maría arnau", "jose maria arnau")


def fetch_dblp(author_name, venue):
    """Query DBLP for author's papers at a venue. Returns total and per-year counts."""
    q = f'author:{author_name}: venue:{venue}'
    url = f"https://dblp.org/search/publ/api?q={urllib.parse.quote(q)}&format=json&h=100"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"    ERROR {author_name}/{venue}: {e}", file=sys.stderr)
        return None

    hits = data.get("result", {}).get("hits", {})
    hit_list = hits.get("hit", [])

    years = {}
    for h in hit_list:
        info = h.get("info", {})
        # Skip proceedings/editorials
        pub_type = info.get("type", "")
        if "Editorship" in pub_type:
            continue
        title = info.get("title", "")
        if title.startswith("Proceedings of"):
            continue
        v = info.get("venue", "")
        if venue not in str(v):
            continue
        year = int(info.get("year", 0))
        if year > 0:
            years[year] = years.get(year, 0) + 1

    total = sum(years.values())
    return {"total": total, "years": years}


def main():
    authors = load_existing_data()
    print(f"Loaded {len(authors)} unique authors from data.js", file=sys.stderr)

    # Load previous results if exists (for resuming)
    cache_file = "cross_venue_cache.json"
    cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} cached results", file=sys.stderr)

    total_queries = 0
    sorted_authors = sorted(authors.items(), key=lambda x: x[1]["name"])

    for i, (key, author) in enumerate(sorted_authors):
        name = author["name"]
        missing_venues = []
        for v in ["hpca", "micro", "isca", "asplos"]:
            if author[v] is None:
                missing_venues.append(v)

        if not missing_venues:
            continue

        cache_key = f"{name}"
        if cache_key in cache:
            # Restore from cache
            for v in missing_venues:
                if v in cache[cache_key]:
                    author[v] = cache[cache_key][v]
            continue

        print(f"[{i+1}/{len(sorted_authors)}] {name} - querying {', '.join(v.upper() for v in missing_venues)}", file=sys.stderr)
        cached_entry = {}

        for v in missing_venues:
            r = fetch_dblp(name, v.upper())
            if r:
                author[v] = r
                cached_entry[v] = r
                if r["total"] > 0:
                    print(f"    {v.upper()}: {r['total']}", file=sys.stderr)
            total_queries += 1
            time.sleep(3)

        cache[cache_key] = cached_entry
        # Save cache periodically
        if total_queries % 20 == 0:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)

    # Final cache save
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)

    # Build output
    results = []
    for key, author in authors.items():
        entry = {"name": author["name"]}
        total_all = 0
        for v in ["hpca", "micro", "isca", "asplos"]:
            d = author[v]
            count = d["total"] if d else 0
            entry[v] = count
            entry[f"{v}_hof"] = author[f"{v}_hof"]
            entry[f"{v}_years"] = d["years"] if d else {}
            total_all += count
        entry["total"] = total_all
        entry["venues_hof"] = sum(1 for v in ["hpca","micro","isca","asplos"] if author[f"{v}_hof"])
        results.append(entry)

    results.sort(key=lambda x: -x["total"])

    # Save full results
    with open("cross_venue_full.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\nTotal queries: {total_queries}", file=sys.stderr)
    print(f"\n{'Name':<30} {'Total':>5} {'HPCA':>6} {'MICRO':>6} {'ISCA':>6} {'ASPLOS':>7}", file=sys.stderr)
    print("-" * 75, file=sys.stderr)
    for r in results[:30]:
        def fmt(v):
            count = r[v]
            star = "★" if r[f"{v}_hof"] else ""
            return f"{count}{star}" if count > 0 else "-"
        print(f"{r['name']:<30} {r['total']:>5} {fmt('hpca'):>6} {fmt('micro'):>6} {fmt('isca'):>6} {fmt('asplos'):>7}", file=sys.stderr)


if __name__ == "__main__":
    main()
