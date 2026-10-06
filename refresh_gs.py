# -*- coding: utf-8 -*-
"""Refresh the Google Scholar metrics of every researcher on the site (6 Oct 2026).

One request per profile: citations?user=ID&sortby=cited_by&pagesize=100 carries both the metrics table
(citations, h-index, i10-index, "All" column) and the first 100 papers by citations; a further page is
fetched only while the papers on the page are still at 100+ citations. Buckets b = papers with
100+, 200+, 400+, 800+, 1000+ citations, as in data.js.

Polite pacing (15-25 s between requests; the first run used 8-14 s and got HTTP 429 after 84 profiles).
On HTTP 429 the run waits 45 minutes and retries the same profile, at most 3 times, then stops; a captcha /
"unusual traffic" page stops it at once. It never tries to get around a block. Progress:
gs_refresh_<date>.json, so a rerun resumes. Each result also keeps the profile's affiliation line and its
10 most-cited titles, to check that the profile is the right person.
Usage: python refresh_gs.py            (fetch)
       python refresh_gs.py --report   (old vs new, name check)"""
import json, os, random, re, subprocess, sys, time, unicodedata, urllib.request, datetime, html as ihtml
sys.stdout.reconfigure(encoding="utf-8")
DATE = "20261006"
OUT = f"gs_refresh_{DATE}.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
TH = (100, 200, 400, 800, 1000)
PACE = (15, 25)          # seconds between requests (was 8-14 until the 429 at profile 85)
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D.gs))']).decode("utf-8"))
ids = {}
for name, g in D.items():
    if g.get("gs"): ids.setdefault(g["gs"], []).append(name)
# two researchers who had no Scholar data; profiles checked by hand on 6 Oct 2026 (name, affiliation, top papers)
for gid, n in {"om-NSbgAAAAJ": "Minesh Patel", "BHupl5EAAAAJ": "André Seznec"}.items(): ids.setdefault(gid, [n])
res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
for gid in [g for g, r in res.items() if "error" in r]: del res[gid]      # retry earlier errors

def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s.lower().replace("ı", "i")) if unicodedata.category(c) != "Mn")

class Blocked(Exception): pass
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            html = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise Blocked(f"HTTP {e.code}")
    if re.search(r"unusual traffic|gs_captcha|not a robot|recaptcha", html, re.I):
        raise Blocked("captcha page")
    return html

def profile(gid):
    base = f"https://scholar.google.com/citations?user={gid}&hl=en&sortby=cited_by&pagesize=100"
    html = get(base + "&cstart=0")
    if html is None: return {"error": "404"}
    name = re.search(r'id="gsc_prf_in"[^>]*>([^<]+)<', html)
    aff = re.search(r'class="gsc_prf_il"[^>]*>(.*?)</div>', html)
    titles = [ihtml.unescape(t) for t in re.findall(r'class="gsc_a_at">([^<]+)<', html)][:10]
    stats = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
    if len(stats) < 6: return {"error": "no metrics table"}
    cites = [int(x) for x in re.findall(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)</a>', html)]
    allc = list(cites); start = 0
    while len(cites) == 100 and cites[-1] >= TH[0] and start < 900:
        start += 100
        time.sleep(random.uniform(PACE[0], PACE[1]))
        html = get(base + f"&cstart={start}")
        cites = [int(x) for x in re.findall(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)</a>', html or "")]
        allc += cites
    return {"gs_name": name.group(1).strip() if name else None,
            "aff": ihtml.unescape(re.sub(r"<[^>]+>", "", aff.group(1))).strip() if aff else None, "titles": titles, "c": int(stats[0]), "h": int(stats[2]), "i10": int(stats[4]),
            "b": [sum(1 for c in allc if c >= t) for t in TH], "pages": start // 100 + 1,
            "when": datetime.datetime.now().isoformat(timespec="seconds")}

if "--report" in sys.argv:
    for gid, names in sorted(ids.items(), key=lambda kv: kv[1][0]):
        o = D.get(names[0], {"h": 0, "c": 0, "b": []}); n = res.get(gid)
        if not n: print(f"   MISSING {names[0]} {gid}"); continue
        if "error" in n: print(f"   ERROR {names[0]} {gid} {n['error']}"); continue
        last = lambda s: fold(s).replace(".", " ").split()[-1]
        flag = "" if any(last(x) == last(n["gs_name"] or "") for x in names) else f"   <-- profile name '{n['gs_name']}'"
        drop = "   <-- citations fell" if n["c"] < o["c"] else ""
        print(f"{names[0][:28]:28} h {o['h']:>3}->{n['h']:<3} c {o['c']:>6}->{n['c']:<6} b {o['b']}->{n['b']}{flag}{drop}")
    sys.exit()

todo = [g for g in ids if g not in res]
if "--ids" in sys.argv:          # re-read given profiles (e.g. to keep titles for checking): --ids ID1,ID2 [--as "Name"]
    todo = sys.argv[sys.argv.index("--ids") + 1].split(",")
    for g in todo: ids.setdefault(g, [sys.argv[sys.argv.index("--as") + 1]] if "--as" in sys.argv else [g])
print(f"{len(ids)} profiles, {len(todo)} to fetch", flush=True)
if "--wait" in sys.argv:
    w = int(sys.argv[sys.argv.index("--wait") + 1]); print(f"waiting {w} s before starting", flush=True); time.sleep(w)
backoffs = 0
for i, gid in enumerate(todo):
    while True:
        try:
            res[gid] = profile(gid); break
        except Blocked as e:
            json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
            if str(e) == "HTTP 429" and backoffs < 3:
                backoffs += 1
                print(f"HTTP 429 at {ids[gid][0]}; backing off 45 min ({backoffs}/3)", flush=True)
                time.sleep(2700); continue
            print(f"STOPPED at {ids[gid][0]} ({gid}): {e}; {len(res)} done", flush=True)
            sys.exit(2)
        except Exception as e:
            res[gid] = {"error": f"{type(e).__name__}: {e}"}; break
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    r = res[gid]
    print(f"[{i+1}/{len(todo)}] {ids[gid][0]}: " + (r.get("error") or f"h {r['h']} c {r['c']} b {r['b']} ({r['gs_name']})"), flush=True)
    time.sleep(random.uniform(PACE[0], PACE[1]))
print("done", len(res), flush=True)
