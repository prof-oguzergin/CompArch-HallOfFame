# -*- coding: utf-8 -*-
"""One-off patch for the October 2026 redesign: light/dark themes, Inter + Source Serif 4, neutral chrome,
venue colours only in the data, rank badges instead of emoji. Keeps every data feature as it was."""
import re
P = "index.html"
s = open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    c = s.count(old)
    assert c == count, (c, old[:90])
    s = s.replace(old, new)

# ---------- heatmap ramp variables (validated: dataviz validator + OKLab checks, see CLAUDE.md) ----------
DARK = {
    "isca": (["#2d605d", "#347a6d", "#3b957e", "#42af8e", "#49ca9f"], "llddd"),
    "micro": (["#594c93", "#6955ac", "#795fc4", "#8a69dd", "#9b73f7"], "lllDd"),
    "asplos": (["#844258", "#a04960", "#bc5068", "#d8576f", "#f65e78"], "lllDd"),
    "hpca": (["#36578c", "#3e66a6", "#4675c0", "#4e84db", "#5694f7"], "lllDd"),
    "toppicks": (["#625540", "#846c42", "#aa8445", "#d19d47", "#f8b74a"], "llddd"),
    "hm": (["#4c586a", "#606c7e", "#748193", "#8b97aa", "#a1aec1"], "llddd"),
}
LIGHT = {
    "isca": (["#8cc1b2", "#6baf9c", "#4a9e86", "#278b6f", "#047857"], "ddddl"),
    "micro": (["#c6abf0", "#b28deb", "#9d6fe6", "#874fe0", "#6d28d9"], "dddll"),
    "asplos": (["#e6a5b5", "#de869c", "#d56580", "#cb4163", "#be123c"], "dddll"),
    "hpca": (["#a2b6ef", "#839eea", "#6385e4", "#416ade", "#1d4ed8"], "dddll"),
    "toppicks": (["#dcae8b", "#d2986b", "#c8814b", "#be6b2b", "#b45309"], "ddddl"),
    "hm": (["#b0b6bf", "#949ca8", "#798391", "#5f6b7c", "#475569"], "dddll"),
}
def ramp_vars(R):
    out = []
    for v, (cols, inks) in R.items():
        out.append(" ".join(f"--{v}-{i+1}:{c}; --{v}-{i+1}-i:{'#ffffff' if inks[i] == 'l' else '#000000'};"
                            for i, c in enumerate(cols)))
    return "\n            ".join(out)
RAMP_RULES = "\n        ".join(
    [f".h{k} {{ background: var(--hm-{k}); color: var(--hm-{k}-i); }}" for k in range(1, 6)] +
    [" ".join(f".{v} .h{k} {{ background: var(--{v}-{k}); color: var(--{v}-{k}-i); }}" for k in range(1, 6))
     for v in ["isca", "micro", "asplos", "hpca", "toppicks"]])

