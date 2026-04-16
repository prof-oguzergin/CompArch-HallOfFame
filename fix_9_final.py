"""Re-fetch citations for 9 problematic papers using corrected titles + longer delays."""
import urllib.request, urllib.parse, json, time

# After title corrections - these are the paper entries needing citation lookup
papers = [
    ("ISCA 2024", "HM", "Mind the Gap: Attainable Data Movement and Operational Intensity Bounds for Tensor Algorithms"),
    ("HPCA 2024", "HM", "Pathfinding Future PIM Architectures by Demystifying a Commercial PIM Technology"),
    ("MICRO 2017", "HM", "RTLCheck: Verifying the Memory Consistency of RTL Designs"),
    ("MICRO 2017", "HM", "Architectural Techniques for Energy-Efficient Brain Implants Using Hardware Perceptrons"),
    ("USENIX Security 2018", "TP", "Foreshadow: Extracting the Keys to the Intel SGX Kingdom with Transient Out-of-Order Execution"),
    ("ISCA 2018", "TP", "Mobilizing the Micro-Ops: Exploiting Context Sensitive Decoding for Security and Energy Efficiency"),
    ("MICRO 2018", "TP", "CheckMate: Automated Synthesis of Hardware Exploits and Security Litmus Tests"),
    ("MICRO 2021", "HM", "ITSLF: Inter-Thread Store-to-Load Forwarding in Simultaneous Multithreading"),
    ("ISCA 2023", "HM", "μManycore: A Cloud-Native CPU for Tail at Scale"),
]

results = {}
for conf, ptype, title in papers:
    print(f'\n=== {conf}: {title[:70]} ===')
    q = urllib.parse.quote(title)
    url = f'https://api.semanticscholar.org/graph/v1/paper/search/match?query={q}&fields=title,year,citationCount,externalIds'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)'})

    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            hits = data.get('data', [])
            if hits:
                h = hits[0]
                print(f'  -> "{h.get("title")[:80]}" ({h.get("year")})  {h.get("citationCount")} cites  score={h.get("matchScore"):.0f}')
                results[(conf, title)] = h.get('citationCount')
            else:
                print('  no hits')
                results[(conf, title)] = None
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print('  404 no match')
                results[(conf, title)] = None
                break
            elif e.code == 429:
                wait = 30 * (attempt + 1)
                print(f'  429 rate limit, waiting {wait}s...')
                time.sleep(wait)
            else:
                print(f'  HTTP {e.code}')
                break
    time.sleep(8)

print('\n=== SUMMARY ===')
found = 0
for (c, t), cites in results.items():
    if cites is not None:
        found += 1
    print(f'  {c}: {"NONE" if cites is None else f"{cites:>5} cites"} | {t[:70]}')
print(f'\nFound {found}/{len(papers)}')
