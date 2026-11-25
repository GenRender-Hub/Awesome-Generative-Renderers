#!/usr/bin/env python3
"""Compile GenRender-Survey/figures/metro.tex 1:1 into a native interactive SVG
(docs/assets/metro_interactive.svg + embedded HTML snippet) preserving EVERY exact
coordinate, curve, stem, interchange, fork callout, institution logo, terminal chip,
and Panel (b) monthly surge bar from the original paper's Figure 2."""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

SURVEY = Path("/data/workspace/project/GenRender-Survey")
HUB = Path("/data/workspace/project/Awesome-Generative-Renderers")

# Exact paper palette matching genrender_report.cls & table_symbols.tex
PAL = {
    "grteal": "#315B51",
    "grsea": "#548074",
    "grgold": "#AD803B",
    "grsaffron": "#A97840",
    "grcoral": "#A75246",
    "grplum": "#806886",
    "grblue": "#526F91",
    "grslate": "#293431",
    "grmist": "#EDF1EB",
    "grpaper": "#FAF7EF",
    "grrule": "#D6D0C3",
    "mgeo": "#A391A8",       # grplum!72!white
    "mh3": "#AD803B",        # grgold
    "mfus": "#806886",       # grplum
    "mbr": "#C6B9C9",        # grplum!45!white
    "mctx": "#526F91",       # grblue
    "mxat": "#5A7C74",       # grteal!80!white
    "mtf": "#B9756B",        # grcoral!80!white
    "mnr": "#AEB3B2",        # grslate!38!white
}

CHIP_FILL = {
    "mh3": "#F5EFE6",
    "mfus": "#EFEBF0",
    "mbr": "#F6F3F7",
    "mctx": "#EAEFF4",
    "mxat": "#EAF0EE",
    "mtf": "#F5ECEA",
    "mnr": "#F2F3F3",
    "grblue": "#FFFFFF",
}

def gx(yr: float) -> float:
    if yr < 2023:
        return 3.0 + (yr - 2016.0) * 18.0 / 7.0
    if yr < 2024:
        return 23.2 + (yr - 2023.0) * 11.3
    if yr < 2025:
        return 34.5 + (yr - 2024.0) * 14.0
    if yr < 2026:
        return 48.5 + (yr - 2025.0) * 20.3
    return 71.2 + (yr - 2026.0) * 30.2

def gd(y: int, m: int, d: int) -> float:
    return y + (m - 1) / 12.0 + (d - 1) / 365.0

# TikZ y goes UP (0..141), SVG y goes DOWN: map (x_mm, y_mm) -> (x*10, (141.5 - y)*10)
S = 10.0
H_MM = 141.8
def sx(x_mm: float) -> float: return round(x_mm * S, 1)
def sy(y_mm: float) -> float: return round((H_MM - y_mm) * S, 1)

def load_url_map() -> tuple[dict[str, str], dict[str, str]]:
    cat = json.loads((HUB / "docs/data/catalog.json").read_text(encoding="utf-8"))
    urls, titles = {}, {}
    for p in cat["papers"]:
        urls[p["key"]] = p.get("url", "")
        titles[p["key"]] = p.get("title", "")
    for bp in [SURVEY / "references.bib", SURVEY / "references_extra.bib"]:
        if not bp.exists():
            continue
        txt = bp.read_text(encoding="utf-8")
        for m in re.finditer(r"@\w+\{([^,\s]+),(.*?)\n\}", txt, re.S):
            k, body = m.group(1).strip(), m.group(2)
            if k not in urls or not urls[k]:
                um = re.search(r"\burl\s*=\s*\{([^}]+)\}", body, re.I)
                em = re.search(r"\beprint\s*=\s*\{([^}]+)\}", body, re.I)
                if um:
                    urls[k] = um.group(1).strip()
                elif em:
                    urls[k] = f"https://arxiv.org/abs/{em.group(1).strip()}"
            if k not in titles or not titles[k]:
                tm = re.search(r"\btitle\s*=\s*\{\{?(.*?)\}?\}(?:,|\s*$)", body, re.S | re.I)
                if tm:
                    titles[k] = re.sub(r"\s+", " ", tm.group(1).replace("{", "").replace("}", "")).strip()
    return urls, titles

def clean_lbl(raw: str) -> tuple[str, bool, str]:
    km = re.search(r"\\mc\{([^}]+)\}", raw)
    key = km.group(1) if km else ""
    bold = r"\textbf{" in raw
    txt = re.sub(r"\\mc\{[^}]+\}", "", raw)
    txt = txt.replace(r"\textbf{", "").replace("}", "").replace(r"$\cdot$", "·").replace(r"\ ", " ").replace("\\", "")
    return txt.strip(), bold, key

