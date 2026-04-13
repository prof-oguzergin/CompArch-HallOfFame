#!/usr/bin/env python3
"""
fill_hm_authors.py
Reads data.js, finds toppicks_papers entries with authors:[],
queries DBLP API for each, outputs hm_authors.json.
"""

import re
import json
import time
import random
import urllib.parse
import urllib.request
import urllib.error

DATA_JS = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\data.js"
OUTPUT_JSON = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\hm_authors.json"

DBLP_API = "https://dblp.org/search/publ/api"


def extract_hm_papers(js_path):
    """Parse data.js lines to extract HM papers with empty authors."""
    papers = []
    with open(js_path, "r", encoding="utf-8") as f:
        for line in f:
            # Match lines with type:"HM" and authors:[]
            if 'type:"HM"' in line and 'authors:[]' in line:
                year_m = re.search(r'year:(\d+)', line)
                conf_m = re.search(r'conf:"([^"]+)"', line)
                title_m = re.search(r'title:"([^"]+)"', line)
                if year_m and conf_m and title_m:
                    papers.append({
                        "year": int(year_m.group(1)),
                        "conf": conf_m.group(1),
                        "title": title_m.group(1)
                    })
    return papers


def query_dblp(title, max_results=5, retries=3):
    """Query DBLP search API and return list of hit dicts."""
    params = urllib.parse.urlencode({
        "q": title,
        "format": "json",
        "h": max_results
    })
    url = f"{DBLP_API}?{params}"
    headers = {"User-Agent": "CompArchHoF-author-filler/1.0 (research; contact: bilgi@oguzergin.net)"}
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", {}).get("hits", {}).get("hit", [])
        except (urllib.error.URLError, json.JSONDecodeError, ConnectionResetError, OSError) as e:
            wait = 10 + attempt * 15 + random.uniform(0, 5)
            print(f"  [ERROR] DBLP request failed (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"  Waiting {wait:.0f}s before retry...")
                time.sleep(wait)
    return []


def normalize_title(t):
    """Lowercase, strip punctuation for fuzzy comparison."""
    return re.sub(r'[^a-z0-9 ]', '', t.lower()).strip()


def extract_authors_from_hit(hit):
    """Extract author names from a DBLP hit dict."""
    info = hit.get("info", {})
    authors_field = info.get("authors", {})
    if not authors_field:
        return []
    author_list = authors_field.get("author", [])
    if isinstance(author_list, dict):
        # Single author returned as dict instead of list
        author_list = [author_list]
    names = []
    for a in author_list:
        if isinstance(a, dict):
            text = a.get("text", "")
        else:
            text = str(a)
        # DBLP sometimes appends disambiguation number like "Name 0001"
        text = re.sub(r'\s+\d{4}$', '', text).strip()
        if text:
            names.append(text)
    return names


def find_best_match(query_title, hits):
    """Return authors from the hit whose title best matches query_title."""
    qnorm = normalize_title(query_title)
    best_authors = []
    best_score = 0
    for hit in hits:
        info = hit.get("info", {})
        hit_title = info.get("title", "")
        hnorm = normalize_title(hit_title)
        # Score: ratio of matching words
        q_words = set(qnorm.split())
        h_words = set(hnorm.split())
        if not q_words:
            continue
        overlap = len(q_words & h_words)
        score = overlap / max(len(q_words), len(h_words))
        if score > best_score:
            best_score = score
            best_authors = extract_authors_from_hit(hit)
    return best_authors, best_score


def main():
    papers = extract_hm_papers(DATA_JS)
    print(f"Found {len(papers)} HM papers with empty authors.")
    print()

    # Load existing results to allow resuming
    existing = {}
    try:
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            prev = json.load(f)
        for r in prev:
            if r.get("authors"):  # Only use previously found entries with authors
                existing[r["title"]] = r
        print(f"Loaded {len(existing)} previously resolved entries.")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    results = []
    not_found = []

    for i, paper in enumerate(papers):
        title = paper["title"]
        year = paper["year"]
        conf = paper["conf"]
        print(f"[{i+1}/{len(papers)}] {year} | {conf}")
        print(f"  Title: {title}")

        # Use cached result if available
        if title in existing:
            cached = existing[title]
            print(f"  -> [CACHED] Authors: {cached['authors']}")
            results.append(cached)
            continue

        hits = query_dblp(title)
        if not hits:
            print("  -> No hits from DBLP")
            not_found.append({"year": year, "conf": conf, "title": title, "authors": [], "score": 0.0})
            results.append({"year": year, "conf": conf, "title": title, "authors": [], "score": 0.0})
            # Save partial results after every query
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            time.sleep(5 + random.uniform(0, 2))
            continue

        authors, score = find_best_match(title, hits)
        print(f"  -> Score: {score:.2f} | Authors: {authors}")

        entry = {"year": year, "conf": conf, "title": title, "authors": authors, "score": round(score, 3)}
        results.append(entry)
        if score < 0.5 or not authors:
            not_found.append(entry)

        # Save partial results after every query
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Rate limiting: 5-7 seconds between queries
        time.sleep(5 + random.uniform(0, 2))

    # Save results
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print()
    print(f"Results saved to {OUTPUT_JSON}")
    print()

    # Summary
    found = [r for r in results if r["authors"] and r["score"] >= 0.5]
    print(f"Successfully matched: {len(found)}/{len(papers)}")
    if not_found:
        print(f"Low confidence or missing ({len(not_found)}):")
        for nf in not_found:
            print(f"  [{nf['year']}] {nf['title'][:70]} (score={nf['score']})")

    print()
    print("=" * 70)
    print("FULL MAPPING (for data.js update):")
    print("=" * 70)
    for r in results:
        if r["authors"]:
            authors_js = ", ".join(f'"{a}"' for a in r["authors"])
            print(f"\n  // {r['year']} | {r['conf']}")
            print(f"  title: \"{r['title']}\"")
            print(f"  authors: [{authors_js}]")


if __name__ == "__main__":
    main()
