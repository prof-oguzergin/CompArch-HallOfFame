"""Test GS scraping pipeline on 5 HoF members."""
import urllib.request, urllib.parse, re, time, sys
sys.stdout.reconfigure(encoding='utf-8')

tests = [
    ('Onur Mutlu', 'ETH Zurich'),
    ('Yale N. Patt', 'UT Austin'),
    ('Mahmut Taylan Kandemir', 'Penn State'),
    ('Moinuddin Qureshi', 'Georgia Tech'),
    ('Daniel Sánchez', 'MIT'),
]

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

def find_gs_id(name, aff):
    q = urllib.parse.quote(f'{name} {aff} google scholar')
    url = f'https://duckduckgo.com/html/?q={q}'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    ids = re.findall(r'scholar\.google\.com[^\"\s]*user%3D([A-Za-z0-9_-]+)', html)
    if not ids:
        ids = re.findall(r'scholar\.google\.com[^\"\s]*user=([A-Za-z0-9_-]+)', html)
    return ids[0] if ids else None

def fetch_gs(gs_id):
    url = f'https://scholar.google.com/citations?user={gs_id}&hl=en&cstart=0&pagesize=100'
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    # Metrics from table
    m = re.search(r'Citations.*?<td[^>]*>(\d+)</td>.*?h-index.*?<td[^>]*>(\d+)</td>.*?i10.*?<td[^>]*>(\d+)</td>', html, re.DOTALL)
    metrics = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    # Paper cites (all papers on this page)
    # Citation counts in paper rows: <a ... class="gsc_a_ac ...">NNN</a>
    cites = [int(x) for x in re.findall(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)</a>', html)]
    return metrics, cites

for name, aff in tests:
    print(f'\n=== {name} ({aff}) ===')
    try:
        gs_id = find_gs_id(name, aff)
        print(f'  GS id: {gs_id}')
        if gs_id:
            time.sleep(3)
            metrics, first_page_cites = fetch_gs(gs_id)
            if metrics:
                print(f'  Total cites: {metrics[0]}, h-index: {metrics[1]}, i10: {metrics[2]}')
                print(f'  First page papers: {len(first_page_cites)} (top cite: {max(first_page_cites) if first_page_cites else 0})')
                for t in [100, 200, 400, 800, 1000]:
                    n = sum(1 for c in first_page_cites if c >= t)
                    print(f'    {t}+: {n}')
    except Exception as e:
        print(f'  ERR: {e}')
    time.sleep(5)
