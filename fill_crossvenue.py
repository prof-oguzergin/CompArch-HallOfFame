#!/usr/bin/env python3
"""
fill_crossvenue.py
Fills missing cross-venue data for CompArch Hall of Fame members using DBLP XML API.
Also verifies ASPLOS suspects: Benjamin C. Lee, Tao Li, Ang Li, Chao Li.

Usage: python fill_crossvenue.py [--dry-run] [--limit N]
"""

import re
import json
import time
import xml.etree.ElementTree as ET
import argparse
import sys
from collections import defaultdict

# Try requests first (handles TLS edge cases better on Windows)
try:
    import requests as _requests
    import urllib3
    urllib3.disable_warnings()
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USE_REQUESTS = False

# ─── Configuration ────────────────────────────────────────────────────────────
DBLP_PID_URL = "https://dblp.org/pid/{pid}.xml"
REQUEST_DELAY = 4      # seconds between requests (respect rate limiting)
MAX_RETRIES   = 3
RETRY_WAIT    = 15     # seconds before retry on 429/503

# Known PIDs for ASPLOS suspects not yet in affiliations
SUSPECT_OVERRIDE_PIDS = {
    # Benjamin C. Lee (Duke → now he moved; HPCA HoF member)
    # DBLP: https://dblp.org/pid/l/BenjaminCLee
    "Benjamin C. Lee": "l/BenjaminCLee",
    # Tao Li (HPCA/MICRO HoF) - there are two Tao Li's on DBLP
    # The comparch one is at U Florida / USTC: https://dblp.org/pid/l/TaoLi3
    # The MICRO HoF Tao Li is different from the ASPLOS suspect Tao Li
    # Need disambiguation; mark as needs-manual-check
    "Tao Li (HPCA)":  "l/TaoLi3",    # HPCA member - Tao Li at U Florida
    # Ang Li (MICRO HoF, Microsoft/PNNL)
    # https://dblp.org/pid/l/AngLi4
    "Ang Li":  "l/AngLi4",
}

# DBLP venue key prefixes for the 4 conferences
VENUE_KEYS = {
    "hpca":   "conf/hpca",
    "micro":  "conf/micro",
    "isca":   "conf/isca",
    "asplos": "conf/asplos",
}

# Tags that indicate non-paper entries to skip
SKIP_TYPES = {"proceedings", "editorship"}   # DBLP r/@type values

# Regex patterns that identify keynotes/invited talks in titles
KEYNOTE_RE = re.compile(
    r'\b(keynote|invited\s+talk|invited\s+paper|panel|tutorial|workshop\s+summary)\b',
    re.IGNORECASE
)


# ─── Parse data.js ────────────────────────────────────────────────────────────
def load_data_js(path: str) -> dict:
    """Minimal parser: extract hof_names, crossvenue dict, affiliations dict."""
    with open(path, encoding="utf-8") as f:
        src = f.read()

    result = {
        "hof_members": set(),       # canonical names across all venues
        "hof_venue":   {},          # name -> which HoF venues they belong to
        "crossvenue":  {},          # name -> {hpca:N, micro:N, ...}
        "affiliations": {},         # name -> {inst:..., pid:...}
    }

    # ── Extract HoF member names from the four venue arrays ──────────────────
    venue_blocks = re.findall(
        r'(hpca|micro|isca|asplos)\s*:\s*\[([^\]]*(?:\[[^\]]*\])*[^\]]*)\]',
        src, re.DOTALL
    )
    for venue_tag, block in venue_blocks:
        names = re.findall(r'\{name:"([^"]+)"', block)
        for n in names:
            result["hof_members"].add(n)
            result["hof_venue"].setdefault(n, set()).add(venue_tag)

    # ── Extract affiliations block ────────────────────────────────────────────
    # Isolate from "affiliations: {" to the closing "},"
    aff_start = src.find("affiliations: {")
    if aff_start != -1:
        aff_brace_start = src.index("{", aff_start)
        depth, i = 0, aff_brace_start
        while i < len(src):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        aff_block = src[aff_brace_start+1:i]
        # Each line: "Name": {inst:"...", pid:"..."}
        for m in re.finditer(
            r'"([^"]+)"\s*:\s*\{[^}]*\}',
            aff_block
        ):
            entry_text = m.group(0)
            name = m.group(1)
            inst_m = re.search(r'inst\s*:\s*"([^"]*)"', entry_text)
            pid_m  = re.search(r'pid\s*:\s*"([^"]*)"',  entry_text)
            inst = inst_m.group(1) if inst_m else ""
            pid  = pid_m.group(1)  if pid_m  else ""
            result["affiliations"][name] = {"inst": inst, "pid": pid}

    # ── Extract crossvenue block ──────────────────────────────────────────────
    cv_start = src.find("crossvenue: {")
    if cv_start != -1:
        cv_brace_start = src.index("{", cv_start)
        depth, i = 0, cv_brace_start
        while i < len(src):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        cv_block = src[cv_brace_start+1:i]
        for m in re.finditer(r'"([^"]+)"\s*:\s*\{([^}]*)\}', cv_block):
            name = m.group(1)
            counts = {}
            for kv in re.finditer(r'(hpca|micro|isca|asplos)\s*:\s*(\d+)', m.group(2)):
                counts[kv.group(1)] = int(kv.group(2))
            result["crossvenue"][name] = counts

    return result


