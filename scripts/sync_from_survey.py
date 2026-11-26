#!/usr/bin/env python3
"""Sync structured catalog (docs/data/catalog.json), downloadable docs/references.bib,
root citation.bib, visual assets, and Awesome README.md directly from GenRender-Survey's
verified LaTeX sources (main.bbl, references.bib, appendix_master_table.tex, benchmark_scope.tex)."""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image

SURVEY_DIR = Path("/data/workspace/project/GenRender-Survey")
HUB_DIR = Path(__file__).resolve().parents[1]


def clean_tex(s: str) -> str:
    s = re.sub(r"\\citep?\{[^}]*\}", "", s)
    s = re.sub(r"\\textcolor\{[^}]*\}\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\(?:tiny|scriptsize|footnotesize|textbf|emph|textit)\b", "", s)
    s = s.replace(r"\grmark", "Yes").replace(r"\grcross", "No").replace(r"\grnr", "NR")
    s = s.replace(r"\gropen", "–").replace(r"\gropt", "Partial")
    s = s.replace(r"\&", "&").replace(r"\%", "%").replace(r"\#", "#").replace(r"\$", "$")
    s = s.replace(r"\!", "").replace(r"\,", " ").replace("~", " ").replace(r"\ ", " ")
    s = s.replace(r"\approx", "≈").replace(r"\sim", "~").replace(r"\times", "×")
    s = s.replace(r"\rightarrow", "→").replace(r"\le", "≤").replace(r"\ge", "≥").replace(r"\pm", "±")
    s = s.replace("--", "–").replace("$", "")
    s = re.sub(r"\\[\"'`^~]\{?([A-Za-z])\}?", r"\1", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def parse_bib(paths: list[Path]) -> dict[str, dict]:
    bib_map: dict[str, dict] = {}
    for p in paths:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"(@\w+\{([^,\s]+),(.*?)\n\})", text, re.S):
            raw, key, body = m.group(1), m.group(2).strip(), m.group(3)

            def field(name: str) -> str:
                fm = re.search(rf"\b{name}\s*=\s*\{{(.*?)\}}(?:,|\s*$)", body, re.S | re.I)
                if not fm:
                    fm = re.search(rf'\b{name}\s*=\s*"(.*?)"', body, re.S | re.I)
                return clean_tex(fm.group(1)) if fm else ""

            url = field("url")
            eprint = field("eprint")
            if not url and eprint:
                url = f"https://arxiv.org/abs/{eprint}"
            bib_map[key] = {
                "key": key,
                "title": field("title"),
                "authors": field("author"),
                "year": field("year"),
                "venue": field("booktitle") or field("journal") or ("arXiv" if eprint else ""),
                "eprint": eprint,
                "url": url,
                "bibtex": raw.strip(),
            }
    return bib_map


def get_cited_keys(bbl_path: Path) -> list[str]:
    if not bbl_path.exists():
        return []
    text = bbl_path.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", text)


def classify_injection(inj: str) -> str:
    low = inj.lower()
    if any(k in low for k in ["h3", "ref.", "ref2va", "in-context", "seq.", "token concat", "ic-lora"]):
        return "In-Context / Ref Seq"
    if any(k in low for k in ["concat", "fusion", "additive", "latent"]):
        return "Input / Feature Fusion"
    if any(k in low for k in ["branch", "controlnet", "adapter", "vace", "lora"]):
        return "Control Branch / Adapter"
    if any(k in low for k in ["x-attn", "cross-attn", "attention"]):
        return "Cross-Attention"
    return "Other / Undisclosed"


