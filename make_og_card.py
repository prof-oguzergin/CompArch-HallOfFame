# -*- coding: utf-8 -*-
"""Build og-card.png (1200x630 link-preview image) from data.js.

The strip at the bottom is real data: for each venue, the number of papers that Hall of Fame
members published there each year, binned into the same 5-step colour ramps as the site's
heatmaps. No head counts on the card, so it does not go stale when the lists change.
Rendering: headless Chrome (window 250 px taller than the card, then cropped with PIL).
Run: python make_og_card.py
"""
import json, os, subprocess, sys, time
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "og-card.png")
TMP = os.path.join(os.environ.get("TEMP", HERE), "comparch_og")
os.makedirs(TMP, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

D = json.loads(subprocess.check_output(["node", "-e",
    'const fs=require("fs");const s=fs.readFileSync(process.argv[1],"utf8");'
    'const D=eval("(function(){"+s+"; return DATA;})()");'
    'process.stdout.write(JSON.stringify({hpca:D.hpca,micro:D.micro,isca:D.isca,asplos:D.asplos}))',
    os.path.join(HERE, "data.js")]).decode("utf-8"))

# same ramps as the site's heatmaps: 5+ is the venue accent, lower steps mix it into the surface
RAMP = {
    "isca":   ["#2d605d", "#347a6d", "#3b957e", "#42af8e", "#49ca9f"],
    "micro":  ["#594c93", "#6955ac", "#795fc4", "#8a69dd", "#9b73f7"],
    "asplos": ["#844258", "#a04960", "#bc5068", "#d8576f", "#f65e78"],
    "hpca":   ["#36578c", "#3e66a6", "#4675c0", "#4e84db", "#5694f7"],
}
LABEL = {"isca": "ISCA", "micro": "MICRO", "asplos": "ASPLOS", "hpca": "HPCA"}
Y0, Y1 = 1980, max(int(y) for v in RAMP for e in D[v] for y in e["y"])
rows = []
for v in ["isca", "micro", "asplos", "hpca"]:
    per = {y: sum(e["y"].get(str(y), 0) for e in D[v]) for y in range(Y0, Y1 + 1)}
    top = max(per.values())
    cells = []
    for y in range(Y0, Y1 + 1):
        n = per[y]
        if n == 0:
            cells.append('<i class="c"></i>')
        else:
            k = min(4, int(5 * n / (top + 1e-9)))
            cells.append(f'<i class="c" style="background:{RAMP[v][k]}"></i>')
    rows.append(f'<div class="row"><b style="color:{RAMP[v][3]}">{LABEL[v]}</b>{"".join(cells)}</div>')

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ position:relative; width:1200px; height:630px; background:#0f172a; font-family:'Segoe UI',system-ui,sans-serif; overflow:hidden;
        background-image: radial-gradient(900px 420px at 0% 0%, rgba(245,158,11,0.16), transparent 70%); }}
.wrap {{ position:absolute; left:72px; right:72px; top:58px; bottom:48px; }}
.kicker {{ color:#94a3b8; font-size:21px; letter-spacing:3px; text-transform:uppercase; font-weight:600; }}
h1 {{ margin-top:14px; font-size:82px; line-height:1.0; font-weight:800; letter-spacing:-1px;
      background:linear-gradient(135deg,#f59e0b,#fde68a); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
.chips {{ margin-top:26px; display:flex; gap:12px; }}
.chip {{ font-size:20px; font-weight:700; padding:6px 16px; border-radius:999px; border:2px solid; letter-spacing:1px; }}
.strip {{ position:absolute; left:0; right:0; bottom:46px; }}
.row {{ display:flex; align-items:center; gap:3px; margin-top:5px; }}
.row b {{ width:86px; font-size:15px; letter-spacing:1px; }}
.c {{ display:block; width:18px; height:15px; border-radius:2px; background:#1e293b; }}
.axis {{ display:flex; justify-content:space-between; margin:6px 0 0 89px; color:#64748b; font-size:14px; width:{(Y1 - Y0 + 1) * 21 - 3}px; }}
.foot {{ position:absolute; left:0; right:0; bottom:0; display:flex; justify-content:space-between; color:#94a3b8; font-size:19px; }}
.foot span b {{ color:#f1f5f9; font-weight:600; }}
</style></head><body><div class="wrap">
<div class="kicker">Researchers with 8+ papers at the top venues</div>
<h1>Computer Architecture<br>Hall of Fame</h1>
<div class="chips">
  <span class="chip" style="color:#10b981;border-color:#10b981">ISCA</span>
  <span class="chip" style="color:#a78bfa;border-color:#8b5cf6">MICRO</span>
  <span class="chip" style="color:#fb7185;border-color:#f43f5e">ASPLOS</span>
  <span class="chip" style="color:#60a5fa;border-color:#3b82f6">HPCA</span>
  <span class="chip" style="color:#fbbf24;border-color:#f59e0b">IEEE Micro Top Picks</span>
</div>
<div class="strip">{"".join(rows)}<div class="axis"><span>{Y0}</span><span>{(Y0 + Y1) // 2}</span><span>{Y1}</span></div></div>
<div class="foot"><span>Compiled by <b>Oğuz Ergin</b></span><span>Counts verified against DBLP</span></div>
</div></body></html>"""
src = os.path.join(TMP, "card.html")
open(src, "w", encoding="utf-8").write(html)
shot = os.path.join(TMP, "card_full.png")
if os.path.exists(shot): os.remove(shot)
# PowerShell Start-Process -Wait is the reliable way to wait for headless Chrome on Windows.
# %TEMP% is already an 8.3 path here (C:\Users\ZGAMES~1\...); Start-Process does not quote paths with spaces.
args = ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
        "--user-data-dir=" + os.path.join(TMP, "prof"), "--screenshot=" + shot,
        "--window-size=1200,880", "file:///" + src.replace("\\", "/")]
ps = "Start-Process -FilePath '{}' -ArgumentList {} -Wait".format(CHROME, ",".join("'" + a + "'" for a in args))
subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
for _ in range(40):
    if os.path.exists(shot) and os.path.getsize(shot) > 0: break
    time.sleep(0.5)
Image.open(shot).crop((0, 0, 1200, 630)).save(OUT, optimize=True)
print("written", OUT, os.path.getsize(OUT), "bytes")