def build_svg() -> str:
    urls, titles = load_url_map()
    tex = (SURVEY / "figures/metro.tex").read_text(encoding="utf-8")

    out: list[str] = []
    out.append(f'<svg id="metro-exact-svg" class="metro-exact-svg" viewBox="0 0 1612 {int(H_MM*S)}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Figure 2: Four converging lineages and the 2026 surge of Tier-3 generative video renderers">')
    out.append("""<defs>
      <marker id="ma-teal" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0 1L10 5L0 9Z" fill="#315B51"/></marker>
      <marker id="ma-gold" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 1L10 5L0 9Z" fill="#AD803B"/></marker>
      <marker id="ma-plum" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0 1L10 5L0 9Z" fill="#806886"/></marker>
      <marker id="ma-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0 1L10 5L0 9Z" fill="#526F91"/></marker>
    </defs>""")

    # Clean white canvas
    out.append(f'<rect x="0" y="0" width="1612" height="{int(H_MM*S)}" rx="14" fill="#FFFFFF"/>')

    # ---- Title and top legend (y=135.2..139.6) ----
    out.append(f'<text x="{sx(1.0)}" y="{sy(136.7)}" font-size="19.5" font-weight="700" fill="{PAL["grslate"]}">a. Four converging lineages &amp; Late-2026 Tier-3 Generative Renderer Terminal</text>')
    out.append(f'<rect x="{sx(82.0)}" y="{sy(139.8)}" width="{sx(78.2)}" height="{4.6*S}" rx="8.5" fill="#FFFFFF" stroke="{PAL["grrule"]}" stroke-width="1.3"/>')
    # Legend items
    ly = sy(137.5)
    out.append(f'<circle cx="{sx(84.4)}" cy="{ly}" r="5.5" fill="#fff" stroke="{PAL["grslate"]}" stroke-width="2.2"/><text x="{sx(85.8)}" y="{ly+5}" font-size="14.5" fill="{PAL["grslate"]}">paper</text>')
    out.append(f'<rect x="{sx(93.1)}" y="{ly-5}" width="10.5" height="10.5" rx="2" fill="#fff" stroke="{PAL["grslate"]}" stroke-width="2.2"/><text x="{sx(94.9)}" y="{ly+5}" font-size="14.5" fill="{PAL["grslate"]}">product / workflow</text>')
    out.append(f'<circle cx="{sx(113.2)}" cy="{ly}" r="7" fill="#fff" stroke="{PAL["grslate"]}" stroke-width="2.5"/><circle cx="{sx(113.2)}" cy="{ly}" r="2.6" fill="{PAL["grslate"]}"/><text x="{sx(114.8)}" y="{ly+5}" font-size="14.5" fill="{PAL["grslate"]}">one work on two lines</text>')
    out.append(f'<line x1="{sx(134.4)}" y1="{ly}" x2="{sx(137.4)}" y2="{ly}" stroke="{PAL["grplum"]}" stroke-width="6"/><line x1="{sx(134.5)}" y1="{ly}" x2="{sx(137.3)}" y2="{ly}" stroke="#fff" stroke-width="1.8" stroke-dasharray="4 3"/><text x="{sx(138.2)}" y="{ly+5}" font-size="14.5" fill="{PAL["grslate"]}">streamed / stateful (3b)</text>')

    # ---- Era headers & background bands ----
    eras = [
        (0.8, 20.7, "#FAF7EF", "#D6D0C3", "I. 2016–22", PAL["grslate"]),
        (22.2, 47.3, "#EDF1EB", "#9AB5AE", "II. 2023–25 · Controllable Priors & R2V", PAL["grslate"]),
        (70.2, 20.4, "#F4F0F5", "#B8A8BC", "IIIa. Jan–Jul 2026", PAL["grslate"]),
        (92.2, 67.8, "#EFE9F1", "#9C84A2", "IIIb. Aug – Mid-Nov 2026 · Tier-3 Generative Renderer Terminal", "#5F4964"),
    ]
    for x0, w, fill, stroke, lbl, tcol in eras:
        out.append(f'<rect x="{sx(x0)}" y="{sy(131.6)}" width="{sx(w)}" height="{4.6*S}" rx="8.5" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>')
        out.append(f'<text x="{sx(x0+w/2)}" y="{sy(128.6)}" text-anchor="middle" font-size="15.5" font-weight="700" fill="{tcol}">{escape(lbl)}</text>')

    # Era background bands (y=30.7..126.0)
    out.append(f'<rect x="{sx(0.8)}" y="{sy(126.0)}" width="{sx(20.7)}" height="{95.3*S}" rx="11" fill="#FBF9F4"/>')
    out.append(f'<rect x="{sx(22.2)}" y="{sy(126.0)}" width="{sx(47.3)}" height="{95.3*S}" rx="11" fill="#F2F6F1"/>')
    out.append(f'<rect x="{sx(70.2)}" y="{sy(126.0)}" width="{sx(20.4)}" height="{95.3*S}" rx="11" fill="#F8F6F9"/>')
    out.append(f'<rect x="{sx(92.2)}" y="{sy(126.0)}" width="{sx(67.8)}" height="{95.3*S}" rx="12" fill="#F5F1F6" stroke="#CCBECD" stroke-width="1.3"/>')

    # ---- Interchanges (vertical dashed connectors) ----
    ix1 = gx(gd(2023, 11, 21))
    ix2 = gx(gd(2025, 3, 10))
    out.append(f'<line x1="{sx(ix1)}" y1="{sy(116.2)}" x2="{sx(ix1)}" y2="{sy(74.4)}" stroke="#22453C" stroke-width="2.6" stroke-dasharray="5 4"/>')
    out.append(f'<line x1="{sx(ix2)}" y1="{sy(97.8)}" x2="{sx(ix2)}" y2="{sy(74.4)}" stroke="#91682A" stroke-width="2.6" stroke-dasharray="5 4"/>')

    # ---- Four converging subway tracks (grouped by data-mline for interactive hover/filter!) ----
    # 1. LLM Scene Authoring (grteal, y=116.2)
    llm_start = gx(gd(2023, 9, 20)) - 2.4
    out.append('<g class="metro-track-grp" data-mline="llm">')
    out.append(f'<path d="M {sx(90.9)} {sy(116.2)} L {sx(90.9)} {sy(71.3)} Q {sx(90.9)} {sy(70.3)} {sx(91.9)} {sy(70.3)} L {sx(93.1)} {sy(70.3)}" fill="none" stroke="{PAL["grteal"]}" stroke-width="2.8" stroke-dasharray="7 4" marker-end="url(#ma-teal)"/>')
    out.append(f'<line x1="{sx(llm_start)}" y1="{sy(116.2)}" x2="{sx(93.0)}" y2="{sy(116.2)}" stroke="{PAL["grteal"]}" stroke-width="6.2" stroke-linecap="round" marker-end="url(#ma-teal)"/>')
    # Badge
    out.append(f'<rect x="{sx(llm_start-18.8)}" y="{sy(118.4)}" width="{sx(18.6)}" height="{4.4*S}" rx="8" fill="{PAL["grteal"]}"/><text x="{sx(llm_start-9.5)}" y="{sy(115.6)}" text-anchor="middle" font-size="12.6" font-weight="700" fill="#fff">LLM Scene Authoring</text>')
    out.append('</g>')

    # 2. Subject & Multi-Ref R2V (grgold, y=97.8)
    r2v_start = gx(gd(2024, 7, 30)) - 0.8
    out.append('<g class="metro-track-grp" data-mline="r2v">')
    out.append(f'<line x1="{sx(r2v_start)}" y1="{sy(97.8)}" x2="{sx(89.2)}" y2="{sy(97.8)}" stroke="{PAL["grgold"]}" stroke-width="6.2" stroke-linecap="round"/>')
    out.append(f'<path d="M {sx(88.8)} {sy(97.8)} L {sx(89.3)} {sy(97.8)} Q {sx(90.0)} {sy(97.8)} {sx(90.0)} {sy(98.6)} L {sx(90.0)} {sy(109.9)} Q {sx(90.0)} {sy(110.7)} {sx(90.8)} {sy(110.7)} L {sx(93.1)} {sy(110.7)}" fill="none" stroke="{PAL["grgold"]}" stroke-width="4.0" marker-end="url(#ma-gold)"/>')
    out.append(f'<path d="M {sx(90.0)} {sy(97.8)} L {sx(90.0)} {sy(79.5)} Q {sx(90.0)} {sy(78.5)} {sx(91.0)} {sy(78.5)} L {sx(93.1)} {sy(78.5)}" fill="none" stroke="{PAL["grgold"]}" stroke-width="2.8" stroke-dasharray="7 4" marker-end="url(#ma-gold)"/>')
    out.append(f'<line x1="{sx(32.0)}" y1="{sy(100.6)}" x2="{sx(r2v_start)}" y2="{sy(97.8)}" stroke="{PAL["grgold"]}" stroke-width="1.4"/>')
    out.append(f'<rect x="{sx(12.2)}" y="{sy(103.4)}" width="{sx(20.0)}" height="{4.4*S}" rx="8" fill="{PAL["grgold"]}"/><text x="{sx(22.2)}" y="{sy(100.6)}" text-anchor="middle" font-size="12.6" font-weight="700" fill="#fff">Subject &amp; Multi-Ref R2V</text>')
    out.append('</g>')

    # 3. Graphics & Buffer Synthesis (mgeo -> grplum, y=74.4 + Streamed branch y=59.7)
    geo_start = gx(gd(2016, 3, 19))
    stream_bend = gx(gd(2025, 12, 18))
    out.append('<g class="metro-track-grp" data-mline="geo">')
    out.append(f'<line x1="{sx(geo_start)}" y1="{sy(74.4)}" x2="{sx(69.8)}" y2="{sy(74.4)}" stroke="{PAL["mgeo"]}" stroke-width="6.2" stroke-linecap="round"/>')
    out.append(f'<path d="M {sx(69.8)} {sy(74.4)} L {sx(87.2)} {sy(74.4)} Q {sx(88.8)} {sy(74.4)} {sx(88.8)} {sy(76.0)} L {sx(88.8)} {sy(100.9)} Q {sx(88.8)} {sy(102.5)} {sx(90.4)} {sy(102.5)} L {sx(93.0)} {sy(102.5)}" fill="none" stroke="{PAL["grplum"]}" stroke-width="6.0" stroke-linecap="round" marker-end="url(#ma-plum)"/>')
    # Streamed branch (3b) with inner dashed white track!
    stream_d = f'M {sx(66.5)} {sy(74.4)} L {sx(stream_bend)} {sy(59.7)} L {sx(93.0)} {sy(59.7)}'
    out.append(f'<path d="{stream_d}" fill="none" stroke="{PAL["grplum"]}" stroke-width="6.0" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#ma-plum)"/>')
    out.append(f'<path d="M {sx(66.8)} {sy(73.3)} L {sx(stream_bend)} {sy(59.7)} L {sx(91.4)} {sy(59.7)}" fill="none" stroke="#fff" stroke-width="1.8" stroke-dasharray="5 4"/>')
    out.append(f'<line x1="{sx(4.8)}" y1="{sy(84.8)}" x2="{sx(geo_start)}" y2="{sy(74.4)}" stroke="{PAL["mgeo"]}" stroke-width="1.4"/>')
    out.append(f'<circle cx="{sx(geo_start)}" cy="{sy(74.4)}" r="5.5" fill="#fff" stroke="{PAL["mgeo"]}" stroke-width="2.2"/>')
    out.append(f'<rect x="{sx(1.8)}" y="{sy(88.3)}" width="{sx(24.0)}" height="{4.4*S}" rx="8" fill="{PAL["grplum"]}"/><text x="{sx(13.8)}" y="{sy(85.5)}" text-anchor="middle" font-size="12.6" font-weight="700" fill="#fff">Graphics &amp; Buffer Synthesis</text>')
    out.append('</g>')

    # 4. Action WMs (grblue, y=44.3)
    wm_start = gx(gd(2020, 5, 25)) - 1.2
    out.append('<g class="metro-track-grp" data-mline="wm">')
    out.append(f'<path d="M {sx(87.4)} {sy(44.3)} L {sx(89.8)} {sy(44.3)} Q {sx(90.6)} {sy(44.3)} {sx(90.6)} {sy(45.1)} L {sx(90.6)} {sy(52.2)} Q {sx(90.6)} {sy(53.0)} {sx(91.4)} {sy(53.0)} L {sx(93.1)} {sy(53.0)}" fill="none" stroke="{PAL["grblue"]}" stroke-width="4.0" marker-end="url(#ma-blue)"/>')
    out.append(f'<line x1="{sx(wm_start)}" y1="{sy(44.3)}" x2="{sx(93.0)}" y2="{sy(44.3)}" stroke="{PAL["grblue"]}" stroke-width="6.2" stroke-linecap="round" marker-end="url(#ma-blue)"/>')
    out.append(f'<rect x="{sx(wm_start-11.6)}" y="{sy(46.5)}" width="{sx(11.4)}" height="{4.4*S}" rx="8" fill="{PAL["grblue"]}"/><text x="{sx(wm_start-5.9)}" y="{sy(43.7)}" text-anchor="middle" font-size="12.6" font-weight="700" fill="#fff">Action WMs</text>')
    out.append('</g>')

    # ---- Parse & render ALL 57 exact stations (\msa / \msb) ----
    line_map = {"116.2": "llm", "97.8": "r2v", "74.4": "geo", "59.7": "geo", "44.3": "wm"}
    pat_ms = re.compile(
        r"\\ms([ab])\{\\gd\{(\d+)\}\{(\d+)\}\{(\d+)\}\}\{([0-9.]+)\}\{(stn|prod)\}\{([^}]+)\}\{([0-9.]+)\}\{([-0-9.]+)\}\{([^}]+)\}\{((?:[^{}]|\{[^{}]*\})+)\}"
    )
    for m in pat_ms.finditer(tex):
        side, yr, mo, dy, ty_s, kind, col_k, stem_s, xoff_s, logo, raw_lbl = m.groups()
        ty = float(ty_s)
        stem = float(stem_s)
        xoff = float(xoff_s)
        tx = gx(gd(int(yr), int(mo), int(dy)))
        col = PAL.get(col_k, PAL["grslate"])
        mline = line_map.get(ty_s, "geo")
        lbl, bold, key = clean_lbl(raw_lbl)
        url = urls.get(key, "")
        full_title = titles.get(key, lbl)

        ly_end = ty + stem if side == "a" else ty - stem
        lx = tx + xoff
        # Exact metro.tex station pill proportions (4.0pt font -> 10.4px SVG units, ph=2.70mm)
        pw = max(8.4, len(lbl) * 0.61 + 3.5)
        ph = 2.70
        pill_y_top = ly_end + ph if side == "a" else ly_end

        out.append(f'<g class="metro-track-grp metro-station" data-mline="{mline}">')
        # Leader stem
        out.append(f'<path d="M {sx(tx)} {sy(ty)} L {sx(tx)} {sy(ly_end)} L {sx(lx)} {sy(ly_end)}" fill="none" stroke="{col}" stroke-opacity="0.58" stroke-width="1.2"/>')
        # Station marker on track
        if kind == "prod":
            out.append(f'<rect x="{sx(tx)-5.2}" y="{sy(ty)-5.2}" width="10.4" height="10.4" rx="2" fill="#fff" stroke="{col}" stroke-width="2.4"/>')
        else:
            out.append(f'<circle cx="{sx(tx)}" cy="{sy(ty)}" r="5.5" fill="#fff" stroke="{col}" stroke-width="2.4"/>')

        # Clickable pill
        open_a = f'<a href="{escape(url)}" target="_blank" rel="noopener">' if url else "<g>"
        close_a = "</a>" if url else "</g>"
        out.append(open_a)
        out.append(f'<title>{escape(full_title)} ({yr}-{int(mo):02d})</title>')
        out.append(f'<rect class="m-pill-bg" x="{sx(lx - pw/2)}" y="{sy(pill_y_top)}" width="{sx(pw)}" height="{ph*S}" rx="5" fill="#FFFFFF" stroke="{col}" stroke-opacity="0.55" stroke-width="1.05"/>')
        out.append(f'<image href="assets/org_icons/{escape(logo)}.png" x="{sx(lx - pw/2 + 0.55)}" y="{sy(pill_y_top - 0.52)}" width="16.5" height="16.5" preserveAspectRatio="xMidYMid meet"/>')
        fw = "700" if bold else "500"
        out.append(f'<text x="{sx(lx - pw/2 + 2.55)}" y="{sy(pill_y_top - 1.78)}" font-size="10.4" font-weight="{fw}" fill="{PAL["grslate"]}">{escape(lbl)}</text>')
        out.append(close_a)
        out.append("</g>")

    # Interchange double-ring circles (GPT4Motion & VACE)
    for ix, iy in [(ix1, 116.2), (ix1, 74.4), (ix2, 97.8), (ix2, 74.4)]:
        out.append(f'<circle cx="{sx(ix)}" cy="{sy(iy)}" r="7.5" fill="#fff" stroke="{PAL["grslate"]}" stroke-width="2.6"/><circle cx="{sx(ix)}" cy="{sy(iy)}" r="2.8" fill="{PAL["grslate"]}"/>')

    # ---- 5 Fork callout boxes ----
    forks = [
        ("grteal", ix1, 86.1, "west", 1.3, ["LLM-written scenes", "condition diffusion"]),
        ("grgold", ix2, 86.1, "west", 1.3, ["control videos and", "references in one model"]),
        ("grplum", 67.65, 62.75, "east", 1.9, ["from fixed clips to causal", "streams of engine state"]),
        ("grblue", 90.6, 52.0, "east", 1.0, ["causal few-step", "distillation"]),
        ("grgold", 90.0, 108.65, "east", 2.0, ["appearance slot & H3 ref. seq."]),
    ]
    for ck, fx, fy, anchor, llen, lines in forks:
        col = PAL[ck]
        fe = fx + llen if anchor == "west" else fx - llen
        bw = max(len(l) for l in lines) * 0.50 + 2.0
        bh = 1.95 * len(lines) + 1.2
        bx = fe if anchor == "west" else fe - bw
        out.append(f'<line x1="{sx(fx)}" y1="{sy(fy)}" x2="{sx(fe)}" y2="{sy(fy)}" stroke="{col}" stroke-width="1.3"/>')
        out.append(f'<circle cx="{sx(fx)}" cy="{sy(fy)}" r="3.0" fill="{col}"/>')
        out.append(f'<rect x="{sx(bx)}" y="{sy(fy + bh/2)}" width="{sx(bw)}" height="{bh*S}" rx="5" fill="#FFFFFF" stroke="{col}" stroke-opacity="0.58" stroke-width="1.05"/>')
        for idx, ltxt in enumerate(lines):
            ty_line = fy + bh/2 - 1.85 - idx * 1.95
            out.append(f'<text x="{sx(bx + bw/2)}" y="{sy(ty_line)}" text-anchor="middle" font-size="9.9" font-style="italic" fill="#46534F">{escape(ltxt)}</text>')

    # ---- Right-hand Terminal boxes (x=93.4..159.2) ----
    # T3a box (y=94.4..125.0)
    out.append(f'<rect x="{sx(93.4)}" y="{sy(125.0)}" width="{sx(65.8)}" height="{30.6*S}" rx="10" fill="#FFFFFF" stroke="{PAL["grplum"]}" stroke-opacity="0.72" stroke-width="1.6"/>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(122.4)}" font-size="15.2" font-weight="700" fill="#5F4964">T3a Clip Renderers · Pre-Fixed Structure (12 representative)</text>')
    out.append(f'<line x1="{sx(149.2)}" y1="{sy(122.8)}" x2="{sx(152.2)}" y2="{sy(122.8)}" stroke="{PAL["grplum"]}" stroke-width="5.2"/><text x="{sx(152.8)}" y="{sy(122.1)}" font-size="14" font-weight="700" fill="#5F4964">3a</text>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(119.3)}" font-size="13.2" font-weight="700" font-style="italic" fill="#6B5271">Executable code &amp; programmable proxies</text>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(105.8)}" font-size="13.2" font-weight="700" font-style="italic" fill="#6B5271">Engine buffers, 3D scaffolds &amp; simulators</text>')

    # T3b box (y=48.7..92.8)
    out.append(f'<rect x="{sx(93.4)}" y="{sy(92.8)}" width="{sx(65.8)}" height="{44.1*S}" rx="10" fill="#FFFFFF" stroke="{PAL["grplum"]}" stroke-opacity="0.72" stroke-width="1.6"/>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(90.2)}" font-size="15.2" font-weight="700" fill="#5F4964">T3b Stream &amp; Stateful Renderers (18 representative)</text>')
    out.append(f'<line x1="{sx(149.2)}" y1="{sy(90.6)}" x2="{sx(152.2)}" y2="{sy(90.6)}" stroke="{PAL["grplum"]}" stroke-width="5.2"/><line x1="{sx(149.3)}" y1="{sy(90.6)}" x2="{sx(152.1)}" y2="{sy(90.6)}" stroke="#fff" stroke-width="1.6" stroke-dasharray="4 3"/><text x="{sx(152.8)}" y="{sy(89.9)}" font-size="14" font-weight="700" fill="#5F4964">3b</text>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(87.1)}" font-size="13.2" font-weight="700" font-style="italic" fill="#6B5271">Interactive game engines &amp; live structure streams</text>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(73.6)}" font-size="13.2" font-weight="700" font-style="italic" fill="#6B5271">Coding agents &amp; executable rule harnesses</text>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(54.8)}" font-size="13.2" font-weight="700" font-style="italic" fill="#6B5271">Persistent world state &amp; rolling geometric streams</text>')

    # Implicit WM Contrast box (y=33.8..47.1)
    out.append(f'<rect x="{sx(93.4)}" y="{sy(47.1)}" width="{sx(65.8)}" height="{13.3*S}" rx="10" fill="#F2F6FA" stroke="{PAL["grblue"]}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    out.append(f'<text x="{sx(94.8)}" y="{sy(44.8)}" font-size="14.6" font-weight="700" fill="#3C5877">Contrasting Route: Implicit End-to-End WMs (Aug–Nov, Ch. 9)</text>')

    # Render ALL 36 terminal chips (\tchip) at EXACT coordinates!
    pat_tc = re.compile(
        r"\\tchip\{([^}]+)\}\{([^}]+)\}\{([0-9.]+)\}\{([0-9.]+)\}\{([^}]+)\}\{((?:[^{}]|\{[^{}]*\})+)\}"
    )
    for m in pat_tc.finditer(tex):
        style, pcol, cx_s, cy_s, logo, raw_lbl = m.groups()
        cx, cy = float(cx_s), float(cy_s)
        cw, ch = 20.8, 3.85
        lbl, bold, key = clean_lbl(raw_lbl)
        url = urls.get(key, "")
        full_title = titles.get(key, lbl)
        stroke = PAL.get(pcol, PAL["grblue"])
        fill = CHIP_FILL.get(pcol, "#FFFFFF") if style == "chip" else "#FFFFFF"
        pw_attr = pcol if style == "chip" else "implicit"

        open_a = f'<a class="metro-tchip" data-pw="{pw_attr}" href="{escape(url)}" target="_blank" rel="noopener">' if url else f'<g class="metro-tchip" data-pw="{pw_attr}">'
        close_a = "</a>" if url else "</g>"
        out.append(open_a)
        out.append(f'<title>{escape(full_title)}</title>')
        out.append(f'<rect class="m-pill-bg" x="{sx(cx - cw/2)}" y="{sy(cy + ch/2)}" width="{sx(cw)}" height="{ch*S}" rx="6" fill="{fill}" stroke="{stroke}" stroke-opacity="0.78" stroke-width="1.2"/>')
        out.append(f'<image href="assets/org_icons/{escape(logo)}.png" x="{sx(cx - cw/2 + 0.7)}" y="{sy(cy + 0.92)}" width="18.5" height="18.5" preserveAspectRatio="xMidYMid meet"/>')
        fw = "700" if bold else "500"
        out.append(f'<text x="{sx(cx - cw/2 + 2.9)}" y="{sy(cy - 0.45)}" font-size="11.6" font-weight="{fw}" fill="{PAL["grslate"]}">{escape(lbl)}</text>')
        out.append(close_a)

    # ---- Time axis (y=29.5) ----
    out.append(f'<line x1="{sx(2.0)}" y1="{sy(29.5)}" x2="{sx(90.6)}" y2="{sy(29.5)}" stroke="#697471" stroke-width="1.6"/>')
    for tval, tlbl in [(2016,"2016"),(2020,"2020"),(2023,"2023"),(2024,"2024"),(2025,"2025"),(2026,"Jan '26"),(2026.5,"Jul '26")]:
        tx = gx(tval)
        out.append(f'<line x1="{sx(tx)}" y1="{sy(30.3)}" x2="{sx(tx)}" y2="{sy(28.7)}" stroke="#697471" stroke-width="1.3"/>')
        out.append(f'<text x="{sx(tx)}" y="{sy(26.8)}" text-anchor="middle" font-size="14" font-weight="700" fill="{PAL["grslate"]}">{tlbl}</text>')
    out.append(f'<text x="{sx(126.3)}" y="{sy(26.8)}" text-anchor="middle" font-size="14.2" font-weight="700" fill="#5F4964">Aug – Mid-Nov 2026 Terminal (chip colours match pathways in b)</text>')

    # ---- Panel (b): Injection pathways & monthly surge chart (y=2.2..25.0) ----
    out.append(f'<rect x="{sx(0.8)}" y="{sy(25.0)}" width="{sx(159.2)}" height="{22.8*S}" rx="11" fill="#FFFFFF" stroke="{PAL["grrule"]}" stroke-width="1.4"/>')
    out.append(f'<text x="{sx(2.4)}" y="{sy(22.6)}" font-size="16.5" font-weight="700" fill="{PAL["grslate"]}">b. Injection pathways (all 50 Tier-3 systems)</text>')
    out.append(f'<rect x="{sx(2.4)}" y="{sy(21.0)}" width="{sx(34.0)}" height="{3.1*S}" rx="7" fill="#F2ECF4" stroke="#B6A3BC" stroke-width="1.1"/>')
    out.append(f'<text x="{sx(19.4)}" y="{sy(18.9)}" text-anchor="middle" font-size="13.2" font-weight="700" fill="#5F4964">32 since mid-Aug \'26 · 18 in October alone</text>')

    legend_items = [
        ("mfus", "Input or feature fusion (16)", 2.4, 15.2),
        ("mbr",  "Control branch or adapter (13)", 29.8, 15.2),
        ("mh3",  "MiniMax-H3 ref. seq. (12)", 2.4, 12.0),
        ("mctx", "Other in-context seq. (4)", 29.8, 12.0),
        ("mxat", "Cross-attention (3)", 2.4, 8.8),
        ("mtf",  "Training-free inv. (1)", 29.8, 8.8),
        ("mnr",  "Undisclosed (1)", 2.4, 5.6),
    ]
    for pw, lbl, lx, ly in legend_items:
        out.append(f'<g class="metro-pw-legend" data-pw="{pw}" style="cursor:pointer;">')
        out.append(f'<rect x="{sx(lx)}" y="{sy(ly+0.9)}" width="17.5" height="13.5" rx="3" fill="{PAL[pw]}" stroke="rgba(0,0,0,0.18)" stroke-width="0.8"/>')
        out.append(f'<text x="{sx(lx+2.3)}" y="{sy(ly-0.35)}" font-size="13.5" fill="{PAL["grslate"]}">{escape(lbl)}</text>')
        out.append("</g>")

    # Monthly stacked bars (exact coordinates from metro.tex!)
    out.append(f'<line x1="{sx(58.0)}" y1="{sy(9.4)}" x2="{sx(151.8)}" y2="{sy(9.4)}" stroke="#848E8B" stroke-width="1.3"/>')
    bars = [
        (61.0, "Jan", ["mfus","mfus"], False),
        (67.0, "Mar", ["mbr"], False),
        (73.0, "Sep", ["mfus"], False),
        (79.0, "Oct", ["mfus"], False),
        (85.0, "Dec", ["mbr"], False),
        (92.2, "Jan", ["mfus","mbr"], False),
        (98.3, "Mar", ["mfus","mctx"], False),
        (104.4,"Apr", ["mfus"], False),
        (110.5,"May", ["mbr"], False),
        (116.8,"Jul", ["mfus","mfus","mfus","mbr","mbr","mtf"], False),
        (124.6,"Aug", ["mh3","mctx","mxat"], False),
        (131.6,"Sep", ["mh3","mfus","mbr","mbr","mbr"], False),
        (140.5,"Oct", ["mh3"]*6 + ["mfus"]*5 + ["mbr"]*3 + ["mctx"]*2 + ["mxat","mnr"], True),
        (149.0,"Nov", ["mh3"]*4 + ["mbr","mxat"], False),
    ]
    for bx, mlbl, items, is_oct in bars:
        if not is_oct:
            for idx, pw in enumerate(items, 1):
                by = 9.6 + (idx - 1) * 1.30
                out.append(f'<rect class="metro-bar-blk" data-pw="{pw}" x="{sx(bx-1.35)}" y="{sy(by+1.16)}" width="27" height="11.6" rx="2.2" fill="{PAL[pw]}" stroke="#fff" stroke-width="0.9"/>')
            top_y = 9.6 + len(items) * 1.30
            out.append(f'<text x="{sx(bx)}" y="{sy(top_y + 0.35)}" text-anchor="middle" font-size="13.5" font-weight="700" fill="{PAL["grslate"]}">{len(items)}</text>')
        else:
            # Double-column 2x9 for October (18!)
            col1, col2 = items[:9], items[9:]
            for idx, pw in enumerate(col1, 1):
                by = 9.6 + (idx - 1) * 1.30
                out.append(f'<rect class="metro-bar-blk" data-pw="{pw}" x="{sx(139.0-1.35)}" y="{sy(by+1.16)}" width="27" height="11.6" rx="2.2" fill="{PAL[pw]}" stroke="#fff" stroke-width="0.9"/>')
            for idx, pw in enumerate(col2, 1):
                by = 9.6 + (idx - 1) * 1.30
                out.append(f'<rect class="metro-bar-blk" data-pw="{pw}" x="{sx(142.0-1.35)}" y="{sy(by+1.16)}" width="27" height="11.6" rx="2.2" fill="{PAL[pw]}" stroke="#fff" stroke-width="0.9"/>')
            top_y = 9.6 + 9 * 1.30
            out.append(f'<text x="{sx(140.5)}" y="{sy(top_y + 0.35)}" text-anchor="middle" font-size="13.5" font-weight="700" fill="#5F4964">18</text>')
        fw = "800" if is_oct else "500"
        out.append(f'<text x="{sx(bx)}" y="{sy(7.4)}" text-anchor="middle" font-size="13.2" font-weight="{fw}" fill="{PAL["grslate"]}">{mlbl}</text>')

    # Surge bracket & 2025 / 2026 year brackets
    out.append(f'<path d="M {sx(122.6)} {sy(22.8)} L {sx(122.6)} {sy(23.7)} L {sx(150.6)} {sy(23.7)} L {sx(150.6)} {sy(22.8)}" fill="none" stroke="#5F4964" stroke-width="1.4"/>')
    out.append(f'<text x="{sx(122.0)}" y="{sy(23.0)}" text-anchor="end" font-size="13.5" font-weight="700" fill="#5F4964">Late-2026 surge (32) →</text>')

    out.append(f'<path d="M {sx(59.5)} {sy(6.3)} L {sx(59.5)} {sy(5.6)} L {sx(86.5)} {sy(5.6)} L {sx(86.5)} {sy(6.3)}" fill="none" stroke="#8C9693" stroke-width="1.2"/>')
    out.append(f'<text x="{sx(73.0)}" y="{sy(3.8)}" text-anchor="middle" font-size="13.5" font-weight="700" fill="#4E5B57">2025 (6)</text>')

    out.append(f'<path d="M {sx(90.7)} {sy(6.3)} L {sx(90.7)} {sy(5.6)} L {sx(150.6)} {sy(5.6)} L {sx(150.6)} {sy(6.3)}" fill="none" stroke="#7A6082" stroke-width="1.2"/>')
    out.append(f'<text x="{sx(120.65)}" y="{sy(3.8)}" text-anchor="middle" font-size="13.5" font-weight="700" fill="#5F4964">2026 (44)</text>')

    out.append("</svg>")
    return "\n".join(out)

if __name__ == "__main__":
    svg_str = build_svg()
    out_fp = HUB / "docs/assets/metro_exact.svg"
    out_fp.write_text(svg_str, encoding="utf-8")
    print(f"Wrote 1:1 native interactive SVG: {out_fp} ({len(svg_str)//1024} KB)")