CSS = r"""    <style>
        /* ---------- theme tokens ---------- */
        :root, :root[data-theme="dark"] {
            color-scheme: dark;
            --bg: #0b1120; --surface: #111a2b; --surface2: #1a2438; --border: #26324b; --row-line: #1c2639;
            --text: #e6e9ef; --text-muted: #9aa5b8; --text-faint: #6b778c;
            --accent: #f2b544; --gold: #f2b544; --gold-light: #f6c76b;
            --accent-hpca: #6aa5f8; --accent-micro: #a78bfa; --accent-isca: #3fcf9b; --accent-asplos: #fb7185; --accent-toppicks: #f2b544;
            --grid: rgba(255,255,255,0.07); --hover: rgba(255,255,255,0.035); --highlight: rgba(242,181,68,0.08);
            --rk1: #e3b341; --rk2: #c0c7d1; --rk3: #cd8a5a;
            --cite-500: #f6c76b; --cite-200: #fde68a; --cite-100: #6ee7b7; --cite-50: #93c5fd;
            @@DARK@@
        }
        :root[data-theme="light"] {
            color-scheme: light;
            --bg: #f5f6f8; --surface: #ffffff; --surface2: #f0f2f5; --border: #e1e5eb; --row-line: #edf0f4;
            --text: #111827; --text-muted: #556070; --text-faint: #8b95a5;
            --accent: #a15c07; --gold: #a15c07; --gold-light: #92400e;
            --accent-hpca: #1d4ed8; --accent-micro: #6d28d9; --accent-isca: #047857; --accent-asplos: #be123c; --accent-toppicks: #a15c07;
            --grid: rgba(17,24,39,0.08); --hover: rgba(17,24,39,0.035); --highlight: rgba(217,119,6,0.08);
            --rk1: #e3b341; --rk2: #c9cfd8; --rk3: #d49a6a;
            --cite-500: #a15c07; --cite-200: #b45309; --cite-100: #047857; --cite-50: #1d4ed8;
            @@LIGHT@@
        }
        :root { --maxw: 1680px; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; font-size: 15px; background: var(--bg); color: var(--text); line-height: 1.55; -webkit-font-smoothing: antialiased; }
        a { color: var(--accent); }

        /* ---------- header ---------- */
        .site-head { background: var(--surface); border-bottom: 1px solid var(--border); }
        .head-inner { max-width: var(--maxw); margin: 0 auto; padding: 1.7rem 1.25rem 1.3rem; display: flex; gap: 1rem; align-items: flex-start; justify-content: space-between; }
        .site-head h1 { font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif; font-weight: 600; font-size: 2.15rem; line-height: 1.15; letter-spacing: -0.01em; }
        .lede { color: var(--text-muted); margin-top: 0.45rem; font-size: 1rem; max-width: 70ch; }
        .meta { color: var(--text-muted); margin-top: 0.55rem; font-size: 0.85rem; }
        .meta a { text-decoration: none; } .meta a:hover { text-decoration: underline; }
        .meta .sep { margin: 0 0.4rem; color: var(--text-faint); }
        .theme-toggle { flex: none; width: 38px; height: 38px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface2); color: var(--text); display: grid; place-items: center; cursor: pointer; }
        .theme-toggle:hover { border-color: var(--accent); }
        .theme-toggle:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
        .theme-toggle svg { width: 18px; height: 18px; }
        :root[data-theme="dark"] .icon-moon, :root[data-theme="light"] .icon-sun { display: none; }

        .container { max-width: var(--maxw); margin: 0 auto; padding: 0 1.25rem 1rem; }
        .summary { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.6rem 1.5rem; margin: 1.1rem 0 0.2rem; }
        .stats-bar { display: flex; gap: 1.6rem; flex-wrap: wrap; }
        .stat-item { display: flex; align-items: baseline; gap: 0.45rem; }
        .stat-number { font-size: 1.3rem; font-weight: 700; font-variant-numeric: tabular-nums; }
        .stat-label { font-size: 0.88rem; color: var(--text-muted); }

        .updates-toggle { background: none; border: 1px solid var(--border); border-radius: 8px; color: var(--text-muted); font: inherit; font-size: 0.85rem; padding: 0.35rem 0.75rem; cursor: pointer; }
        .updates-toggle:hover { color: var(--text); border-color: var(--accent); }
        .updates-toggle .arrow { display: inline-block; transition: transform 0.2s; font-size: 0.7rem; margin-left: 0.3rem; }
        .updates-toggle.open .arrow { transform: rotate(90deg); }
        .updates-list { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
        .updates-list.open { max-height: 3000px; }
        .updates-list ul { list-style: none; padding: 0.6rem 0 0.2rem; max-width: 900px; }
        .updates-list li { font-size: 0.85rem; color: var(--text-muted); padding: 0.4rem 0; border-bottom: 1px solid var(--row-line); }
        .updates-list li:last-child { border-bottom: none; }
        .updates-list .upd-date { color: var(--text); font-weight: 600; margin-right: 0.6rem; font-variant-numeric: tabular-nums; }

        /* ---------- tabs and controls ---------- */
        .tabs { display: flex; gap: 0.15rem; border-bottom: 1px solid var(--border); margin-top: 1.1rem; overflow-x: auto; scrollbar-width: none; }
        .tabs::-webkit-scrollbar { display: none; }
        .tab { flex: none; display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.65rem 0.9rem; border: 0; background: none; color: var(--text-muted); font: inherit; font-size: 0.93rem; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; white-space: nowrap; }
        .tab:hover { color: var(--text); }
        .tab.active { color: var(--text); font-weight: 600; border-bottom-color: var(--accent); }
        .tab:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; border-radius: 6px; }
        .tab .badge { font-size: 0.72rem; font-weight: 500; color: var(--text-muted); background: var(--surface2); border: 1px solid var(--border); border-radius: 999px; padding: 0 0.45rem; }
        .dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
        .dot.isca { background: var(--accent-isca); } .dot.micro { background: var(--accent-micro); } .dot.asplos { background: var(--accent-asplos); }
        .dot.hpca { background: var(--accent-hpca); } .dot.toppicks { background: var(--accent-toppicks); } .dot.hm { background: var(--text-faint); }

        .controls { display: flex; gap: 0.6rem; margin: 0.9rem 0; flex-wrap: wrap; align-items: center; }
        .search-box { flex: 1; min-width: 200px; padding: 0.55rem 0.8rem 0.55rem 2.1rem; border: 1px solid var(--border); border-radius: 8px; color: var(--text); font: inherit; font-size: 0.92rem;
            background: var(--surface) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238b95a5' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E") no-repeat 0.7rem center / 15px; }
        .search-box:focus, #instFilter:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--highlight); }
        .search-box::placeholder { color: var(--text-muted); }
        #instFilter { padding: 0.55rem 0.8rem; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text); font: inherit; font-size: 0.88rem; min-width: 170px; cursor: pointer; }
        .controls label { color: var(--text-muted); font-size: 0.85rem; display: flex; align-items: center; gap: 0.35rem; cursor: pointer; }
        .controls input[type="checkbox"] { accent-color: var(--accent); }

        .conf-info { color: var(--text-muted); font-size: 0.88rem; margin: 0 0 0.75rem; max-width: 120ch; }
        .conf-info strong { color: var(--text); font-weight: 600; }
        .conf-info a { text-decoration: none; } .conf-info a:hover { text-decoration: underline; }
        .note-box { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 0.6rem 0.85rem; margin-bottom: 0.75rem; font-size: 0.88rem; color: var(--text-muted); }
        .tab-panel { display: none; }
        .tab-panel.active { display: block; }
        .tab-panel h3 { color: var(--text) !important; font-weight: 600; font-size: 1.02rem !important; }
        .hoc-toggle { background: none; border: 1px solid var(--border); border-radius: 8px; color: var(--text); font: inherit; font-size: 0.92rem; font-weight: 600; padding: 0.5rem 0.9rem; cursor: pointer; margin: 1rem 0 0.4rem; }
        .hoc-toggle:hover { border-color: var(--accent); }
        .hoc-arrow { display: inline-block; transition: transform 0.2s; margin-left: 0.3rem; color: var(--text-muted); }
        .hoc-toggle.open .hoc-arrow { transform: rotate(90deg); }

        /* ---------- heatmap tables ---------- */
        .heatmap-wrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
        .heatmap-wrap.sticky-scroll { max-height: 78vh; overflow-y: auto; }
        .heatmap { border-collapse: collapse; font-size: 0.76rem; width: max-content; min-width: 100%; font-variant-numeric: tabular-nums; }
        .heatmap thead { position: sticky; top: 0; z-index: 2; }
        .heatmap th { background: var(--surface2); padding: 0.35rem 0.25rem; font-weight: 600; color: var(--text-muted); white-space: nowrap; text-align: center; }
        .heatmap th.name-col { text-align: left; padding-left: 0.6rem; min-width: 160px; position: sticky; left: var(--l1, 32px); z-index: 3; background: var(--surface2); }
        .heatmap th.rank-col { width: 34px; position: sticky; left: 0; z-index: 3; background: var(--surface2); }
        .heatmap th.total-col { width: 42px; position: sticky; left: var(--l2, 200px); z-index: 3; background: var(--surface2); box-shadow: inset -1px 0 0 var(--border); }
        .heatmap th.year-col { width: 24px; font-size: 0.66rem; font-weight: 500; writing-mode: vertical-rl; text-orientation: mixed; padding: 0.4rem 0.15rem; height: 50px; }
        .heatmap td { padding: 0.24rem 0.25rem; text-align: center; border-bottom: 1px solid var(--row-line); }
        .heatmap td.name-cell { text-align: left; padding-left: 0.6rem; white-space: nowrap; font-weight: 500; font-size: 0.82rem; position: sticky; left: var(--l1, 32px); z-index: 1; background: var(--surface); }
        .heatmap td.rank-cell { color: var(--text-muted); font-weight: 600; font-size: 0.72rem; position: sticky; left: 0; z-index: 1; background: var(--surface); }
        .heatmap td.total-cell { font-weight: 700; font-size: 0.82rem; color: var(--text); position: sticky; left: var(--l2, 200px); z-index: 1; background: var(--surface); box-shadow: inset -1px 0 0 var(--border); }
        .heatmap td.year-cell { font-size: 0.7rem; font-weight: 600; min-width: 22px; }
        .heatmap tr:hover td.h0 { background: var(--hover); }
        .heatmap tr:hover td.name-cell, .heatmap tr:hover td.rank-cell, .heatmap tr:hover td.total-cell { background: var(--surface2); }
        @media (min-width: 769px) { .heatmap-wrap.venue-scroll { max-height: calc(100vh - 140px); overflow: auto; } }
        .hm-legend { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; font-size: 0.8rem; color: var(--text-muted); margin: 0 0 0.45rem; }
        .hm-legend .sw { display: inline-block; min-width: 24px; text-align: center; font-size: 0.7rem; font-weight: 600; border-radius: 3px; padding: 0 4px; }
        .hm-legend .sw:first-of-type { margin-left: 4px; }
        .no-results { text-align: center !important; color: var(--text-muted); font-style: italic; padding: 1rem !important; }

        /* Heatmap colours: one hue per venue, five steps for 1, 2, 3, 4 and 5+ papers in a year, separate
           ramps for the dark and the light theme. Lightness and saturation both move with the count, 5+ is
           the most vivid; step 1 clears the surface at 2:1, cell text (white or black) is >= 4.5:1 and
           neighbouring steps differ by OKLab deltaE >= 0.05 (the numbers in the cells carry the value). */
        .h0 { color: transparent; } .h5 { font-weight: 800; }
        @@RULES@@

        /* ---------- simple tables (Combined, Top Picks, acceptance) ---------- */
        .simple-table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
        .simple-table th { background: var(--surface2); padding: 0.55rem 0.7rem; text-align: left; font-size: 0.78rem; font-weight: 600; color: var(--text-muted); cursor: pointer; user-select: none; position: sticky; top: 0; z-index: 2; white-space: nowrap; border-bottom: 1px solid var(--border); }
        .simple-table th:hover { color: var(--text); }
        .simple-table th[data-sort] { text-align: right; }
        .simple-table th[data-sort="name"] { text-align: left; }
        .simple-table th:first-child { text-align: center; }
        .simple-table th.sorted { color: var(--text); box-shadow: inset 0 -2px 0 var(--accent); }
        .simple-table th.sorted::after { content: ' \25BE'; color: var(--accent); }
        .simple-table th.sorted.asc::after { content: ' \25B4'; }
        .simple-table td { padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--row-line); font-size: 0.9rem; }
        .simple-table td.count { font-weight: 500; text-align: right; }
        .simple-table td.count.tot { font-weight: 700; }
        .simple-table td.count.m { font-weight: 650; }
        .count.m.v-isca { color: var(--accent-isca); } .count.m.v-micro { color: var(--accent-micro); }
        .count.m.v-asplos { color: var(--accent-asplos); } .count.m.v-hpca { color: var(--accent-hpca); }
        .count.tp { color: var(--accent-toppicks); font-weight: 600; }
        .count.nm { color: var(--text-muted); font-weight: 400; } .count.zero { color: var(--text-faint); font-weight: 400; }
        .simple-table tr:hover td { background: var(--hover); }
        .highlight td { background: var(--highlight) !important; }
        .vdots { white-space: nowrap; }
        .vd { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
        .vd.v-isca { background: var(--accent-isca); } .vd.v-micro { background: var(--accent-micro); }
        .vd.v-asplos { background: var(--accent-asplos); } .vd.v-hpca { background: var(--accent-hpca); }
        .vd.off { background: transparent !important; box-shadow: inset 0 0 0 1.5px var(--border); }
        .nm-link { color: var(--text); text-decoration: none; } .nm-link:hover { color: var(--accent); text-decoration: underline; }
        .inst { font-size: 0.74rem; color: var(--text-muted); margin-left: 0.3rem; }
        .rk { display: inline-flex; align-items: center; justify-content: center; width: 21px; height: 21px; border-radius: 50%; font-size: 0.7rem; font-weight: 700; color: #1f1a10; vertical-align: middle; }
        .rk1 { background: var(--rk1); } .rk2 { background: var(--rk2); } .rk3 { background: var(--rk3); }
        .tp-badge { display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700; }
        .tp-badge.tp { background: var(--highlight); color: var(--accent); }
        .tp-badge.hm { background: var(--surface2); color: var(--text-muted); }
        .tp-authors { font-size: 0.82rem; color: var(--text-muted); }

        .ar-btn { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; color: var(--text-muted); font: inherit; font-size: 0.85rem; padding: 0.4rem 0.8rem; cursor: pointer; }
        .ar-btn:hover { color: var(--text); }
        .ar-btn.active { color: var(--text); border-color: var(--accent); background: var(--highlight); }

        footer { max-width: var(--maxw); margin: 2rem auto 0; padding: 1.4rem 1.25rem 2rem; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.82rem; text-align: center; }
        footer p + p { margin-top: 0.3rem; }
        footer a { text-decoration: none; } footer a:hover { text-decoration: underline; }
        .quip { font-style: italic; color: var(--text-faint); }

        @media (max-width: 768px) {
            .head-inner { padding: 1.1rem 1rem 0.9rem; }
            .site-head h1 { font-size: 1.45rem; }
            .lede { font-size: 0.9rem; }
            .meta { font-size: 0.8rem; }
            .container { padding: 0 0.75rem 1rem; }
            .stats-bar { gap: 1rem; } .stat-number { font-size: 1.1rem; } .stat-label { font-size: 0.8rem; }
            .tab { padding: 0.55rem 0.65rem; font-size: 0.86rem; }
            /* On narrow screens the 50+ column year heatmap overflows and the
               sticky rank/name cells misalign with the rest of the row. Hide the
               per-year columns and show just rank + name + total, which stays aligned. */
            .heatmap:not(.acc-table) .year-col, .heatmap:not(.acc-table) td.year-cell { display: none; }
            .heatmap td.rank-cell, .heatmap td.name-cell, .heatmap td.total-cell,
            .heatmap th.rank-col, .heatmap th.name-col, .heatmap th.total-col { position: static; box-shadow: none; }
            .hm-legend { display: none; }
            .heatmap td.total-cell { text-align: right; padding-right: 0.9rem; }
        }
    </style>"""
