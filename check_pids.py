"""
Check which DBLP PID links are broken in the CompArch Hall of Fame project.
Reads name->pid mappings from data.js affiliations section and checks each URL.
"""

import re
import time
import sys
import urllib.request
import urllib.error

# Fix Windows console encoding for Turkish characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATA_JS_PATH = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\data.js"

def extract_pids(filepath):
    """Extract name->pid mappings from the affiliations section of data.js."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Find affiliations section
    aff_match = re.search(r'affiliations\s*:\s*\{(.*?)\n\}', content, re.DOTALL)
    if not aff_match:
        raise ValueError("Could not find affiliations section in data.js")

    aff_section = aff_match.group(1)

    # Extract name and pid pairs
    pattern = r'"([^"]+)"\s*:\s*\{[^}]*pid\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, aff_section)

    return {name: pid for name, pid in matches}

def check_pid(pid):
    """Check if a DBLP PID URL returns 200."""
    url = f"https://dblp.org/pid/{pid}.html"
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; PID-checker/1.0)")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200, resp.status, url
    except urllib.error.HTTPError as e:
        return False, e.code, url
    except urllib.error.URLError as e:
        return False, str(e.reason), url
    except Exception as e:
        return False, str(e), url

def main():
    print("Extracting PIDs from data.js...")
    pid_map = extract_pids(DATA_JS_PATH)
    print(f"Found {len(pid_map)} entries with PIDs\n")

    broken = []
    ok = []

    for i, (name, pid) in enumerate(sorted(pid_map.items())):
        valid, status, url = check_pid(pid)
        if valid:
            ok.append((name, pid))
            print(f"[OK]     {name}: {pid}")
        else:
            broken.append((name, pid, status, url))
            print(f"[BROKEN] {name}: {pid}  (status: {status})")

        # Rate limiting: 2 seconds between requests (skip after last)
        if i < len(pid_map) - 1:
            time.sleep(2)

    print(f"\n{'='*60}")
    print(f"Results: {len(ok)} OK, {len(broken)} BROKEN")
    print(f"{'='*60}")

    if broken:
        print("\nBROKEN PIDs:")
        for name, pid, status, url in broken:
            print(f"  {name}")
            print(f"    PID: {pid}")
            print(f"    URL: {url}")
            print(f"    Status: {status}")
    else:
        print("\nAll PIDs are valid!")

if __name__ == "__main__":
    main()
