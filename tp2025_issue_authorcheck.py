# -*- coding: utf-8 -*-
"""Second source for tp2025_issue_records.json: the publisher's author lists (Crossref for papers with a DOI, the USENIX
page for the two without), compared with dblp's, plus the site's existing spellings of each surname (one person written
two ways, or two people merged by a PID)."""
import html, json, re, subprocess, sys, unicodedata, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "CompArch-HallOfFame data check"}
R = json.load(open("dblp_sparql/tp2025_issue_records.json", encoding="utf-8"))
USENIX = {"EMT": "https://www.usenix.org/conference/osdi25/presentation/chai",
          "GPUHammer": "https://www.usenix.org/conference/usenixsecurity25/presentation/lin-shaopeng"}
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s.lower().replace("ı", "i")) if unicodedata.category(c) != "Mn").replace(".", "").strip()
def strip(n): return re.sub(r"\s+\d{4}$", "", n)
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return r.read().decode("utf-8", errors="replace")
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify(D))']).decode("utf-8"))
site = set(a for p in D["toppicks_papers"] for a in p["authors"]) | {e["name"] for v in ["isca", "micro", "asplos", "hpca"] for e in D[v]}
by_last = {}
for n in site: by_last.setdefault(fold(n).split()[-1], set()).add(n)
for r in R:
    names, src = None, None
    try:
        if r["doi"]:
            m = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(r["doi"])))["message"]
            names = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in m["author"]]; src = "Crossref"
        else:
            u = USENIX[r["title"].split(":")[0]]
            t = get(u); src = u
            names = [html.unescape(x) for x in re.findall(r'<meta name="citation_author" content="([^"]+)"', t)]
    except Exception as e:
        print("   fetch failed:", r["title"][:40], e)
    print(f"\n{r['type']} {r['title'][:70]} [{src}]")
    if names is not None:
        if len(names) != len(r["authors"]): print(f"   !! author count dblp {len(r['authors'])} vs {len(names)}: {names}")
        for (d, _), s in zip(r["authors"], names):
            if fold(strip(d)) != fold(s): print(f"   differs: dblp '{d}' vs source '{s}'")
    for d, _ in r["authors"]:
        n = strip(d); others = by_last.get(fold(n).split()[-1], set()) - {n}
        same_initial = {o for o in others if fold(o)[0] == fold(n)[0]}
        if same_initial: print(f"   site spelling? '{n}' vs {sorted(same_initial)}")