def parse_master_table(tex_path: Path, bib: dict[str, dict], matrix_rows: dict[str, dict]) -> list[dict]:
    systems: list[dict] = []
    tier = "T3a"
    for line in tex_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith(r"\cmpgroup"):
            if "Tier 3a" in s:
                tier = "T3a"
            elif "Tier 3b" in s:
                tier = "T3b"
            elif "Tiers 1" in s or "Tier 1" in s or "Tier~1" in s:
                tier = "T1-2"
            continue
        if r"\citep{" not in s or "&" not in s:
            continue
        s_clean = re.sub(r"\\\\\s*$", "", s)
        # Split on unescaped '&' only (never split '\&')!
        cols = [c.strip() for c in re.split(r"(?<!\\)&", s_clean)]
        if len(cols) < 7:
            continue
        km = re.search(r"\\citep\{([^}]+)\}", cols[0])
        key = km.group(1).split(",")[0].strip() if km else ""
        name = clean_tex(cols[0])
        binfo = bib.get(key, {})
        mrow = matrix_rows.get(name.lower(), {})
        rt_raw = cols[6]
        is_rt = r"\grmark" in rt_raw
        rt_note = clean_tex(rt_raw)
        systems.append({
            "kind": "system",
            "name": name,
            "tier": tier,
            "key": key,
            "title": binfo.get("title", name),
            "authors": binfo.get("authors", ""),
            "year": binfo.get("year", ""),
            "date": mrow.get("date", binfo.get("year", "")),
            "url": binfo.get("url", mrow.get("paper_url", "")),
            "project_url": mrow.get("project_url", ""),
            "backbone": mrow.get("backbone", ""),
            "upstream": clean_tex(cols[1]),
            "inputs": clean_tex(cols[2]),
            "state_owner": clean_tex(cols[3]),
            "injection": clean_tex(cols[4]),
            "injection_family": classify_injection(clean_tex(cols[4])),
            "training_data": clean_tex(cols[5]),
            "realtime": is_rt,
            "realtime_note": rt_note,
            "bibtex": binfo.get("bibtex", ""),
        })
    return systems


def parse_benchmarks(tex_path: Path, bib: dict[str, dict]) -> list[dict]:
    benches: list[dict] = []
    stage = "Stage 1: Specification Construction"
    for line in tex_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith(r"\cmpgroup"):
            if "Stage 1" in s:
                stage = "Stage 1: Specification Construction"
            elif "Stage 2" in s:
                stage = "Stage 2: Rendering"
            elif "Stage 3" in s:
                stage = "Stage 3: Final Video / System"
            continue
        m = re.match(r"\\cmpmethod\{([^}]+)\}\{([^}]+)\}", s)
        if not m:
            continue
        name = clean_tex(m.group(1))
        key = m.group(2).split(",")[0].strip()
        cols = [c.strip() for c in re.split(r"(?<!\\)&", re.sub(r"\\\\\s*$", "", s))]
        binfo = bib.get(key, {})
        benches.append({
            "kind": "benchmark",
            "name": name,
            "tier": "Benchmark",
            "stage": stage,
            "key": key,
            "title": binfo.get("title", name),
            "authors": binfo.get("authors", ""),
            "year": binfo.get("year", ""),
            "url": binfo.get("url", ""),
            "output_type": clean_tex(cols[2]) if len(cols) > 2 else "",
            "reference": clean_tex(cols[3]) if len(cols) > 3 else "",
            "breakdown": clean_tex(cols[4]) if len(cols) > 4 else "",
            "cases": clean_tex(cols[5]) if len(cols) > 5 else "",
            "bibtex": binfo.get("bibtex", ""),
        })
    return benches


