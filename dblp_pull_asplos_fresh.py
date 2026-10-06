# -*- coding: utf-8 -*-
"""Fresh pull of the ASPLOS stream from the dblp SPARQL endpoint (same query and record format as
dblp_sparql_pull.py), written to dblp_sparql/asplos_<date>.json so the 30 Sep 2026 pull stays untouched.
Used by asplos2026_check.py to see whether dblp changed any author assignment since then."""
import json, sys, time, datetime
sys.stdout.reconfigure(encoding="utf-8")
src = open("dblp_sparql_pull.py", encoding="utf-8").read()
ns = {}; exec(src.split("for v in VENUES:")[0], ns)
res = ns["run"](ns["QUERY"] % "asplos")
rows = res["results"]["bindings"]
recs = {}
for b in rows:
    p = b["publ"]["value"]
    r = recs.setdefault(p, {"publ": p, "type": b["role"]["value"], "year": int(str(b["y"]["value"])[:4]),
                            "title": b["t"]["value"], "venue": b.get("v", {}).get("value", ""),
                            "pages": b.get("pg", {}).get("value", ""), "persons": []})
    pe = {"pid": ns["pid_of"](b["pers"]["value"]), "name": b["name"]["value"]}
    if pe not in r["persons"]:
        r["persons"].append(pe)
out = list(recs.values())
fn = f"dblp_sparql/asplos_{datetime.date.today():%Y%m%d}.json"
json.dump(out, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(fn, "rows", len(rows), "records", len(out), "endpoint total", res.get("meta", {}).get("result-size-total"))
