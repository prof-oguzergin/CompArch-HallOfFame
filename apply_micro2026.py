# -*- coding: utf-8 -*-
"""Add MICRO 2026 (MICRO-59, program of 5 Oct 2026) to data.js. Provisional until dblp indexes MICRO 2026.

Inputs: micro2026_candidates.json (micro2026_match.py), dblp_sparql/*.json (pre-2026 counts by PID).
Every decision below was checked by hand against the program's affiliations; dry run unless --apply.
"""
import json, re, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
APPLY = "--apply" in sys.argv

C = json.load(open("micro2026_candidates.json", encoding="utf-8"))
ns = {}; exec(open("dblp_verify.py", encoding="utf-8").read().split("hof = json.load")[0], ns); classify = ns["classify"]
DB = {v: json.load(open(f"dblp_sparql/{v}.json", encoding="utf-8")) for v in ["hpca", "micro", "isca", "asplos"]}

# ---- existing MICRO members: 2026 papers (industry-track papers not counted for now) ----
count = {name: sum(1 for t, n, aff, ind in v["papers"] if not ind) for name, v in C["members"].items()}
count["Rakesh Kumar"] = 0          # program author is Rakesh Kumar (NTNU), a different person
count["Ang Li"] = 1                # BITE (PNNL co-authors); CacheFlex is Ang Li (UW, Princeton PhD), another person
count["Jangwoo Kim"] = 1           # SafeMind; BoostX-RNIC is an industry-track paper
count["Juan Gomez-Luna"] = 1       # program spells "Juan Gómez Luna" (NVIDIA): PipeDRAM
count["Ronald G. Dreslinski"] = 1  # program spells "Ron Dreslinski": Orbital AI Datacenters
count = {k: v for k, v in count.items() if v}