def build_library(cited_keys: list[str], bib: dict[str, dict], systems: list[dict], benches: list[dict]) -> list[dict]:
    sys_by_key = {x["key"]: x for x in systems if x["key"]}
    bench_by_key = {x["key"]: x for x in benches if x["key"]}

    papers: list[dict] = []
    seen: set[str] = set()
    for key in cited_keys:
        if key in seen or key not in bib:
            continue
        seen.add(key)
        b = bib[key]
        sx = sys_by_key.get(key)
        bx = bench_by_key.get(key)
        if sx:
            track = sx["tier"]  # T3a, T3b, T1-2
            badge = sx["name"]
            summary = f"{sx['upstream']} · {sx['inputs']} · {sx['injection']}"
            is_rt = sx["realtime"]
            rt_note = sx["realtime_note"]
        elif bx:
            track = "Benchmark"
            badge = bx["name"]
            summary = f"{bx['stage']} · {bx['reference']} · {bx['breakdown']}"
            is_rt = False
            rt_note = ""
        else:
            # Classify broader cited literature cleanly
            tlow = (b["title"] + " " + b["key"]).lower()
            if any(w in tlow for w in ["bench", "eval", "metric", "vbench", "score", "probe"]):
                track = "Benchmark"
            elif any(w in tlow for w in ["distill", "caus", "forcing", "stream", "real-time", "realtime", "kv", "cache", "vae", "codec", "flow", "attention", "serve"]):
                track = "Systems & Training"
            elif any(w in tlow for w in ["world model", "genie", "oasis", "gamengen", "lingbot", "matrix-game", "worldplay", "cosmos", "survey", "harness"]):
                track = "World Models & Surveys"
            else:
                track = "Foundations & Context"
            badge = ""
            summary = b["venue"]
            is_rt = False
            rt_note = ""

        papers.append({
            "key": key,
            "name": badge,
            "title": b["title"] or key,
            "authors": b["authors"],
            "year": b["year"],
            "venue": b["venue"],
            "eprint": b["eprint"],
            "url": b["url"],
            "track": track,
            "summary": summary,
            "realtime": is_rt,
            "realtime_note": rt_note,
            "bibtex": b["bibtex"],
        })
    return papers


def sync_assets() -> None:
    assets_dir = HUB_DIR / "docs/assets"
    lockups_dir = assets_dir / "lockups"
    assets_dir.mkdir(parents=True, exist_ok=True)
    lockups_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cropped transparent logo
    shutil.copy2(SURVEY_DIR / "brand/logoVideoRender_cropped.png", assets_dir / "logo.png")

    # 2. Transparent teaser resized for crisp fast web loading (1800px wide)
    t_im = Image.open(SURVEY_DIR / "figures/generated/genrender_teaser_v19_transparent.png").convert("RGBA")
    t_im.thumbnail((1800, 900), Image.Resampling.LANCZOS)
    t_im.save(assets_dir / "teaser.png", optimize=True)

    # 3. Render Figure 4 (specification ladder pyramid) cleanly to web PNG (1600px wide)
    ladder_pdf = SURVEY_DIR / "figures/generated/ch02_fig04_ladder.pdf"
    if ladder_pdf.exists():
        tmp_prefix = Path("/tmp/hub_ladder_render")
        subprocess.run(
            ["pdftoppm", "-png", "-r", "120", "-singlefile", str(ladder_pdf), str(tmp_prefix)],
            check=True,
        )
        l_im = Image.open(f"{tmp_prefix}.png").convert("RGB")
        l_im.thumbnail((1600, 900), Image.Resampling.LANCZOS)
        l_im.save(assets_dir / "ladder.png", optimize=True)

    # 4. Copy all 15 official horizontal calligraphy university lockups
    for fp in sorted((SURVEY_DIR / "figures/logos/lockups").glob("*.png")):
        shutil.copy2(fp, lockups_dir / fp.name)