CSS = CSS.replace("@@DARK@@", ramp_vars(DARK)).replace("@@LIGHT@@", ramp_vars(LIGHT)).replace("@@RULES@@", RAMP_RULES)
a = s.index("    <style>"); b = s.index("    </style>", a) + len("    </style>")
s = s[:a] + CSS + s[b:]

# fonts + theme init before the stylesheet (no flash of the wrong theme)
rep('    <meta name="theme-color" content="#0f172a">',
    '''    <meta name="theme-color" content="#0b1120">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,600&display=swap" rel="stylesheet">
    <script>
      // theme: saved choice, otherwise the system setting
      (function () { var t; try { t = localStorage.getItem('theme'); } catch (e) {}
        if (t !== 'light' && t !== 'dark') t = window.matchMedia && matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', t); })();
    </script>''')

# ---------- header ----------
a = s.index('<div class="hero">'); b = s.index('<div class="container">')
hero_old = s[a:b]
email = re.search(r'mailto:([^"]+)"', hero_old).group(1)
s = s[:a] + f'''<header class="site-head">
    <div class="head-inner">
        <div class="head-text">
            <h1>Computer Architecture Hall of Fame</h1>
            <p class="lede">Researchers with eight or more papers at ISCA, MICRO, ASPLOS and HPCA, together with the complete list of IEEE Micro Top Picks.</p>
            <p class="meta">Compiled by <a href="https://oguzergin.net">O&#287;uz Ergin</a><span class="sep">&middot;</span><a href="https://dblp.org/pid/48/389.html">DBLP</a><span class="sep">&middot;</span><a href="mailto:{email}">{email}</a><span class="sep">&middot;</span>Counts verified against DBLP</p>
        </div>
        <button class="theme-toggle" id="themeToggle" type="button" aria-label="Switch theme" title="Switch between light and dark theme">
            <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>
            <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.3A8.5 8.5 0 0 1 9.7 3.5a8.5 8.5 0 1 0 10.8 10.8z"/></svg>
        </button>
    </div>
</header>
''' + s[b:]
rep('''    <div class="stats-bar" id="statsBar"></div>
    <div class="updates-bar">
        <button class="updates-toggle" onclick="this.classList.toggle('open');document.getElementById('updatesList').classList.toggle('open')">Recent Updates <span class="arrow">&#9658;</span></button>
        <div class="updates-list" id="updatesList"></div>
    </div>''',
'''    <div class="summary">
        <div class="stats-bar" id="statsBar"></div>
        <button class="updates-toggle" type="button" onclick="this.classList.toggle('open');document.getElementById('updatesList').classList.toggle('open')">Recent updates <span class="arrow">&#9658;</span></button>
    </div>
    <div class="updates-list" id="updatesList"></div>''')

