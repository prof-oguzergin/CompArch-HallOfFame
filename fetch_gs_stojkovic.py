# -*- coding: utf-8 -*-
"""Fetch GS metrics for a single new member (Jovan Stojkovic). Reuses fetch_gs_all logic."""
import urllib.request, re, time, sys
sys.stdout.reconfigure(encoding='utf-8')
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'})
    with urllib.request.urlopen(req,timeout=25) as r: return r.read().decode('utf-8',errors='ignore')

GID='1BcJ5ZAAAAAJ'
html=fetch(f'https://scholar.google.com/citations?user={GID}&hl=en')
# metrics table: All / Since-year columns -> take 'All' (first number of each row)
nums=re.findall(r'gsc_rsb_std">(\d+)</td>', html)
# order: cites_all, cites_recent, h_all, h_recent, i10_all, i10_recent
if len(nums)>=5:
    cites,h,i10=int(nums[0]),int(nums[2]),int(nums[4])
    print(f'metrics: cites={cites} h={h} i10={i10}')
else:
    print('METRICS PARSE FAILED; raw nums=',nums); sys.exit(1)

# buckets sorted by cited
counts={t:0 for t in (100,200,400,800,1000)}
cstart=0
while True:
    u=f'https://scholar.google.com/citations?user={GID}&hl=en&cstart={cstart}&pagesize=100&view_op=list_works&sortby=cited_by'
    h2=fetch(u)
    cs=[int(x) for x in re.findall(r'class="gsc_a_ac[^"]*"[^>]*>(\d+)</a>',h2)]
    if not cs: break
    for c in cs:
        for t in counts:
            if c>=t: counts[t]+=1
    if min(cs)<100 or len(cs)<100: break
    cstart+=100; time.sleep(2)
bar=[counts[100],counts[200],counts[400],counts[800],counts[1000]]
print(f'bar (100/200/400/800/1000+): {bar}')
print(f'\nDATA.JS LINE:')
print(f'  "Jovan Stojkovic":{{gs:"{GID}",h:{h},i10:{i10},c:{cites},b:{bar}}},')
