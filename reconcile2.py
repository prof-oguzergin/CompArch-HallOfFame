# -*- coding: utf-8 -*-
"""Robust reconcile: parse full ISCA2026 HTML correctly (comma-in-affiliation safe),
recount each data.js ISCA member's true 2026, and surface non-HoF authors who reach 8+."""
import re, html, unicodedata

raw = open('isca_prog_raw.html', encoding='utf-8').read()
src = open('data.js', encoding='utf-8').read()

def sa(s): return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')
def norm(s): s=sa(s).lower().strip(); s=re.sub(r'[.\-]',' ',s); return re.sub(r'\s+',' ',s).strip()
def collapse(s):
    t=norm(s).split(); return (t[0]+' '+t[-1]) if len(t)>=2 else norm(s)

COMMON_LAST={'li','kim','chen','wang','zhang','liu','gao','sun','xie','guo','yang','zhao','wu',
 'huang','jin','he','hu','lee','luo','song','tang','yin','yu','ma','xu','zhou','zhu','yan','shen','qian','patel','smith','das'}

# ---- robust parse: each paper's authors ----
papers=[]   # list of list of norm-name
disp={}
for blk in re.findall(r'<div class="paper-authors">(.*?)</div>', raw, re.DOTALL):
    txt=re.sub(r'<[^>]+>',' ',blk); txt=re.sub(r'\s+',' ',html.unescape(txt)).strip()
    if not txt: continue
    plist=[]
    for part in re.split(r'\)\s*,\s*', txt):          # split between authors (after affiliation close-paren)
        m=re.match(r'(.+?)\s*\((.+)', part)            # Name ( Affiliation
        if not m: continue
        nm=m.group(1).strip().strip(',').strip()
        if len(nm.split())<2: continue
        k=norm(nm); disp.setdefault(k,nm); plist.append(k)
    if plist: papers.append(plist)

# author -> distinct paper count
acount={}
for pl in papers:
    for k in set(pl): acount[k]=acount.get(k,0)+1

def true_count(name):
    k=norm(name); c=collapse(name); t=k.split(); last=t[-1]; fi=t[0][0]
    rare=last not in COMMON_LAST
    n=0
    for pl in papers:
        for pk in pl:
            if pk==k or pk==c:
                n+=1; break
            if rare:
                pt=pk.split()
                if pt[-1]==last and pt[0][0]==fi:   # nickname/initial only for rare surnames
                    n+=1; break
    return n

# ---- data.js current ISCA members ----
iscab=src[src.index('\nisca: ['):src.index('\nasplos: [')]
cur={}
for m in re.finditer(r'name:"([^"]+)",total:(\d+),y:\{([^}]*)\}', iscab):
    h=re.search(r'2026:(\d+)',m.group(3)); cur[m.group(1)]=(int(m.group(2)), int(h.group(1)) if h else 0)
cvb=src[src.index('crossvenue: {'):src.index('toppicks_papers:')]
cv_isca={}
for m in re.finditer(r'"([^"]+)":\s*\{([^}]*)\}', cvb):
    mi=re.search(r'isca:(\d+)',m.group(2));
    if mi: cv_isca[norm(m.group(1))]=int(mi.group(1))
hofnorm={norm(n) for n in cur}

print("=== (A) members whose TRUE 2026 != data.js (need fixing) ===")
for name,(tot,c26) in cur.items():
    t=true_count(name)
    if t!=c26:
        print(f"  {name}: {c26} -> {t}   (total {tot} -> {tot-c26+t})")

print("\n=== (B) NON-HoF authors reaching 8+ (crossvenue isca + true 2026) ===")
for k,cnt in sorted(acount.items(), key=lambda x:-x[1]):
    if k in hofnorm: continue
    cv=cv_isca.get(k)
    if cv is not None and cv+cnt>=8:
        print(f"  {disp[k]}: cv_isca {cv} + {cnt} = {cv+cnt}  ENTERS")
    elif cv is not None and cv+cnt>=6:
        print(f"  {disp[k]}: cv_isca {cv} + {cnt} = {cv+cnt}  near")

print("\n=== (C) NON-HoF, no crossvenue, 2+ papers (possible missed seniors -> DBLP) ===")
for k,cnt in sorted(acount.items(), key=lambda x:-x[1]):
    if k in hofnorm or k in cv_isca: continue
    if cnt>=2: print(f"  {disp[k]}: {cnt} papers")