# ---------- tabs ----------
for v, label in [("isca", "ISCA"), ("micro", "MICRO"), ("asplos", "ASPLOS"), ("hpca", "HPCA"), ("toppicks", "Top Picks"), ("hm", "Honorable Mentions")]:
    rep(f'<button class="tab" data-tab="{v}">{label}</button>', f'<button class="tab" data-tab="{v}"><span class="dot {v}"></span>{label}</button>')
rep('placeholder="Search by name..."', 'placeholder="Search researchers"')
rep('<select id="instFilter" style="padding:0.5rem 0.8rem;border:1px solid var(--surface2);border-radius:6px;background:var(--surface);color:var(--text);font-size:0.85rem;min-width:160px;cursor:pointer">',
    '<select id="instFilter" aria-label="Filter by institution">')
rep('<label><input type="checkbox" id="highlightMulti" checked> Highlight 4-venue</label>',
    '<label><input type="checkbox" id="highlightMulti" checked> Highlight researchers in all four</label>')
# Combined header: neutral colours for the Scholar columns
for x in ['style="width:45px;cursor:pointer;color:var(--gold)"', 'style="width:65px;cursor:pointer;color:var(--gold)"',
          'style="width:50px;cursor:pointer;color:var(--gold)"']:
    s = s.replace(x, x.replace(";color:var(--gold)", ""))
