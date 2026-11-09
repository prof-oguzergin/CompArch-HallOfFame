# -*- coding: utf-8 -*-
"""IEEE Micro 46(5), Guest Editors' Introduction (9 Nov 2026): the twelfth Top Pick and the 11 Honorable Mentions.
Pulls each conference paper from the dblp SPARQL endpoint (title, ordered authors with PIDs, venue, DOI) and the Semantic
Scholar citation count of that DOI. Output: dblp_sparql/tp2025_issue_records.json, read by apply_tp2025_issue.py."""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "CompArch-HallOfFame data check"}
WANT = [("TP", "ASPLOS", "Forecasting GPU Performance for Deep Learning Training and Inference", "Forecasting GPU Performance"),
    ("HM", "HPCA", "CORDOBA: Carbon-Efficient Optimization Framework for Computing Systems", "CORDOBA carbon"),
    ("HM", "MICRO", "Dissecting and Modeling the Architecture of Modern GPU Cores", "Dissecting Modeling Architecture Modern GPU Cores"),
    ("HM", "OSDI", "EMT: An OS Framework for New Memory Translation Architectures", "EMT OS Framework Memory Translation"),
    ("HM", "MICRO", "Flexing RISC-V Instruction Subset Processors to Extreme Edge", "Flexing RISC-V Instruction Subset"),
    ("HM", "USENIX Security", "GPUHammer: Rowhammer Attacks on GPU Memories Are Practical", "GPUHammer"),
    ("HM", "MICRO", "Learning to Walk: Architecting Learned Virtual Memory Translation", "Learning to Walk Learned Virtual Memory Translation"),
    ("HM", "SOSP", "LithOS: An Operating System for Efficient Machine Learning on GPUs", "LithOS"),
    ("HM", "ISCA", "RT+SpMSpM: Harnessing Ray Tracing for Efficient Sparse Matrix Computations", "Harnessing Ray Tracing Sparse Matrix"),
    ("HM", "ISCA", "Single-Address-Space FaaS with Jord", "Single-Address-Space FaaS Jord"),
    ("HM", "ISCA", "SpecASan: Mitigating Transient Execution Attacks Using Speculative Address Sanitization", "SpecASan"),
    ("HM", "ASPLOS", "TAPAS: Thermal- and Power-Aware Scheduling for LLM Inference in Cloud Platforms", "TAPAS Thermal Power-Aware Scheduling LLM")]
ENDPOINT = "https://sparql.dblp.org/sparql"
STREAM = {"ASPLOS": "asplos", "HPCA": "hpca", "MICRO": "micro", "ISCA": "isca", "OSDI": "osdi", "SOSP": "sosp", "USENIX Security": "uss"}
Q = """PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?publ ?t ?v ?doi ?o ?pers ?name WHERE {
  ?publ dblp:publishedInStream <https://dblp.org/streams/conf/%s> ; a dblp:Inproceedings ;
        dblp:yearOfPublication "2025"^^<http://www.w3.org/2001/XMLSchema#gYear> ; dblp:title ?t ; dblp:hasSignature ?s .
  ?s dblp:signatureOrdinal ?o ; dblp:signatureCreator ?pers ; dblp:signatureCreator ?pers .
  ?pers dblp:primaryCreatorName ?name .
  OPTIONAL { ?publ dblp:publishedIn ?v } OPTIONAL { ?publ dblp:doi ?doi }
}"""
def sparql(q):
    data = urllib.parse.urlencode({"query": q}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={"Accept": "application/sparql-results+json", **UA})
    with urllib.request.urlopen(req, timeout=300) as r: return json.load(r)["results"]["bindings"]
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return json.loads(r.read().decode("utf-8"))
def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())
def s2(doi, title):
    """Semantic Scholar citation count, by DOI or (USENIX papers have no DOI in dblp) by exact title. Backs off on 429."""
    F = "fields=citationCount,title,abstract"
    url = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?{F}" if doi else
           f"https://api.semanticscholar.org/graph/v1/paper/search/match?query={urllib.parse.quote(title)}&{F}")
    for wait in (20, 60, 120, 300, 0):
        time.sleep(6)
        try:
            d = get(url); d = d["data"][0] if "data" in d else d
            if not doi and norm(d["title"]) != norm(title): print("   S2 title differs:", d["title"]); return None, None
            return d["citationCount"], d.get("abstract")
        except urllib.error.HTTPError as e:
            if e.code != 429 or not wait: print("   S2:", title[:40], e); return None, None
            time.sleep(wait)
papers = {}
for v in sorted({w[1] for w in WANT}):
    rows = sparql(Q % STREAM[v]); time.sleep(3)
    P = papers.setdefault(v, {})
    for b in rows:
        r = P.setdefault(b["publ"]["value"], {"title": b["t"]["value"], "venue": b.get("v", {}).get("value", ""), "doi": b.get("doi", {}).get("value", ""), "a": {}})
        r["a"][int(b["o"]["value"])] = [b["name"]["value"], b["pers"]["value"].split("/pid/")[-1]]
    print(v, len(P), "papers")
out = []
for typ, venue, title, q in WANT:
    key = norm(title)[:24]
    hit = [(k, r) for k, r in papers[venue].items() if norm(r["title"]).startswith(key)]
    if len(hit) != 1:                     # the conference title may differ from the one in the issue: show keyword matches
        words = [w for w in re.findall(r"[a-z0-9]+", q.lower()) if len(w) > 3]
        near = [r["title"] for r in papers[venue].values() if sum(w in r["title"].lower() for w in words) >= max(1, len(words) - 1)]
        print(f"!! {typ} {venue} {title}: {len(hit)} exact, near: {near[:5]}")
        out.append({"type": typ, "want_venue": venue, "want_title": title, "missing": True}); continue
    k, r = hit[0]
    doi = re.sub(r"^https?://doi.org/", "", r["doi"])
    cites, abstract = s2(doi, r["title"].rstrip("."))
    if "Forecasting GPU" in title: print("   abstract mentions NeuSight:", "NeuSight" in (abstract or ""))
    au = [r["a"][o] for o in sorted(r["a"])]
    print(f"{typ} {venue} | {r['title']} | {doi} | cites {cites} ||", ", ".join(a[0] for a in au))
    out.append({"type": typ, "want_venue": venue, "want_title": title, "key": k, "title": r["title"].rstrip("."), "venue": r["venue"], "doi": doi, "authors": au, "cites": cites})
json.dump(out, open("dblp_sparql/tp2025_issue_records.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("found", sum("missing" not in r for r in out), "of", len(out))
