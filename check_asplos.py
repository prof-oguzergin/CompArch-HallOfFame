#!/usr/bin/env python3
"""
Check ASPLOS papers for HPCA/MICRO/ISCA authors not yet in asplos_dblp.json
"""

import json
import re
import sys
import time
import urllib.request
import urllib.parse

DATA_JS = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\data.js"
ASPLOS_JSON = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\asplos_dblp.json"
OUTPUT_JSON = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\asplos_new_candidates.json"

THRESHOLD_REPORT = 5
THRESHOLD_CANDIDATE = 8
DELAY = 1.5

def extract_authors_from_datajs(path):
    """Extract unique author names from hpca, micro, isca arrays in data.js"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    authors = set()
    # Match name:"..." patterns inside hpca, micro, isca sections
    # Strategy: find each array block then extract names
    for conf in ['hpca', 'micro', 'isca']:
        # Find the array for this conference
        pattern = rf'{conf}:\s*\[(.*?)\],\s*(?:asplos|micro|isca|hpca|\}})'
        m = re.search(pattern, content, re.DOTALL)
        if m:
            block = m.group(1)
        else:
            # Try finding up to end
            start = content.find(f'{conf}:')
            if start == -1:
                print(f"WARNING: could not find {conf} in data.js", file=sys.stderr)
                continue
            # Find matching bracket
            bracket_start = content.find('[', start)
            depth = 0
            end = bracket_start
            for i, ch in enumerate(content[bracket_start:], bracket_start):
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            block = content[bracket_start+1:end]

        names = re.findall(r'name:"([^"]+)"', block)
        for n in names:
            authors.add(n)
        print(f"  {conf}: {len(names)} entries found", file=sys.stderr)

    return authors


def load_already_checked(path):
    """Load asplos_dblp.json and return set of already-checked author names"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # It's a list of objects with "name" field
        if isinstance(data, list):
            return {entry['name'] for entry in data if 'name' in entry}
        elif isinstance(data, dict):
            return set(data.keys())
        else:
            return set()
    except FileNotFoundError:
        print(f"WARNING: {path} not found, treating as empty", file=sys.stderr)
        return set()


def query_dblp_asplos(author_name):
    """Query DBLP for ASPLOS papers by author. Returns (total, years_dict, titles_list)"""
    encoded = urllib.parse.quote(author_name)
    url = f"https://dblp.org/search/publ/api?q={encoded}+venue%3AASPLOS&format=json&h=100"

    req = urllib.request.Request(url, headers={"User-Agent": "CompArch-HallOfFame/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
    except Exception as e:
        print(f"    ERROR querying {author_name}: {e}", file=sys.stderr)
        return 0, {}, []

    hits = data.get('result', {}).get('hits', {})
    total_str = hits.get('@total', '0')
    total = int(total_str)

    hit_list = hits.get('hit', [])
    if isinstance(hit_list, dict):
        hit_list = [hit_list]

    years = {}
    titles = []
    for hit in hit_list:
        info = hit.get('info', {})
        year = str(info.get('year', 'unknown'))
        title = info.get('title', '')
        venue = info.get('venue', '')
        # Filter to only ASPLOS entries (DBLP search can return fuzzy results)
        if 'ASPLOS' in venue.upper():
            years[year] = years.get(year, 0) + 1
            titles.append(f"  [{year}] {title}")

    confirmed_total = sum(years.values())
    return confirmed_total, years, titles


def main():
    print("=== CompArch Hall of Fame — ASPLOS Check ===", file=sys.stderr)
    print(f"Reading {DATA_JS}", file=sys.stderr)

    all_authors = extract_authors_from_datajs(DATA_JS)
    print(f"\nTotal unique authors in HPCA+MICRO+ISCA: {len(all_authors)}", file=sys.stderr)

    already_checked = load_already_checked(ASPLOS_JSON)
    print(f"Already checked for ASPLOS: {len(already_checked)}", file=sys.stderr)

    to_check = sorted(all_authors - already_checked)
    print(f"Authors still to check: {len(to_check)}", file=sys.stderr)
    print("", file=sys.stderr)

    results = []
    candidates = []  # 8+ papers

    for i, author in enumerate(to_check, 1):
        print(f"[{i}/{len(to_check)}] Querying: {author}", file=sys.stderr)
        total, years, titles = query_dblp_asplos(author)

        entry = {
            "name": author,
            "total": total,
            "years": years,
            "titles": titles
        }
        results.append(entry)

        if total >= THRESHOLD_REPORT:
            print(f"  *** {author}: {total} ASPLOS papers ***", file=sys.stderr)
            for t in titles[:5]:
                print(f"    {t}", file=sys.stderr)
            if total >= THRESHOLD_CANDIDATE:
                candidates.append(entry)
        else:
            print(f"  -> {total} papers", file=sys.stderr)

        if i < len(to_check):
            time.sleep(DELAY)

    # Save results
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n=== RESULTS SAVED TO {OUTPUT_JSON} ===", file=sys.stderr)
    print(f"\n=== AUTHORS WITH {THRESHOLD_CANDIDATE}+ ASPLOS PAPERS (NEW CANDIDATES) ===", file=sys.stderr)
    if candidates:
        for c in sorted(candidates, key=lambda x: x['total'], reverse=True):
            yrs = sorted(c['years'].keys())
            print(f"  {c['name']}: {c['total']} papers ({yrs[0]}–{yrs[-1]})", file=sys.stderr)
    else:
        print("  None found.", file=sys.stderr)

    # Also print a summary to stdout
    print("\n=== SUMMARY ===")
    print(f"Authors checked: {len(to_check)}")
    print(f"With 5+ ASPLOS papers:")
    for c in sorted(results, key=lambda x: x['total'], reverse=True):
        if c['total'] >= THRESHOLD_REPORT:
            yrs = sorted(c['years'].keys()) if c['years'] else ['?']
            print(f"  {c['name']}: {c['total']} ({yrs[0]}–{yrs[-1]})")
    print(f"\nWith 8+ ASPLOS papers (hall of fame candidates):")
    for c in sorted(candidates, key=lambda x: x['total'], reverse=True):
        yrs = sorted(c['years'].keys())
        print(f"  {c['name']}: {c['total']} ({yrs[0]}–{yrs[-1]})")


if __name__ == '__main__':
    main()