rep('<th data-sort="vc" onclick="sortCombined(\'vc\')" style="cursor:pointer;text-align:left">HoF Venues</th>',
    '<th data-sort="vc" onclick="sortCombined(\'vc\')" style="cursor:pointer;text-align:left" title="Halls of Fame: ISCA, MICRO, ASPLOS, HPCA">Halls of Fame</th>')
# panel-local style blocks for the citation toggles move to the stylesheet
s = re.sub(r'\s*\.hoc-toggle \{[^}]*\}\s*\.hoc-toggle:hover \{[^}]*\}\s*\.hoc-arrow \{[^}]*\}\s*\.hoc-toggle\.open \.hoc-arrow \{[^}]*\}', '', s, count=1)
rep('🏆 Hall of Citations — Top 20 Most-Cited Top Picks', 'Hall of Citations: the 20 most-cited Top Picks')
rep('🏆 Hall of Citations — Top 20 Most-Cited Honorable Mentions', 'Hall of Citations: the 20 most-cited Honorable Mentions')

# ---------- footer ----------
a = s.index("<footer>"); b = s.index("</footer>") + len("</footer>")
foot = s[a:b]
assert 'id="lastUpdated"' in foot
s = s[:a] + '''<footer>
    <p>Computer Architecture Hall of Fame &middot; compiled by <a href="https://oguzergin.net" target="_blank">O&#287;uz Ergin</a>, University of Sharjah &middot; <span class="quip">still working on that 8th paper</span></p>
    <p>Sources: <a href="https://ieeetcca.org/awards/hpca-hall-of-fame/">HPCA</a> &middot; <a href="https://www.sigmicro.org/awards/microhof.php">MICRO</a> &middot; <a href="https://pages.cs.wisc.edu/~arch/www/iscabibhall.html">ISCA</a> &middot; <a href="https://liberty.princeton.edu/Fame/ASPLOS/">ASPLOS</a> &middot; <a href="https://dblp.org">DBLP</a></p>
    <p>Last updated: <span id="lastUpdated">5 Oct 2026</span> &middot; <a href="https://github.com/prof-oguzergin/CompArch-HallOfFame">GitHub</a></p>
</footer>''' + s[b:]

