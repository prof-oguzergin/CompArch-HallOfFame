"""Manually search for the 9 unmatched papers with query variations."""
import urllib.request, urllib.parse, json, time

# (conf, title_in_data_js, alternate_queries_to_try)
papers = [
    ("ISCA 2024", "Mind the Gap: Attainable Data Movement and Operational Intensity Bounds for Tensor Algorithms",
     ["Mind the Gap Attainable Data Movement Operational Intensity"]),
    ("HPCA 2024", "uPIMulator: A Fast and Flexible Simulation Framework for General Purpose PIM Architectures",
     ["uPIMulator Fast Flexible Simulation PIM"]),
    ("MICRO 2017", "Automated Memory Consistency Verification of Processor RTL Implementations with Dynamic Axiomatic Tests",
     ["Automated Memory Consistency Verification Processor RTL"]),
    ("MICRO 2017", "Architectural Techniques for Energy-Efficient Brain Implants Using Hardware Perceptron-based Classifiers",
     ["Energy-efficient brain implant neural decoding"]),
    ("USENIX Security 2018", "Foreshadow: Breaking Virtual Memory Protection and the SGX Ecosystem",
     ["Foreshadow SGX L1 Terminal Fault", "Foreshadow: Extracting the Keys to the Intel SGX Kingdom"]),
    ("ISCA 2018", "Mobilizing the Micro-Ops: Context-Sensitive Decoding On-Demand for Security and Performance",
     ["Mobilizing Micro-Ops Context-Sensitive Decoding"]),
    ("MICRO 2018", "CheckMate: Automated Synthesis of Hardware-Aware Exploit Synthesis Using the CheckMate Tool",
     ["CheckMate Automated Synthesis Hardware-Aware Exploits", "CheckMate Automated Exploit Hardware"]),
    ("MICRO 2021", "ITSLF: Inter-Thread Store-to-Load Forwarding in Simultaneous Multithreading",
     ["Inter-thread store-to-load forwarding SMT"]),
    ("ISCA 2023", "uManycore: A Cloud-Native CPU for Tail at Scale",
     ["uManycore Cloud-Native CPU Tail Latency"]),
]

results = {}
for conf, title, variants in papers:
    print(f'\n=== {conf}: {title[:70]} ===')
    all_queries = [title] + variants
    for q in all_queries:
        url = f'https://api.semanticscholar.org/graph/v1/paper/search/match?query={urllib.parse.quote(q)}&fields=title,year,citationCount,externalIds'
        req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)'})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
            hits = data.get('data', [])
            if hits:
                h = hits[0]
                print(f'  Q: "{q[:60]}..."')
                print(f'  -> "{h.get("title")}" ({h.get("year")}) - {h.get("citationCount")} cites - score={h.get("matchScore"):.0f}')
                results[(conf, title)] = {
                    'query': q,
                    'matched_title': h.get('title'),
                    'year': h.get('year'),
                    'citations': h.get('citationCount'),
                    'score': h.get('matchScore')
                }
                break
            else:
                print(f'  Q: "{q[:60]}..." -> no match')
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f'  429 rate limit, waiting...')
                time.sleep(15)
            else:
                print(f'  HTTP {e.code}')
        time.sleep(3)
    if (conf, title) not in results:
        print(f'  !! NO MATCH FOUND with any variant')
    time.sleep(2)

print('\n\n=== SUMMARY ===')
for (conf, title), r in results.items():
    print(f'{conf}: {r["citations"]:>5} cites  |  {r["matched_title"][:80]}')

# Save results for merging
with open('fix_9_results.json', 'w', encoding='utf-8') as f:
    json.dump({f'{c}::{t[:80]}': r for (c,t), r in results.items()}, f, indent=2, ensure_ascii=False)
