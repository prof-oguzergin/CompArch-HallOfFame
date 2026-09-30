# -*- coding: utf-8 -*-
"""Pull every record of the four HoF venue streams from the dblp SPARQL endpoint,
keyed by author/editor PID (never by name string). Output: dblp_sparql/<venue>.json

Each record: {publ, type: 'I'(Inproceedings)|'E'(Editorship), year, title, venue(publishedIn),
             pages, persons: [{pid, name}]}
"""
import json, sys, time, urllib.parse, urllib.request
from collections import defaultdict, Counter

ENDPOINT = "https://sparql.dblp.org/sparql"
VENUES = ["asplos", "isca", "micro", "hpca"]

QUERY = """PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?publ ?pers ?name ?y ?v ?pg ?t ?role WHERE {
  ?publ dblp:publishedInStream <https://dblp.org/streams/conf/%s> ;
        dblp:yearOfPublication ?y ; dblp:title ?t .
  { ?publ a dblp:Inproceedings ; dblp:authoredBy ?pers . BIND("I" AS ?role)
    OPTIONAL { ?publ dblp:publishedIn ?v } OPTIONAL { ?publ dblp:pagination ?pg } }
  UNION
  { ?publ a dblp:Editorship ; dblp:editedBy ?pers . BIND("E" AS ?role) }
  ?pers dblp:primaryCreatorName ?name .
}"""

def run(q):
    data = urllib.parse.urlencode({"query": q}).encode()
    req = urllib.request.Request(ENDPOINT, data=data,
        headers={"Accept": "application/sparql-results+json", "User-Agent": "CompArch-HoF-verify/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)

def pid_of(uri):
    return uri.split("/pid/", 1)[1] if "/pid/" in uri else uri

for v in VENUES:
    res = run(QUERY % v)
    rows = res["results"]["bindings"]
    total = res.get("meta", {}).get("result-size-total")
    recs = {}
    for b in rows:
        p = b["publ"]["value"]
        r = recs.setdefault(p, {"publ": p, "type": b["role"]["value"],
                                "year": int(str(b["y"]["value"])[:4]), "title": b["t"]["value"],
                                "venue": b.get("v", {}).get("value", ""),
                                "pages": b.get("pg", {}).get("value", ""), "persons": []})
        pe = {"pid": pid_of(b["pers"]["value"]), "name": b["name"]["value"]}
        if pe not in r["persons"]:
            r["persons"].append(pe)
    out = list(recs.values())
    json.dump(out, open(f"dblp_sparql/{v}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    types = Counter(r["type"] for r in out)
    venues = Counter(r["venue"] for r in out if r["type"] == "I")
    yrs = [r["year"] for r in out]
    print(f"{v}: rows={len(rows)} (endpoint total={total}) records={len(out)} types={dict(types)} years={min(yrs)}-{max(yrs)}")
    print("   publishedIn:", dict(venues.most_common(12)))
    time.sleep(3)