# ---------- JS ----------
rep('''    const inst = showInst && a?.inst ? ` <span style="font-size:0.7rem;color:var(--text-muted)">${a.inst}</span>` : '';
    return `<a href="${url}" target="_blank" style="color:var(--text);text-decoration:none" onmouseover="this.style.color='var(--gold)'" onmouseout="this.style.color='var(--text)'">${name}</a>${inst}`;''',
'''    const inst = showInst && a?.inst ? `<span class="inst">${a.inst}</span>` : '';
    return `<a class="nm-link" href="${url}" target="_blank" rel="noopener">${name}</a>${inst}`;''')
rep(r"""function medal(r, tied) {
    const t = tied ? 'Tied for ' : '';
    if (r===1) return `<span class="medal" title="${t}1st">\u{1F947}</span>`;
    if (r===2) return `<span class="medal" title="${t}2nd">\u{1F948}</span>`;
    if (r===3) return `<span class="medal" title="${t}3rd">\u{1F949}</span>`;
    return tied ? `<span title="Tied">=${r}</span>` : r;
}""",
r"""function medal(r, tied) {
    if (r <= 3) return `<span class="rk rk${r}" title="${tied ? 'Tied for ' : ''}${['', '1st', '2nd', '3rd'][r]}">${r}</span>`;
    return tied ? `<span title="Tied">=${r}</span>` : r;
}""")
rep('''        const badges = [];
        if (d.isca>=8) badges.push('<span title="ISCA" style="color:var(--accent-isca)">★</span>');
        if (d.micro>=8) badges.push('<span title="MICRO" style="color:var(--accent-micro)">★</span>');
        if (d.asplos>=8) badges.push('<span title="ASPLOS" style="color:var(--accent-asplos)">★</span>');
        if (d.hpca>=8) badges.push('<span title="HPCA" style="color:var(--accent-hpca)">★</span>');''',
'''        const vcls = v => d[v] >= 8 ? `m v-${v}` : (d[v] ? 'nm' : 'zero');
        const dots = ['isca','micro','asplos','hpca'].map(v => `<span class="vd v-${v}${d[v] >= 8 ? '' : ' off'}" title="${VLABEL[v]}${d[v] >= 8 ? ' Hall of Fame' : ': ' + (d[v] || 0) + ' papers'}"></span>`).join('');''')