# ---- new MICRO members: site name -> (dblp pid, MICRO 2026 papers) ----
NEW = {
    "Guangyu Sun": ("29/6473-3", 7), "Ataberk Olgun": ("285/5355", 4), "Yu Feng": ("30/4550-7", 7),
    "Zhuoran Song": ("220/4324", 4), "Fangxin Liu": ("198/2194", 6), "Yang Hu": ("43/4685-1", 3),
    "Shouyi Yin": ("98/3428", 2), "José F. Martínez": ("m/JFMartinez", 2), "Lizy Kurian John": ("j/LizyKurianJohn", 1),
    "Minyi Guo": ("99/6797", 6), "Nisa Bostancı": ("293/6888", 4), "Jaehyuk Huh": ("83/5240", 1),
    "Houxiang Ji": ("205/7183", 3), "Yinhe Han": ("32/2695-1", 4), "Adrián Cristal": ("41/1128", 2),
    "Osman S. Ünsal": ("79/1809", 2), "Yun Liang": ("83/2265", 1), "Heiner Litz": ("89/5432", 1),
    "Alexandros Daglis": ("142/3203", 1), "Liqiang Lu": ("202/5928", 3), "Seokin Hong": ("78/9350", 1),
    "A. Giray Yağlıkçı": ("147/4019", 1),   # program: "Abdullah Giray Yaglikci (CISPA)", Terracotta
}
# not entrants (checked): Jian Wang 39/449-46 is a 1987-1994 Tsinghua author, not the ICT CAS author of 2026;
# Yuan-Hsi Chou 5+1=6
NEW_SITE = {   # not on the site before: affiliation, Google Scholar (fetch_gs_one.py, 5 Oct 2026)
    "Zhuoran Song": ("SJTU", '{gs:"LgHi-gQAAAAJ",h:15,i10:19,c:753,b:[1,0,0,0,0]}'),
    "Fangxin Liu": ("SJTU", '{gs:"dXzsaIsAAAAJ",h:18,i10:37,c:1416,b:[2,0,0,0,0]}'),
    "Nisa Bostancı": ("ETH Zurich", '{gs:"PfU0Q38AAAAJ",h:18,i10:21,c:1136,b:[2,1,0,0,0]}'),
    "Houxiang Ji": ("UIUC", '{gs:"tJwsCPYAAAAJ",h:11,i10:13,c:854,b:[2,1,0,0,0]}'),
    "Yinhe Han": ("ICT-CAS", '{gs:"t40cM-4AAAAJ",h:39,i10:145,c:7327,b:[13,5,2,0,0]}'),
    "Osman S. Ünsal": ("BSC Barcelona", '{gs:"6JU2JSMAAAAJ",h:40,i10:143,c:6460,b:[13,3,0,0,0]}'),
    "Heiner Litz": ("UC Santa Cruz", '{gs:"NVAyqAgAAAAJ",h:28,i10:47,c:2933,b:[6,2,0,0,0]}'),
    "Alexandros Daglis": ("Georgia Tech / U Edinburgh", '{gs:"Mm-dHpMAAAAJ",h:18,i10:24,c:1378,b:[4,1,0,0,0]}'),
    "Liqiang Lu": ("Zhejiang U", '{gs:"wvpFjh0AAAAJ",h:18,i10:28,c:2326,b:[8,5,0,0,0]}'),
    "Seokin Hong": ("SKKU", '{gs:"RdB0pDUAAAAJ",h:13,i10:23,c:707,b:[0,0,0,0,0]}'),
}
# members of other venues with MICRO 2026 papers who stay below 8 at MICRO: crossvenue micro += n
CV_ADD = {"Ahmed Louri": 1, "Chao Li": 1, "Christina Delimitrou": 1, "David W. Nellans": 1, "Hai Jin": 3,
          "Hai Helen Li": 1, "Jie Zhang": 1,          # Peking U only; "Jie Zhang (Southeast Univ.)" is another person
          "Jovan Stojkovic": 2, "Kevin Skadron": 1, "Leibo Liu": 1, "Mike O'Connor": 1, "Mingyu Gao": 3,
          "Myoungsoo Jung": 1, "Quan Chen": 1, "Saugata Ghose": 1, "Vikram S. Adve": 1, "Xiaofei Liao": 2, "Yiran Chen": 1}
AFF_INST = {"A. Giray Yağlıkçı": "CISPA", "Mohammad Alian": "Cornell", "Juan Gomez-Luna": "NVIDIA"}   # verified moves

def main_years(pid, v="micro"):
    ys = {}
    for r in DB[v]:
        if classify(v, r) == "MAIN" and any(p["pid"] == pid for p in r["persons"]):
            ys[r["year"]] = ys.get(r["year"], 0) + 1
    return ys
def fmt_entry(name, ys):
    yy = ",".join(f"{y}:{c}" for y, c in sorted(ys.items()))
    return f'  {{name:"{name}",total:{sum(ys.values())},y:{{{yy}}}}}'

data = open("data.js", encoding="utf-8").read()
D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync("data.js","utf8");const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify({micro:D.micro,crossvenue:D.crossvenue,affiliations:D.affiliations,gs:D.gs}))']).decode("utf-8"))
micro_names = {e["name"] for e in D["micro"]}

# ---- micro block ----
a = data.index("\nmicro: [") + 1; b = data.index("\n]", a)
lines = data[a:b].split("\n")
out, done = [], set()
for ln in lines:
    m = re.match(r'\s*\{name:"([^"]+)",total:(\d+),y:\{([^}]*)\}\}(,?)\s*$', ln)
    if m and m.group(1) in count:
        name = m.group(1); ys = {int(k): int(c) for k, c in (kv.split(":") for kv in m.group(3).split(",") if kv)}
        assert 2026 not in ys, name
        ys[2026] = count[name]; done.add(name)
        ln = fmt_entry(name, ys) + m.group(4)
        print(f"update  {name:28s} {m.group(2)} -> {sum(ys.values())}")
    out.append(ln)
