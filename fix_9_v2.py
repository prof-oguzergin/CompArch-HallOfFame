"""Use regular search endpoint (more lenient) with year filter."""
import urllib.request, urllib.parse, json, time

papers = [
    ("ISCA 2024", 2024, "Mind the Gap Attainable Data Movement Operational Intensity Tensor"),
    ("HPCA 2024", 2024, "uPIMulator Fast Flexible Simulation PIM"),
    ("MICRO 2017", 2017, "Automated Memory Consistency Verification Processor RTL"),
    ("MICRO 2017", 2017, "Energy-Efficient Brain Implants Hardware Perceptron"),
    ("USENIX Security 2018", 2018, "Foreshadow Extracting Keys Intel SGX Kingdom"),  # already matched, 1167
    ("ISCA 2018", 2018, "Mobilizing Micro-Ops Context-Sensitive Decoding Security"),
    ("MICRO 2018", 2018, "CheckMate Automated Exploit Synthesis Hardware"),
    ("MICRO 2021", 2021, "Inter-Thread Store-to-Load Forwarding Simultaneous Multithreading"),
    ("ISCA 2023", 2023, "uManycore Cloud-Native CPU Tail"),
]

for conf, year, q in papers:
    print(f'\n=== {conf} — {q[:60]} ===')
    # Try search endpoint with year filter
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(q)}&year={year}&fields=title,year,citationCount,venue,externalIds&limit=5'
    req = urllib.request.Request(url, headers={'User-Agent':'CompArch-HallOfFame/1.0 (bilgi@oguzergin.net)'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        hits = data.get('data', [])
        if not hits:
            print('  No hits')
        for i, h in enumerate(hits[:3]):
            print(f'  {i+1}. [{h.get("year")}] {h.get("title")[:90]}')
            print(f'     venue: {h.get("venue","?")[:60]} | cites: {h.get("citationCount")}')
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print('  429 rate limit, waiting 30s...')
            time.sleep(30)
        else:
            print(f'  HTTP {e.code}')
    time.sleep(4)