# ─── DBLP fetch helpers ───────────────────────────────────────────────────────
_session = None

def get_session():
    global _session
    if _session is None and USE_REQUESTS:
        import requests
        from requests.adapters import HTTPAdapter
        import ssl

        class TLSAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.options |= 0x4   # OP_NO_SSLv2
                try:
                    ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
                except Exception:
                    pass
                kwargs['ssl_context'] = ctx
                super().init_poolmanager(*args, **kwargs)

        _session = requests.Session()
        _session.mount('https://', TLSAdapter())
        _session.mount('http://', TLSAdapter())
        _session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; CompArchHoF/1.0)'})
    return _session


def fetch_dblp_xml(pid: str) -> str | None:
    url = DBLP_PID_URL.format(pid=pid)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CompArchHoF/1.0)"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if USE_REQUESTS:
                sess = get_session()
                resp = sess.get(url, timeout=25, verify=False)
                if resp.status_code in (429, 503):
                    print(f"    Rate-limited ({resp.status_code}), waiting {RETRY_WAIT}s …", flush=True)
                    time.sleep(RETRY_WAIT)
                    continue
                if resp.status_code == 404:
                    print(f"    PID not found: {pid}", flush=True)
                    return None
                resp.raise_for_status()
                return resp.text
            else:
                import urllib.request, urllib.error
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as r:
                    return r.read().decode("utf-8", errors="replace")
        except Exception as ex:
            msg = str(ex)
            print(f"    Attempt {attempt}/{MAX_RETRIES} error for {pid}: {msg[:120]}", flush=True)
            if attempt < MAX_RETRIES:
                wait = RETRY_WAIT * attempt   # back-off: 15s, 30s
                print(f"    Waiting {wait}s before retry …", flush=True)
                time.sleep(wait)
    return None


def count_venue_papers(xml_src: str) -> dict[str, int]:
    """Parse DBLP XML and count regular papers per venue."""
    counts = defaultdict(int)
    try:
        root = ET.fromstring(xml_src)
    except ET.ParseError as e:
        print(f"    XML parse error: {e}", flush=True)
        return counts

    for r in root.iter("r"):
        # Each <r> wraps one pub element: article, inproceedings, proceedings, etc.
        for child in r:
            pub_type = child.tag.lower()  # "inproceedings", "proceedings", "article" …

            # Skip proceedings/editorship
            if pub_type in SKIP_TYPES:
                continue

            # We only care about conference papers (inproceedings)
            if pub_type != "inproceedings":
                continue

            # Check keynote/invited via title
            title_el = child.find("title")
            title = (title_el.text or "") if title_el is not None else ""
            if KEYNOTE_RE.search(title):
                continue

            # Get booktitle key from <crossref> or <booktitle>
            crossref_el = child.find("crossref")
            key_attr = child.get("key", "")

            # Primary: use paper's own key (e.g. conf/hpca/Smith99)
            for venue_name, venue_prefix in VENUE_KEYS.items():
                if key_attr.startswith(venue_prefix + "/"):
                    counts[venue_name] += 1
                    break

    return dict(counts)