missing = set(count) - done
assert not missing, missing
if not out[-1].rstrip().endswith(","): out[-1] = out[-1].rstrip() + ","
for name, (pid, n) in NEW.items():
    assert name not in micro_names, name
    ys = main_years(pid); assert 2026 not in ys; ys[2026] = n
    assert sum(ys.values()) >= 8, (name, ys)
    out.append(fmt_entry(name, ys) + ",")
    print(f"NEW     {name:28s} {sum(ys.values())}  {ys}")
out[-1] = out[-1].rstrip(",")
data = data[:a] + "\n".join(out) + data[b:]

# ---- crossvenue block (edits strictly inside it) ----
cs = data.index("\ncrossvenue: {"); ce = data.index("\n},", cs) + 1
cv = data[cs:ce].split("\n")
def cv_line(name, c):
    return f'  "{name}": {{' + ",".join(f"{v}:{c[v]}" for v in ["hpca", "micro", "isca", "asplos"] if c.get(v)) + "},"
idx = {re.match(r'\s*"([^"]+)":', l).group(1): i for i, l in enumerate(cv) if re.match(r'\s*"([^"]+)":', l)}
for name in NEW:
    if name in NEW_SITE: continue
    c = dict(D["crossvenue"].get(name, {})); c.pop("micro", None)
    cv[idx[name]] = cv_line(name, c); print(f"cv-micro {name}: {D['crossvenue'].get(name)} -> {c}")
for name, n in CV_ADD.items():
    c = dict(D["crossvenue"].get(name, {})); c["micro"] = c.get("micro", 0) + n
    assert c["micro"] < 8, (name, c)
    if name in idx: cv[idx[name]] = cv_line(name, c)
    else: cv.insert(2, cv_line(name, c))
    print(f"cv+     {name}: {D['crossvenue'].get(name)} -> {c}")
for name in NEW_SITE:
    pid = NEW[name][0]
    c = {v: sum(main_years(pid, v).values()) for v in ["hpca", "isca", "asplos"]}
    assert all(x < 8 for x in c.values()), (name, c)
    cv.insert(2, cv_line(name, c)); print(f"cv new  {name}: {c}")
data = data[:cs] + "\n".join(cv) + data[ce:]

# ---- affiliations and gs ----
def insert_after(head, new_lines):
    global data
    i = data.index("\n" + head) + len("\n" + head)
    data = data[:i] + "".join("\n" + l for l in new_lines) + data[i:]
insert_after("affiliations: {", [f'  "{n}": {{inst:"{inst}",pid:"{NEW[n][0]}"}},' for n, (inst, g) in NEW_SITE.items()])
insert_after("gs: {", [f'  "{n}":{g},' for n, (inst, g) in NEW_SITE.items()])
s0 = data.index("\naffiliations: {"); s1 = data.index("\n},", s0)
blk = data[s0:s1]
for name, inst in AFF_INST.items():
    blk2, k = re.subn(r'(\n  "' + re.escape(name) + r'":\s*\{inst:")[^"]*(")', lambda m: m.group(1) + inst + m.group(2), blk)
    assert k == 1, name; blk = blk2; print(f"inst    {name} -> {inst}")
data = data[:s0] + blk + data[s1:]

# ---- changelog ----
entrants = ", ".join(NEW)
note = (f'  {{date:"5 Oct 2026",text:"MICRO 2026 added from the conference program (to be re-checked against DBLP once it is indexed). '
        f'{len(NEW)} researchers crossed the 8-paper MICRO threshold: {entrants}. '
        f'Existing members\' MICRO records were extended through 2026. MICRO Hall of Fame now {len(D["micro"]) + len(NEW)}."}},\n')
data = data.replace("updates: [\n", "updates: [\n" + note, 1)
print(note)
if APPLY:
    open("data.js", "w", encoding="utf-8", newline="").write(data)
    print("data.js written")