rep('''            <td class="count">${d.total}</td>
            <td class="count" style="color:var(--accent-isca)">${d.isca||'-'}</td>
            <td class="count" style="color:var(--accent-micro)">${d.micro||'-'}</td>
            <td class="count" style="color:var(--accent-asplos)">${d.asplos||'-'}</td>
            <td class="count" style="color:var(--accent-hpca)">${d.hpca||'-'}</td>
            <td class="count" style="color:var(--accent-toppicks)">${d.tp||'-'}</td>
            <td class="count" style="color:var(--text-muted)">${d.hm||'-'}</td>
            <td class="count" style="color:var(--gold)">${gsLink}${d.h!=null?d.h:'-'}${gsEnd}</td>
            <td class="count" style="color:var(--gold)">${fmtCites(d.c)}</td>
            <td class="count" style="color:var(--gold-light)">${d.b100!=null?d.b100:'-'}</td>
            <td class="count" style="color:var(--gold-light)">${d.b1000!=null?d.b1000:'-'}</td>
            <td>${badges.join('')}</td></tr>`;''',
'''            <td class="count tot">${d.total}</td>
            <td class="count ${vcls('isca')}">${d.isca||'-'}</td>
            <td class="count ${vcls('micro')}">${d.micro||'-'}</td>
            <td class="count ${vcls('asplos')}">${d.asplos||'-'}</td>
            <td class="count ${vcls('hpca')}">${d.hpca||'-'}</td>
            <td class="count ${d.tp ? 'tp' : 'zero'}">${d.tp||'-'}</td>
            <td class="count ${d.hm ? 'nm' : 'zero'}">${d.hm||'-'}</td>
            <td class="count">${gsLink}${d.h!=null?d.h:'-'}${gsEnd}</td>
            <td class="count">${fmtCites(d.c)}</td>
            <td class="count nm">${d.b100!=null?d.b100:'-'}</td>
            <td class="count nm">${d.b1000!=null?d.b1000:'-'}</td>
            <td class="vdots">${dots}</td></tr>`;''')
rep('''    document.getElementById('statsBar').innerHTML = `
        <div class="stat-item"><div class="stat-number">${n}</div><div class="stat-label">Researchers</div></div>
        <div class="stat-item"><div class="stat-number">5</div><div class="stat-label">Venues</div></div>
        <div class="stat-item"><div class="stat-number">${four}</div><div class="stat-label">In All 4 HoFs</div></div>`;''',
'''    const tp = (DATA.toppicks_papers || []).filter(p => p.type === 'TP').length;
    document.getElementById('statsBar').innerHTML = `
        <div class="stat-item"><span class="stat-number">${n}</span><span class="stat-label">researchers</span></div>
        <div class="stat-item"><span class="stat-number">${four}</span><span class="stat-label">in all four Halls of Fame</span></div>
        <div class="stat-item"><span class="stat-number">${tp}</span><span class="stat-label">Top Picks papers</span></div>`;''')