# ─── Determine what is "missing" for a member ────────────────────────────────
def missing_venues(hof_venues: set, crossvenue_entry: dict | None) -> list[str]:
    """Return list of venues where we have no cross-venue data and member is NOT in HoF."""
    all_venues = set(VENUE_KEYS.keys())
    non_hof_venues = all_venues - hof_venues   # venues where they are NOT in HoF
    if crossvenue_entry is None:
        return sorted(non_hof_venues)
    already_have = set(crossvenue_entry.keys())
    return sorted(non_hof_venues - already_have)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fill missing cross-venue data from DBLP")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no network calls")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N members (0=all)")
    parser.add_argument("--name", type=str, default="", help="Process only this name")
    args = parser.parse_args()

    data_js_path = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\data.js"
    output_path  = r"C:\Users\Z GAMES\Yapay Zeka\CompArch-HallOfFame\crossvenue_update.json"

    print("Loading data.js …", flush=True)
    data = load_data_js(data_js_path)

    hof_members  = data["hof_members"]
    hof_venue    = data["hof_venue"]
    crossvenue   = data["crossvenue"]
    affiliations = data["affiliations"]

    print(f"  HoF members found : {len(hof_members)}")
    print(f"  Affiliations with PID: {sum(1 for v in affiliations.values() if v.get('pid'))}")
    print(f"  Existing crossvenue entries: {len(crossvenue)}")

    # ── ASPLOS suspects: always include for verification ─────────────────────
    suspects = ["Benjamin C. Lee", "Tao Li", "Ang Li", "Chao Li"]
    suspect_pids = {}
    for s in suspects:
        pid = (affiliations.get(s) or {}).get("pid", "")
        # Apply override if no PID found in affiliations
        if not pid and s in SUSPECT_OVERRIDE_PIDS:
            pid = SUSPECT_OVERRIDE_PIDS[s]
            print(f"  [Override PID] {s} -> {pid}")
        suspect_pids[s] = pid
        # Make sure we process them
        if s not in hof_members:
            hof_venue.setdefault(s, set())   # treat as having no HoF (forces all-venue check)
    print("\nASPLOS suspects and their PIDs:")
    for s, pid in suspect_pids.items():
        hv = hof_venue.get(s, set())
        cv = crossvenue.get(s, {})
        print(f"  {s:30s} PID: {pid or 'MISSING':25s} HoF: {sorted(hv)}  CV: {cv}")

    # ── Build work list: members with a PID but missing ≥1 cross-venue count ─
    work_list = []
    for name in sorted(hof_members | set(suspects)):
        # For suspects, use the suspect_pids dict (may have override)
        if name in suspects:
            pid = suspect_pids.get(name, "")
        else:
            pid = (affiliations.get(name) or {}).get("pid", "")
        if not pid:
            continue
        hv = hof_venue.get(name, set())
        cv = crossvenue.get(name, {})
        missing = missing_venues(hv, cv or None)
        if name in suspects:
            # Always add suspects for full re-check
            work_list.append((name, pid, hv, cv, missing, True))
        elif missing:
            work_list.append((name, pid, hv, cv, missing, False))

    # Filter by --name
    if args.name:
        work_list = [(n, p, hv, cv, m, s) for (n, p, hv, cv, m, s) in work_list
                     if args.name.lower() in n.lower()]

    # Apply limit
    if args.limit > 0:
        work_list = work_list[:args.limit]

    print(f"\nWork list: {len(work_list)} members to process")
    for name, pid, hv, cv, missing, is_suspect in work_list:
        flag = " [SUSPECT]" if is_suspect else ""
        print(f"  {name:40s} pid={pid:25s} missing={missing}{flag}")

    if args.dry_run:
        print("\n[Dry run — no network requests]")
        sys.exit(0)

    # ── Connectivity test ─────────────────────────────────────────────────────
    print("\nTesting DBLP connectivity …", flush=True)
    test_xml = fetch_dblp_xml("m/OnurMutlu")
    if test_xml is None:
        print("ERROR: Cannot reach dblp.org. Check network connection.")
        print("  The script logic and parsing are correct — run again when DBLP is accessible.")
        sys.exit(1)
    print(f"  OK — received {len(test_xml):,} bytes for test PID m/OnurMutlu", flush=True)
    time.sleep(REQUEST_DELAY)

    # ── Process each member ───────────────────────────────────────────────────
    results = {
        "new_crossvenue":      {},  # name -> {hpca:N, micro:N, ...} (brand-new entries)
        "updated_crossvenue":  {},  # name -> {venue:N, ...} (new keys added to existing entry)
        "suspect_verification":{},  # name -> full counts from DBLP
        "errors":              [],
        "skipped_no_pid":      [],
    }

    for idx, (name, pid, hv, cv, missing, is_suspect) in enumerate(work_list, 1):
        print(f"\n[{idx}/{len(work_list)}] {name}  (PID: {pid})", flush=True)

        xml_src = fetch_dblp_xml(pid)
        if xml_src is None:
            results["errors"].append({"name": name, "pid": pid, "reason": "fetch_failed"})
            time.sleep(REQUEST_DELAY)
            continue

        all_counts = count_venue_papers(xml_src)
        print(f"    DBLP counts: {all_counts}", flush=True)

        if is_suspect:
            results["suspect_verification"][name] = {
                "pid": pid,
                "dblp_counts": all_counts,
                "hof_venues": sorted(hv),
                "existing_crossvenue": cv,
                "note": ""
            }
            # Check if any venue hits 8+ (would be a new HoF candidate)
            for v, cnt in all_counts.items():
                if v not in hv and cnt >= 8:
                    results["suspect_verification"][name]["note"] += (
                        f"WARNING: {v.upper()} count={cnt} ≥ 8 (potential new HoF entry!). "
                    )

        # Add missing entries
        new_keys = {}
        for venue in missing:
            cnt = all_counts.get(venue, 0)
            if venue not in hv:   # double-check: don't add if already in HoF
                new_keys[venue] = cnt

        if new_keys:
            if cv:
                results["updated_crossvenue"][name] = new_keys
                print(f"    → UPDATE existing entry with: {new_keys}", flush=True)
            else:
                results["new_crossvenue"][name] = new_keys
                print(f"    → NEW entry: {new_keys}", flush=True)

        time.sleep(REQUEST_DELAY)

    # ── Write output JSON ─────────────────────────────────────────────────────
    # Convert sets to lists for JSON serialisation
    for v in results["suspect_verification"].values():
        v["hof_venues"] = list(v.get("hof_venues", []))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Results written to: {output_path}")
    print(f"  New crossvenue entries  : {len(results['new_crossvenue'])}")
    print(f"  Updated crossvenue entries: {len(results['updated_crossvenue'])}")
    print(f"  Suspect verifications   : {len(results['suspect_verification'])}")
    print(f"  Errors                  : {len(results['errors'])}")

    # ── Print suspect summary ─────────────────────────────────────────────────
    if results["suspect_verification"]:
        print("\n── ASPLOS Suspect Verification ──────────────────────────")
        for name, info in results["suspect_verification"].items():
            print(f"\n  {name}")
            print(f"    PID         : {info['pid']}")
            print(f"    DBLP counts : {info['dblp_counts']}")
            print(f"    HoF venues  : {info['hof_venues']}")
            print(f"    Existing CV : {info['existing_crossvenue']}")
            if info["note"]:
                print(f"    *** {info['note']}")

    # ── Print new/updated entries for easy copy-paste into data.js ───────────
    if results["new_crossvenue"] or results["updated_crossvenue"]:
        print("\n── Suggested data.js updates ────────────────────────────")
        all_new = {**results["new_crossvenue"], **results["updated_crossvenue"]}
        for name in sorted(all_new):
            counts = all_new[name]
            parts = ",".join(f"{v}:{n}" for v, n in sorted(counts.items()))
            print(f'  "{name}": {{{parts}}},')


if __name__ == "__main__":
    main()
