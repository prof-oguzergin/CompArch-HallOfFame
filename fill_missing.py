"""
Fill missing HPCA and ASPLOS counts using PID-based DBLP XML queries.
"""
import xml.etree.ElementTree as ET, urllib.request, json, sys, time, re
sys.stdout.reconfigure(encoding='utf-8')

# Load data.js to get affiliations with PIDs
with open("data.js", "r", encoding="utf-8") as f:
    content = f.read()

# Extract affiliations PIDs
pids = {}
aff_match = re.search(r'affiliations:\s*\{(.*?)\},', content, re.DOTALL)
if aff_match:
    for m in re.finditer(r'"([^"]+)":\s*\{[^}]*pid:"([^"]+)"', aff_match.group(1)):
        pids[m.group(1)] = m.group(2)

# People with missing HPCA
hpca_missing = [
    "Mark Horowitz", "T. N. Vijaykumar", "Jingwen Leng", "Anoop Gupta",
    "Won Woo Ro", "Henry Hoffmann", "Swamit Tannu", "Shouyi Yin",
    "Ricardo Bianchini", "Simha Sethumadhavan", "Myoungsoo Jung",
    "Dan Tsafrir", "Andrew R. Pleszkun", "Yang Hu", "Janak H. Patel",
    "Keshav Pingali", "Arvind", "Xing Hu", "Jian Huang",
    "Li-Shiuan Peh", "Chao Li", "Jae W. Lee", "Qi Guo", "Ang Li",
    "Jorge Albericio", "Pen-Chung Yew", "Daniel A. Jimenez"
]

# People with missing ASPLOS
asplos_missing = [
    "Antonio González", "Gu-Yeon Wei", "Alper Buyuktosunoglu",
    "T. N. Vijaykumar", "Jun Yang", "Pradip Bose", "Won Woo Ro",
    "Sreenivas Subramoney", "David T. Blaauw", "Tao Li",
    "G. Edward Suh", "Carole-Jean Wu", "Yiannakis Sazeides",
    "A. Giray Yaglikci", "Gary S. Tyson", "Michel Dubois",
    "Hsien-Hsin S. Lee", "Donghyuk Lee", "Anant Agarwal",
    "David H. Albonesi", "Naveen Muralimanohar", "Lixin Zhang",
    "Lizhong Chen", "Eric Rotenberg", "Xiaowei Jiang",
    "Edward S. Davidson", "Daehoon Kim", "Shouyi Yin",
    "Mohammad Sadrosadati", "Konstantinos Kanellopoulos"
]

def query_pid(pid, venue):
    url = f'https://dblp.org/pid/{pid}.xml'
    req = urllib.request.Request(url, headers={'User-Agent': 'CompArch-HoF/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        tree = ET.parse(resp)
    root = tree.getroot()
    years = {}
    for elem in root.iter():
        bt = elem.find('booktitle')
        yr = elem.find('year')
        if bt is not None and venue in (bt.text or ''):
            y = int(yr.text) if yr is not None else 0
            if y > 0:
                years[y] = years.get(y, 0) + 1
    return sum(years.values()), years

# Process HPCA missing
print("=== HPCA MISSING ===")
for name in hpca_missing:
    pid = pids.get(name)
    if not pid:
        print(f"  NO PID: {name}")
        continue
    try:
        total, years = query_pid(pid, 'HPCA')
        if total > 0:
            ystr = ','.join(f'{y}:{c}' for y,c in sorted(years.items()))
            flag = "NEW HOF" if total >= 8 else "cross"
            print(f"  {flag}: {name} pid:{pid} HPCA={total} [{ystr}]")
        else:
            print(f"  zero: {name} pid:{pid} HPCA=0")
    except Exception as e:
        print(f"  ERROR: {name} pid:{pid} {e}")
    time.sleep(3)

print("\n=== ASPLOS MISSING ===")
for name in asplos_missing:
    pid = pids.get(name)
    if not pid:
        print(f"  NO PID: {name}")
        continue
    try:
        total, years = query_pid(pid, 'ASPLOS')
        if total > 0:
            ystr = ','.join(f'{y}:{c}' for y,c in sorted(years.items()))
            flag = "NEW HOF" if total >= 8 else "cross"
            print(f"  {flag}: {name} pid:{pid} ASPLOS={total} [{ystr}]")
        else:
            print(f"  zero: {name} pid:{pid} ASPLOS=0")
    except Exception as e:
        print(f"  ERROR: {name} pid:{pid} {e}")
    time.sleep(3)