rep('''function citeColor(c) {
    if (c === null || c === undefined) return '';
    if (c >= 500) return 'color:#fbbf24';      // gold
    if (c >= 200) return 'color:#fde68a';      // light gold
    if (c >= 100) return 'color:#6ee7b7';      // green
    if (c >= 50) return 'color:#93c5fd';       // blue
    return 'color:var(--text-muted)';
}''',
'''function citeColor(c) {           // theme-aware: the colours are CSS variables
    if (c === null || c === undefined) return '';
    if (c >= 500) return 'color:var(--cite-500)';
    if (c >= 200) return 'color:var(--cite-200)';
    if (c >= 100) return 'color:var(--cite-100)';
    if (c >= 50) return 'color:var(--cite-50)';
    return 'color:var(--text-muted)';
}''')
rep('''function rateColor(r) {
    if (r === null) return '';
    if (r < 15) return 'background:rgba(239,68,68,0.35);color:#fca5a5';
    if (r < 18) return 'background:rgba(245,158,11,0.3);color:#fcd34d';
    if (r < 22) return 'background:rgba(234,179,8,0.25);color:#fde68a';
    if (r < 26) return 'background:rgba(16,185,129,0.25);color:#6ee7b7';
    return 'background:rgba(16,185,129,0.4);color:#6ee7b7';
}
function subColor(s, maxSub) {
    if (s === null) return '';
    const t = Math.min(s / maxSub, 1);
    const a = (0.1 + t * 0.45).toFixed(2);
    return `background:rgba(59,130,246,${a});color:#93c5fd`;
}''',
'''// Acceptance tables: one neutral sequential scale (no red/green judgement), theme-aware CSS variables
function rateColor(r) {
    if (r === null) return '';
    const k = r < 15 ? 1 : r < 18 ? 2 : r < 22 ? 3 : r < 26 ? 4 : 5;
    return `background:var(--hm-${k});color:var(--hm-${k}-i)`;
}
function subColor(s, maxSub) {
    if (s === null) return '';
    const k = 1 + Math.min(4, Math.floor(5 * s / (maxSub + 1e-9)));
    return `background:var(--hm-${k});color:var(--hm-${k}-i)`;
}''')
rep('''                legend: { position: 'top', labels: { color: '#94a3b8', font: { size: 11 } } },''',
    '''                legend: { position: 'top', labels: { color: ink, font: { size: 11, family: 'Inter' } } },''')
rep('''                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: {
                    ticks: {
                        color: '#94a3b8',''',
'''                x: { ticks: { color: ink }, grid: { color: grid } },
                y: {
                    ticks: {
                        color: ink,''')
rep('''                    grid: { color: 'rgba(255,255,255,0.05)' },
                    beginAtZero: true''',
'''                    grid: { color: grid },
                    beginAtZero: true''')
rep('''    const venues = ['hpca','micro','isca','asplos'];
    const colors = {hpca:'#3b82f6',micro:'#8b5cf6',isca:'#10b981',asplos:'#f43f5e'};''',
'''    const venues = ['hpca','micro','isca','asplos'];
    const css = getComputedStyle(document.documentElement);
    const ink = css.getPropertyValue('--text-muted').trim(), grid = css.getPropertyValue('--grid').trim();
    const colors = {hpca:'#3b82f6',micro:'#8b5cf6',isca:'#10b981',asplos:'#f43f5e'};''')
# theme toggle (end of script, after accChart exists)
last = s.rindex("</script>")
s = s[:last] + '''
// Theme toggle: saved per browser, redraws the chart in the new colours
function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('theme', t); } catch (e) {}
    const m = document.querySelector('meta[name="theme-color"]');
    if (m) m.setAttribute('content', getComputedStyle(document.documentElement).getPropertyValue('--bg').trim());
    if (accChart) renderAccChart();
}
document.getElementById('themeToggle').addEventListener('click', () =>
    setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));
''' + s[last:]
open(P, "w", encoding="utf-8", newline="").write(s)
print("redesign patch applied")