def render_readme(systems: list[dict], benches: list[dict], cited_count: int) -> str:
    t3a = [x for x in systems if x["tier"] == "T3a"]
    t3b = [x for x in systems if x["tier"] == "T3b"]
    t12 = [x for x in systems if x["tier"] == "T1-2"]

    def row_sys(x: dict) -> str:
        link = f"[{md_escape(x['name'])}]({x['url']})" if x["url"] else md_escape(x["name"])
        rt = md_escape(x["realtime_note"]) if x["realtime_note"] else ("Yes" if x["realtime"] else "No")
        return f"| {link} | {x['year'] or '—'} | {md_escape(x['upstream'])} | {md_escape(x['inputs'])} | {md_escape(x['injection'])} | {rt} |"

    def row_bench(x: dict) -> str:
        link = f"[{md_escape(x['name'])}]({x['url']})" if x["url"] else md_escape(x["name"])
        return f"| {link} | {md_escape(x['stage'])} | {md_escape(x['reference'])} | {md_escape(x['breakdown'])} | {md_escape(x['cases'] or '—')} |"

    lines = [
        "# Awesome Generative Renderers",
        "### *Video Models as Generative Renderers: Foundations, Interfaces, Systems, and Beyond*",
        "",
        "[![Survey Hub](https://img.shields.io/badge/Survey_Hub-genrender--hub.github.io-1E5246?style=for-the-badge)](https://genrender-hub.github.io/) "
        f"[![Cited Works](https://img.shields.io/badge/Cited_Works-{cited_count}-4E6E91?style=for-the-badge)](https://genrender-hub.github.io/#library) "
        f"[![Tier-3 Renderers](https://img.shields.io/badge/Tier--3_Renderers-{len(t3a)+len(t3b)}-785C84?style=for-the-badge)](#tier-3b-streamed--stateful-renderers) "
        f"[![Benchmarks](https://img.shields.io/badge/Benchmarks-{len(benches)}-AD803B?style=for-the-badge)](#evaluation-benchmarks) "
        "[![Contact](https://img.shields.io/badge/Contact-xyli%40se.cuhk.edu.hk-A75246?style=for-the-badge)](mailto:xyli@se.cuhk.edu.hk)",
        "",
        "A living, community-maintained research library and interactive companion accompanying the survey ***Video Models as Generative Renderers: Foundations, Interfaces, Systems, and Beyond*** (November 2026). Synthesizing **over 330 works** (`336` verified references) and comparing **68 representative systems** across tiers 1–3 (`26` pre-fixed T3a renderers, `24` causal/stateful T3b renderers, and `18` reference-conditioned T1–T2 systems).",
        "",
        "🌐 **Interactive Survey Hub & Searchable Library:** [https://genrender-hub.github.io/](https://genrender-hub.github.io/)",
        "",
        "![External specification in generative video rendering](docs/assets/teaser.png)",
        "",
        "## Core Framework: The Specification Ladder",
        "",
        "Frontier video generation is shifting from open-ended content invention toward **faithful conditional rendering**: decisions about scene layout, identity, rules, and timing move upstream into external specifications, leaving the video model to preserve what is specified and synthesize omitted visual detail.",
        "",
        "| Tier | Upstream Specification | Precision | Timing | Authority |",
        "|---|---|---|---|---|",
        "| **T0** | Text prompt / rewritten caption | Described | Input-dependent | Generator interprets |",
        "| **T1** | Subject reference portraits + text | Exemplified | Input-dependent | Generator interprets |",
        "| **T2** | Multi-modal references & extracted controls | Exemplified / aligned | Input-dependent | Generator interprets |",
        "| **T3a** | Externally constructed structure (clay, G-buffers, code, sim) | Frame-aligned | **Pre-fixed** before sampling | External clip specification |",
        "| **T3b** | Externally constructed structure from live engine / agent | Frame-aligned | **Streamed** chunk by chunk | External evolving state |",
        "",
        "> **Orthogonality note:** The **T3a vs. T3b** boundary is defined by *specification timing and causality* (whether $S_{1:T}$ is pre-fixed before sampling vs. causally driven by an evolving state), **not** wall-clock inference speed. A distilled pre-fixed clip renderer running faster than real-time remains T3a, whereas a causal stateful renderer running at 1 FPS remains T3b.",
        "",
        f"## Tier 3b: Streamed & Stateful Renderers ({len(t3b)} systems)",
        "",
        "| System | Year | Settled Upstream | Renderer Inputs | Injection | RT / Speed |",
        "|---|---|---|---|---|---|",
        *[row_sys(x) for x in t3b],
        "",
        f"## Tier 3a: Pre-Fixed Clip Generative Renderers ({len(t3a)} systems)",
        "",
        "| System | Year | Settled Upstream | Renderer Inputs | Injection | RT / Variant |",
        "|---|---|---|---|---|---|",
        *[row_sys(x) for x in t3a],
        "",
        f"## Tiers 1–2: Reference & Compositional Lineage ({len(t12)} representative systems)",
        "",
        "| System | Year | Settled Upstream | Renderer Inputs | Injection | RT / Speed |",
        "|---|---|---|---|---|---|",
        *[row_sys(x) for x in t12],
        "",
        f"## Evaluation Benchmarks ({len(benches)} benchmarks across 3 pipeline stages)",
        "",
        "| Benchmark | Stage | Reference / Oracle | Breakdown | Cases |",
        "|---|---|---|---|---|",
        *[row_bench(x) for x in benches],
        "",
        "## Contributing",
        "",
        "Want to add a new generative renderer, proxy benchmark, or streaming system? Open a Pull Request editing `docs/data/catalog.json` (or run `python3 scripts/sync_from_survey.py` against updated LaTeX tables) with the verified arXiv link, tier placement, and BibTeX entry, or email [xyli@se.cuhk.edu.hk](mailto:xyli@se.cuhk.edu.hk).",
        "",
        "## Citation",
        "",
        "```bibtex",
        "@article{li2026generativerenderers,",
        "  title   = {Video Models as Generative Renderers: Foundations, Interfaces, Systems, and Beyond},",
        "  author  = {Li, Xinye and Zhang, Liuzhou and Sun, Te and Luo, Shipeng and Lin, Lingshuai and Jin, Yijie and Lang, Zirui and Fang, Guian and others and Wu, Shu and Huang, Yan and Ding, Fangqiang and Zhang, Shaofeng and Lam, Wai},",
        "  journal = {arXiv preprint},",
        "  year    = {2026}",
        "}",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    sync_assets()
    bib = parse_bib([SURVEY_DIR / "references.bib", SURVEY_DIR / "references_extra.bib"])
    cited_keys = get_cited_keys(SURVEY_DIR / "main.bbl")
    matrix_rows: dict[str, dict] = {}
    mpath = SURVEY_DIR / "data/literature_matrix.csv"
    if mpath.exists():
        with mpath.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                matrix_rows[row["system"].strip().lower()] = row

    systems = parse_master_table(SURVEY_DIR / "sections/appendix_master_table.tex", bib, matrix_rows)
    benches = parse_benchmarks(SURVEY_DIR / "tables/benchmark_scope.tex", bib)
    papers = build_library(cited_keys, bib, systems, benches)

    catalog = {
        "meta": {
            "title": "Video Models as Generative Renderers",
            "subtitle": "Foundations, Interfaces, Systems, and Beyond",
            "updated": "2026-11-26",
            "contact": "xyli@se.cuhk.edu.hk",
            "homepage": "https://genrender-hub.github.io/",
            "repo": "https://github.com/GenRender-Hub/Awesome-Generative-Renderers",
            "counts": {
                "cited_works": len(papers),
                "systems_total": len(systems),
                "tier3_total": sum(1 for x in systems if x["tier"] in ("T3a", "T3b")),
                "tier3a": sum(1 for x in systems if x["tier"] == "T3a"),
                "tier3b": sum(1 for x in systems if x["tier"] == "T3b"),
                "tier12": sum(1 for x in systems if x["tier"] == "T1-2"),
                "benchmarks": len(benches),
            },
        },
        "systems": systems,
        "benchmarks": benches,
        "papers": papers,
    }

    out_json = HUB_DIR / "docs/data/catalog.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    # Downloadable full references.bib containing all cited works
    bib_entries = [p["bibtex"] for p in papers if p.get("bibtex")]
    (HUB_DIR / "docs/references.bib").write_text("\n\n".join(bib_entries) + "\n", encoding="utf-8")

    # Root citation.bib
    (HUB_DIR / "citation.bib").write_text(
        "@article{li2026generativerenderers,\n"
        "  title   = {Video Models as Generative Renderers: Foundations, Interfaces, Systems, and Beyond},\n"
        "  author  = {Li, Xinye and Zhang, Liuzhou and Sun, Te and Luo, Shipeng and Lin, Lingshuai and Jin, Yijie and Lang, Zirui and Fang, Guian and others and Wu, Shu and Huang, Yan and Ding, Fangqiang and Zhang, Shaofeng and Lam, Wai},\n"
        "  journal = {arXiv preprint},\n"
        "  year    = {2026}\n"
        "}\n",
        encoding="utf-8",
    )

    readme = render_readme(systems, benches, len(papers))
    (HUB_DIR / "README.md").write_text(readme, encoding="utf-8")
    print("Synced:", catalog["meta"]["counts"])


if __name__ == "__main__":
    main()
