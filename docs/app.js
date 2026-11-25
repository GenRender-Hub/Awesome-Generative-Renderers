(() => {
  let CATALOG = null;
  let activeMatrixTier = "all";
  let matrixQuery = "";

  let activeTrack = "all";
  let activeYear = "all";
  let rtOnly = false;
  let libQuery = "";
  let libSort = "newest";
  let visibleCount = 30;
  let autoplayTimer = null;

  const TIER_ORDER = ["T0", "T1", "T2", "T3a", "T3b"];

  const TIER_DATA = {
    T0: {
      title: "Tier 0 — Text Specification",
      color: "#1d5347",
      soft: "#e6f3ee",
      lineage: "Appearance Lineage · Entry Point",
      desc: "Words or LLM-rewritten dense captions loosely describe scene content without fixing concrete faces, camera trajectories, or frame-level geometry. The generator invents all concrete realizations.",
      upMain: "User / LLM Rewriter",
      upSub: "Dense text prompt c",
      edge: "Described",
      renSub1: "Interprets words softly",
      renSub2: "Invents cast, layout & motion",
      outMain: "Clip Y(1:T)",
      outSub: "Unanchored realization",
      memLoop: false,
      A: [
        ["Identity", "described"],
        ["Appearance", "described"],
        ["Voice", "described"],
        ["Style", "described"],
      ],
      S: [
        ["Layout", "described"],
        ["Motion", "described"],
        ["Camera", "described"],
        ["Events", "described"],
      ],
      duelUp: "Text prompt describing two fighters and a 0:04 knockdown",
      duelSyn: "Faces, choreography, timing, and circling camera",
      duelFail: "Wrong fighter falls, or fallen fighter spontaneously stands back up",
      auth: "State Authority: Generator interprets",
      track: "Foundations & Context",
    },
    T1: {
      title: "Tier 1 — Appearance Anchoring",
      color: "#ad7e34",
      soft: "#f7eedc",
      lineage: "Appearance Lineage · R2V Customization",
      desc: "One or a few subject reference portraits exemplify character identity and wardrobe, while layout, choreography, camera framing, and event timing remain open or text-described.",
      upMain: "Subject Portraits",
      upSub: "Reference images R + prompt",
      edge: "Exemplified",
      renSub1: "Preserves character identity",
      renSub2: "Invents motion & scene layout",
      outMain: "Clip Y(1:T)",
      outSub: "Identity-anchored video",
      memLoop: false,
      A: [
        ["Identity", "exemplified"],
        ["Appearance", "exemplified"],
        ["Voice", "open"],
        ["Style", "described"],
      ],
      S: [
        ["Layout", "open"],
        ["Motion", "described"],
        ["Camera", "described"],
        ["Events", "described"],
      ],
      duelUp: "One reference portrait per fighter + text prompt",
      duelSyn: "Choreography, timing, camera motion, courtyard background",
      duelFail: "Reference photo poses, lighting, and backgrounds copied verbatim",
      auth: "State Authority: Generator interprets",
      track: "T1-2",
    },
    T2: {
      title: "Tier 2 — Compositional Specification",
      color: "#a94f42",
      soft: "#f7e6e3",
      lineage: "Appearance Lineage · Omni-Reference Routing",
      desc: "Multi-modal bundles of subject images, motion/driving clips, audio tracks, timed text, or recording-extracted pose/depth maps specify separate factors; the video model reads, disentangles, and routes them.",
      upMain: "Multi-Modal Bundle",
      upSub: "Refs + clips + audio + timing",
      edge: "Composed",
      renSub1: "Routes references to roles",
      renSub2: "Synthesizes coherent 3D shot",
      outMain: "Clip Y(1:T)",
      outSub: "Multi-condition composition",
      memLoop: false,
      A: [
        ["Identity", "exemplified"],
        ["Appearance", "exemplified"],
        ["Voice", "exemplified"],
        ["Style", "exemplified"],
      ],
      S: [
        ["Layout", "open"],
        ["Motion", "exemplified"],
        ["Camera", "exemplified"],
        ["Events", "exemplified"],
      ],
      duelUp: "Portraits + fight clip + '0:04 red falls' + sound effects",
      duelSyn: "Exact 3D spatial layout, contact timing, entity routing",
      duelFail: "Outfits swap between fighters; original actors from fight clip leak in",
      auth: "State Authority: Generator interprets supplied targets",
      track: "T1-2",
    },
    T3a: {
      title: "Tier 3a — Pre-Fixed External Structure",
      color: "#765885",
      soft: "#efe9f4",
      lineage: "Geometry + Appearance Lineages Converge",
      desc: "Editable frame-aligned structure (clay renders, G-buffers, 3D scaffolds, or agent-authored Blender/Three.js scenes) is finalized before sampling begins. Accelerating T3a via few-step distillation leaves it at T3a.",
      upMain: "Artist / Code / Sim",
      upSub: "Pre-fixed structure S(1:T) + R",
      edge: "Frame-Aligned",
      renSub1: "Locks layout, motion & camera",
      renSub2: "Synthesizes lighting, cloth & fine motion",
      outMain: "Clip Y(1:T)",
      outSub: "Faithful to S(1:T)",
      memLoop: false,
      A: [
        ["Identity", "exemplified"],
        ["Appearance", "exemplified"],
        ["Voice", "exemplified"],
        ["Style", "described"],
      ],
      S: [
        ["Layout", "aligned"],
        ["Motion", "aligned"],
        ["Camera", "aligned"],
        ["Events", "aligned"],
      ],
      duelUp: "Pre-fixed clay animation with skeletons + fighter portraits",
      duelSyn: "Realistic materials, lighting, secondary cloth & natural articulation",
      duelFail: "Stiff placeholder keyframing or flat grey clay shading copied verbatim",
      auth: "State Authority: External clip specification (pre-fixed)",
      track: "T3a",
    },
    T3b: {
      title: "Tier 3b — Causal Evolving-State Stream",
      color: "#3f668c",
      soft: "#e7f0f8",
      lineage: "Live Engine / Agent Harness · Causal Runtime",
      desc: "Structural chunks stream online from a persistent world state s(t) that user or agent actions modify during generation. The renderer cannot peek at future chunks S(>k) and must keep visual memory strictly subordinate to upstream state.",
      upMain: "Live Engine / Harness",
      upSub: "Streaming chunk S(k) from s(t)",
      edge: "Causal Chunk",
      renSub1: "Obeys live state edits promptly",
      renSub2: "Memory m(k) keeps surfaces consistent",
      outMain: "Stream Y(k)",
      outSub: "Interactive frame rollout",
      memLoop: true,
      A: [
        ["Identity", "exemplified"],
        ["Appearance", "exemplified"],
        ["Voice", "exemplified"],
        ["Style", "described"],
      ],
      S: [
        ["Layout", "aligned"],
        ["Motion", "aligned"],
        ["Camera", "aligned"],
        ["Events", "aligned"],
      ],
      duelUp: "Live fighting-game engine state streamed chunk by chunk",
      duelSyn: "Consistent surface detail via visual memory without overriding state",
      duelFail: "Cached visual memory revives the fallen red fighter or delays the fall",
      auth: "State Authority: Persistent external evolving state",
      track: "T3b",
    },
  };

  const ROADMAP_CHAPTERS = {
    2: {
      badge: "CH. 02 · FRAMEWORK",
      color: "#1d5347",
      title: "Definition & Specification Ladder",
      desc: "Establishes the operational per-factor definition of a generative renderer, the inspectability boundary, the 4-tier specification ladder (T0–T3b), orthogonality between causality and inference speed, and the separation between external world state and renderer visual memory.",
      bottle: "Overreaching conditions (copying pose, color bleed, or stiff placeholder limbs) and cached visual history overriding updated external state.",
      keys: "Per-factor rendering contract (Eq. 2), T3a vs T3b orthogonality, 3 proxy-granularity regimes, Wan & MiniMax-H3 native backbones.",
      track: "Foundations & Context",
    },
    3: {
      badge: "CH. 03 · DRIVING DOMAINS",
      color: "#3b7568",
      title: "Driving Application Domains",
      desc: "Examines why creative film/short-drama production, interactive games & coding-agent worlds, and embodied/physics simulation are independently converging on upstream scene specification.",
      bottle: "Balancing authoring cost against spatial/physical controllability across creative previsualization, multi-player games, and robotics sim-to-real.",
      keys: "Seedance 2.5 clay refs, DLSS 5, VideoCoCo, Matrix-Game 4.0, Fight World Model, GameWM, RealWonder.",
      track: "T3a",
    },
    4: {
      badge: "CH. 04 · INTERFACES",
      color: "#765885",
      title: "Renderer Interfaces: References & Structure",
      desc: "Traces specifications across three stages: inference provenance (artist, agent code, engine, simulator, recording), structural representation (depth, semantics, G-buffers, clay proxies, 3D boxes), and network injection pathway.",
      bottle: "Choosing between explicit dense control maps (G-buffers) vs. coarse proxy videos (white-box / capsules) without shifting full asset authoring back upstream.",
      keys: "Table 8 (39 unified interface pipelines), SolarRenderer, DiffusionRenderer, WorldWeave, BoxWorld, RGBX-Next.",
      track: "T3a",
    },
    5: {
      badge: "CH. 05 · INTERPRETATION",
      color: "#3f668c",
      title: "From Injection to Understanding",
      desc: "Analyzes how renderers read conditioning signals selectively: binding multiple references to distinct entities, scheduling structural guidance across denoising steps, and interpreting coarse proxies without copying placeholder artifacts.",
      bottle: "Preventing attribute swaps across entities and stopping fine-tuned renderers from verbatim copying low-poly silhouettes or stiff keyframed limbs.",
      keys: "WorldDraft (source-color bleed), early-step structural schedules (Code Video Model), region-masked attention, ProForcing.",
      track: "T3a",
    },
    6: {
      badge: "CH. 06 · TRAINING & DATA",
      color: "#6b527a",
      title: "Training, Data & Few-Step Distillation",
      desc: "Covers paired supervision pipelines (engine captures, multi-granularity proxies, self-paired synthesis), adapting pretrained video priors via LoRA/ControlNet, causal rollout training, and preserving structural adherence under few-step distillation.",
      bottle: "Distillation and post-training rewards can optimize visual plausibility while silently eroding adherence to specified event timing and fine geometry.",
      keys: "CWM 2.0 multi-granularity training, SolarRenderer 136k 8-source corpus, DMD / Self Forcing / CausVid, ProForcing.",
      track: "Systems & Training",
    },
    7: {
      badge: "CH. 07 · STREAMING RUNTIME",
      color: "#ad7e34",
      title: "Streaming & Interactive Runtime (T3b)",
      desc: "Dissects how Tier-3b renderers stay responsive under live state updates: chunk vs. frame granularity, visual-memory KV management, causal VAE vs. pixel-space decoding, input-to-photon latency budgets, and multi-GPU serving stacks.",
      bottle: "Chunk duration plus 3D VAE decoding dominate input-to-photon latency; history KV caches must preserve surface appearance without reviving removed entities.",
      keys: "Matrix-Game 4.0 (83 FPS, 112 ms), EdenLive (74 FPS), AlayaRenderer-Flash (32 FPS), Wizard KV masking, PlayGen2.",
      track: "T3b",
    },
    8: {
      badge: "CH. 08 · EVALUATION",
      color: "#a94f42",
      title: "Adherence Evaluation & Benchmarks",
      desc: "Reviews 29 benchmarks across specification construction, rendering fidelity, and end-to-end system execution—separating visual aesthetics from factor coverage, geometric precision, state authority, and visual memory.",
      bottle: "Generic video quality scores (VBench/Elo) fail to penalize dropped entities, delayed knockdowns, or violated physical rules.",
      keys: "PROWBench, WorldDraft, WMEval, StreamEval, OmniVBench, FlipTest, StEvo-Bench, WorldExam.",
      track: "Benchmark",
    },
    9: {
      badge: "CH. 09 · COMPETING PATHS",
      color: "#3f668c",
      title: "The Other Path: End-to-End & Code-Only Foils",
      desc: "Tests our thesis against two competing directions: purely implicit action-conditioned video world models (Genie 4, Matrix-Game 3.5, LingBot-World) and direct code-only / classical engine rendering without neural video synthesis.",
      bottle: "Implicit models still suffer geometric drift and hidden-state decay; code-only engines require expensive production assets for photorealism.",
      keys: "Genie 4 (with Gemini loop), Fable 5.2, StrideWorld (14/15 open WMs drift), StEvo-Bench (<10% hidden-state tracking).",
      track: "World Models & Surveys",
    },
    10: {
      badge: "CH. 10–11 · OUTLOOK",
      color: "#13201d",
      title: "Open Problems, Future Directions & Conclusion",
      desc: "Outlines six concrete research directions (representation-general interfaces, selective proxy interpretation, consumer-GPU low-latency streaming, adherence-preserving distillation, standardized counterfactual benchmarks, and governance) plus empirical falsification criteria.",
      bottle: "Bridging multi-GPU cluster prototypes to consumer-GPU sub-100 ms renderers and proving when external state remains superior to stronger generalist priors.",
      keys: "Six open directions, counterfactual state probes, decoder-free pixel heads, adaptive proxy granularity.",
      track: "all",
    },
  };

  const TRACK_ORDER = [
    ["all", "All Cited Works"],
    ["T3b", "Tier 3b · Streamed & Stateful"],
    ["T3a", "Tier 3a · Pre-Fixed Structure"],
    ["T1-2", "Tiers 1–2 · Reference Lineage"],
    ["Benchmark", "Evaluation & Benchmarks"],
    ["Systems & Training", "Streaming, Codecs & Distillation"],
    ["World Models & Surveys", "World Models & Surveys"],
    ["Foundations & Context", "Foundations & Context"],
  ];

  const esc = (s) =>
    String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

  window.openLightbox = (src) => {
    document.getElementById("lb-img").src = src;
    document.getElementById("lightbox").classList.add("open");
  };

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    const orig = btn.textContent;
    btn.textContent = "Copied ✓";
    setTimeout(() => (btn.textContent = orig), 1400);
  }

  /* ---- MODULE 1: Workbench ---- */
  function setWorkbenchTier(tier) {
    const d = TIER_DATA[tier];
    if (!d) return;

    document.querySelectorAll("#tier-switcher .tier-tab").forEach((b) => {
      b.classList.toggle("active", b.dataset.tier === tier);
    });

    document.getElementById("wb-title").textContent = d.title;
    const lin = document.getElementById("wb-lineage");
    lin.textContent = d.lineage;
    lin.style.background = d.soft;
    lin.style.color = d.color;
    document.getElementById("wb-desc").textContent = d.desc;

    // Update SVG diagram
    const upBox = document.getElementById("svg-box-up");
    upBox.setAttribute("fill", d.soft);
    upBox.setAttribute("stroke", d.color);
    document.getElementById("svg-up-main").textContent = d.upMain;
    document.getElementById("svg-up-sub").textContent = d.upSub;
    document.getElementById("svg-edge-1").textContent = d.edge;
    document.getElementById("svg-ren-sub1").textContent = d.renSub1;
    document.getElementById("svg-ren-sub2").textContent = d.renSub2;
    document.getElementById("svg-out-main").textContent = d.outMain;
    document.getElementById("svg-out-sub").textContent = d.outSub;
    document.getElementById("svg-mem-loop").setAttribute("opacity", d.memLoop ? "1" : "0.16");

    // Update 2x4 factor matrix
    const renderRow = (elId, label, cells) => {
      document.getElementById(elId).innerHTML =
        `<span class="factor-row-lbl">${label}</span>` +
        cells
          .map(
            ([name, state]) =>
              `<div class="f-cell ${state}"><strong>${name}</strong><small>${state[0].toUpperCase() + state.slice(1)}</small></div>`
          )
          .join("");
    };
    renderRow("row-appearance", "A · Look", d.A);
    renderRow("row-structure", "S · Struct", d.S);

    // Update Courtyard Duel box
    document.getElementById("duel-up").textContent = d.duelUp;
    document.getElementById("duel-syn").textContent = d.duelSyn;
    document.getElementById("duel-fail").textContent = d.duelFail;
    document.getElementById("duel-auth").textContent = d.auth;
    document.getElementById("wb-jump-lib").dataset.targetTrack = d.track;
  }

  /* ---- MODULE 2: Orthogonality Quadrant ---- */
  function renderQuadrants() {
    const t3aSlow = [];
    const t3aFast = [];
    const t3bSlow = [];
    const t3bFast = [];

    for (const s of CATALOG.systems) {
      if (s.tier === "T3a") {
        const note = (s.realtime_note || "").toLowerCase();
        if (s.realtime || note.includes("var.") || s.name === "CoCode-World") {
          t3aFast.push(s);
        } else {
          t3aSlow.push(s);
        }
      } else if (s.tier === "T3b") {
        if (s.realtime) {
          t3bFast.push(s);
        } else {
          t3bSlow.push(s);
        }
      }
    }

    const chipHtml = (list, isVar = false) =>
      list
        .map((s) => {
          let tag = "";
          if (s.realtime && s.realtime_note && s.realtime_note !== "Yes") {
            tag = s.realtime_note.replace(/^Yes\s*\((.*)\)$/, "$1");
          } else if (s.name === "CoCode-World") {
            tag = "8-step";
          } else if (s.realtime_note && !["No", "Yes", "NR"].includes(s.realtime_note)) {
            tag = s.realtime_note;
          }
          const href = s.url ? `href="${esc(s.url)}" target="_blank" rel="noopener"` : `href="#matrix"`;
          return `<a class="sys-chip ${isVar ? "var" : ""}" ${href}>${esc(s.name)}${tag ? ` <span class="fps">${esc(tag)}</span>` : ""}</a>`;
        })
        .join("");

    document.getElementById("q-t3a-slow-cnt").textContent = `${t3aSlow.length} systems`;
    document.getElementById("q-t3a-fast-cnt").textContent = `${t3aFast.length} systems`;
    document.getElementById("q-t3b-slow-cnt").textContent = `${t3bSlow.length} systems`;
    document.getElementById("q-t3b-fast-cnt").textContent = `${t3bFast.length} systems`;

    document.getElementById("q-t3a-slow").innerHTML = chipHtml(t3aSlow);
    document.getElementById("q-t3a-fast").innerHTML = chipHtml(t3aFast, true);
    document.getElementById("q-t3b-slow").innerHTML = chipHtml(t3bSlow);
    document.getElementById("q-t3b-fast").innerHTML = chipHtml(t3bFast);
  }

  /* ---- MODULE 3: Roadmap Inspector ---- */
  function setRoadmapChapter(ch) {
    const info = ROADMAP_CHAPTERS[ch];
    if (!info) return;
    document.querySelectorAll(".rm-node").forEach((n) => n.classList.toggle("active", n.dataset.ch === String(ch)));
    const insp = document.getElementById("roadmap-inspector");
    insp.style.borderTopColor = info.color;
    const badge = document.getElementById("ri-badge");
    badge.textContent = info.badge;
    badge.style.color = info.color;
    document.getElementById("ri-title").textContent = info.title;
    document.getElementById("ri-desc").textContent = info.desc;
    document.getElementById("ri-bottle").textContent = info.bottle;
    document.getElementById("ri-keys").textContent = info.keys;
    document.getElementById("ri-filter-btn").dataset.track = info.track;
  }

  /* ---- MODULE 4: System Matrix ---- */
  function formatRtBadge(s) {
    const note = s.realtime_note || (s.realtime ? "Yes" : "No");
    if (s.realtime) {
      const clean = note === "Yes" ? "Real-Time" : note.replace(/^Yes\s*\((.*)\)$/, "$1");
      return `<span class="rt-badge fast">⚡ ${esc(clean)}</span>`;
    }
    if (/var\./i.test(note)) {
      return `<span class="rt-badge var">${esc(note)}</span>`;
    }
    if (note === "No") {
      return `<span class="rt-badge slow">${s.tier === "T3a" ? "Pre-fixed clip" : "Sub-RT"}</span>`;
    }
    return `<span class="rt-badge slow">${esc(note)}</span>`;
  }

  function renderMatrix() {
    const tbody = document.getElementById("matrix-tbody");
    const q = matrixQuery.trim().toLowerCase();
    const rows = CATALOG.systems.filter((s) => {
      if (activeMatrixTier === "rt" && !s.realtime) return false;
      if (activeMatrixTier !== "all" && activeMatrixTier !== "rt" && s.tier !== activeMatrixTier) return false;
      if (!q) return true;
      return `${s.name} ${s.tier} ${s.upstream} ${s.inputs} ${s.state_owner} ${s.injection} ${s.training_data} ${s.realtime_note}`.toLowerCase().includes(q);
    });

    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--muted);">No matching systems.</td></tr>`;
      return;
    }

    tbody.innerHTML = rows
      .map((s) => {
        const nameHtml = s.url
          ? `<a class="sys-link" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)} ↗</a>`
          : `<span class="sys-link">${esc(s.name)}</span>`;
        return `<tr>
          <td>${nameHtml}<span class="t-badge ${esc(s.tier)}">${esc(s.tier)}</span></td>
          <td>${esc(s.upstream)}</td>
          <td>${esc(s.inputs)}</td>
          <td>${esc(s.state_owner)}</td>
          <td>${esc(s.injection)}</td>
          <td>${esc(s.training_data)}</td>
          <td>${formatRtBadge(s)}</td>
        </tr>`;
      })
      .join("");
  }

  /* ---- MODULE 5: Searchable Library ---- */
  function renderTrackFilters() {
    const box = document.getElementById("track-filters");
    const counts = { all: CATALOG.papers.length };
    for (const p of CATALOG.papers) counts[p.track] = (counts[p.track] || 0) + 1;

    box.innerHTML = TRACK_ORDER.map(([id, label]) => {
      const act = activeTrack === id ? "active" : "";
      return `<button type="button" class="track-btn ${act}" data-track="${esc(id)}"><b>${esc(label)}</b><span>${counts[id] || 0}</span></button>`;
    }).join("");

    box.querySelectorAll(".track-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        activeTrack = btn.dataset.track;
        visibleCount = 30;
        renderTrackFilters();
        renderLibrary();
      });
    });
  }

  function populateYears() {
    const sel = document.getElementById("year-filter");
    const years = [...new Set(CATALOG.papers.map((p) => p.year).filter(Boolean))].sort((a, b) => b.localeCompare(a));
    sel.innerHTML = `<option value="all">All years</option>` + years.map((y) => `<option value="${esc(y)}">${esc(y)}</option>`).join("");
  }

  function renderLibrary() {
    const q = libQuery.trim().toLowerCase();
    let list = CATALOG.papers.filter((p) => {
      if (activeTrack !== "all" && p.track !== activeTrack) return false;
      if (activeYear !== "all" && p.year !== activeYear) return false;
      if (rtOnly && !p.realtime) return false;
      if (!q) return true;
      return `${p.name} ${p.title} ${p.authors} ${p.year} ${p.eprint} ${p.track} ${p.summary} ${p.venue}`.toLowerCase().includes(q);
    });

    list = [...list].sort((a, b) => {
      if (libSort === "newest") return (b.year || "0").localeCompare(a.year || "0") || a.title.localeCompare(b.title);
      if (libSort === "oldest") return (a.year || "9").localeCompare(b.year || "9") || a.title.localeCompare(b.title);
      return a.title.localeCompare(b.title);
    });

    document.getElementById("results-count").textContent = `Showing ${Math.min(visibleCount, list.length)} of ${list.length} cited works`;
    const slice = list.slice(0, visibleCount);
    const el = document.getElementById("paper-list");

    if (!slice.length) {
      el.innerHTML = `<p style="padding:24px 0;color:var(--muted);">No works match the current filters.</p>`;
    } else {
      el.innerHTML = slice
        .map((p, idx) => {
          const titleHtml = p.url
            ? `<a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a>`
            : esc(p.title);
          const rtChip = p.realtime
            ? `<span class="rt-badge fast">⚡ ${esc((p.realtime_note || "Real-Time").replace(/^Yes\s*\((.*)\)$/, "$1"))}</span>`
            : "";
          const linkHtml = p.eprint
            ? `<a class="p-lnk" href="https://arxiv.org/abs/${esc(p.eprint)}" target="_blank" rel="noopener">arXiv:${esc(p.eprint)} ↗</a>`
            : p.url
            ? `<a class="p-lnk" href="${esc(p.url)}" target="_blank" rel="noopener">Paper / Link ↗</a>`
            : "";
          return `<article class="paper-item">
            <div class="paper-top">
              <span class="t-badge ${esc(p.track)}">${esc(p.track)}</span>
              ${p.name ? `<b style="color:var(--ink);">${esc(p.name)}</b>` : ""}
              ${p.year ? `<span>${esc(p.year)}</span>` : ""}
              ${rtChip}
            </div>
            <h3>${titleHtml}</h3>
            ${p.authors ? `<p class="p-auth">${esc(p.authors)}</p>` : ""}
            ${p.summary ? `<p class="p-sum">${esc(p.summary)}</p>` : ""}
            <div class="p-foot">
              <div>${linkHtml}</div>
              ${p.bibtex ? `<button type="button" class="copy-btn" data-idx="${idx}">Copy BibTeX</button>` : ""}
            </div>
          </article>`;
        })
        .join("");

      el.querySelectorAll(".copy-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const item = slice[Number(btn.dataset.idx)];
          if (item && item.bibtex) copyText(item.bibtex, btn);
        });
      });
    }

    const lm = document.getElementById("load-more");
    if (list.length > visibleCount) {
      lm.style.display = "inline-flex";
      lm.textContent = `Show more (${list.length - visibleCount} remaining)`;
    } else {
      lm.style.display = "none";
    }
  }

  function jumpToLibraryTrack(track) {
    activeTrack = track || "all";
    visibleCount = 30;
    renderTrackFilters();
    renderLibrary();
    document.getElementById("library").scrollIntoView({ behavior: "smooth" });
  }

  async function init() {
    setWorkbenchTier("T3a");
    setRoadmapChapter("2");

    document.querySelectorAll("#tier-switcher .tier-tab").forEach((b) => {
      b.addEventListener("click", () => {
        if (autoplayTimer) {
          clearInterval(autoplayTimer);
          autoplayTimer = null;
          document.getElementById("wb-autoplay").textContent = "▶ Auto-Step";
        }
        setWorkbenchTier(b.dataset.tier);
      });
    });

    document.getElementById("wb-autoplay").addEventListener("click", (e) => {
      if (autoplayTimer) {
        clearInterval(autoplayTimer);
        autoplayTimer = null;
        e.currentTarget.textContent = "▶ Auto-Step";
        return;
      }
      e.currentTarget.textContent = "⏸ Pause";
      let idx = TIER_ORDER.indexOf(document.querySelector("#tier-switcher .tier-tab.active").dataset.tier);
      autoplayTimer = setInterval(() => {
        idx = (idx + 1) % TIER_ORDER.length;
        setWorkbenchTier(TIER_ORDER[idx]);
      }, 2800);
    });

    document.getElementById("wb-jump-lib").addEventListener("click", (e) => {
      e.preventDefault();
      jumpToLibraryTrack(e.currentTarget.dataset.targetTrack);
    });

    document.querySelectorAll(".rm-node").forEach((n) => {
      n.addEventListener("click", () => setRoadmapChapter(n.dataset.ch));
    });
    document.getElementById("ri-filter-btn").addEventListener("click", (e) => {
      jumpToLibraryTrack(e.currentTarget.dataset.track);
    });

    const res = await fetch("data/catalog.json");
    CATALOG = await res.json();

    const c = CATALOG.meta.counts;
    document.getElementById("stat-cited").textContent = c.cited_works;
    document.getElementById("stat-systems").textContent = c.systems_total;
    document.getElementById("stat-t3").textContent = c.tier3_total;
    document.getElementById("stat-bench").textContent = c.benchmarks;

    renderQuadrants();
    populateYears();
    renderTrackFilters();
    renderMatrix();
    renderLibrary();

    document.querySelectorAll("#matrix-pills .pill").forEach((p) => {
      p.addEventListener("click", () => {
        document.querySelectorAll("#matrix-pills .pill").forEach((x) => x.classList.remove("active"));
        p.classList.add("active");
        activeMatrixTier = p.dataset.mt;
        renderMatrix();
      });
    });
    document.getElementById("matrix-search").addEventListener("input", (e) => {
      matrixQuery = e.target.value;
      renderMatrix();
    });
    document.getElementById("year-filter").addEventListener("change", (e) => {
      activeYear = e.target.value;
      visibleCount = 30;
      renderLibrary();
    });
    document.getElementById("rt-only").addEventListener("change", (e) => {
      rtOnly = e.target.checked;
      visibleCount = 30;
      renderLibrary();
    });
    document.getElementById("lib-search").addEventListener("input", (e) => {
      libQuery = e.target.value;
      visibleCount = 30;
      renderLibrary();
    });
    document.getElementById("lib-sort").addEventListener("change", (e) => {
      libSort = e.target.value;
      renderLibrary();
    });
    document.getElementById("reset-filters").addEventListener("click", () => {
      activeTrack = "all";
      activeYear = "all";
      rtOnly = false;
      libQuery = "";
      visibleCount = 30;
      document.getElementById("year-filter").value = "all";
      document.getElementById("rt-only").checked = false;
      document.getElementById("lib-search").value = "";
      renderTrackFilters();
      renderLibrary();
    });
    document.getElementById("load-more").addEventListener("click", () => {
      visibleCount += 40;
      renderLibrary();
    });
    document.getElementById("copy-survey-bib").addEventListener("click", (e) => {
      copyText(document.getElementById("survey-bibtex").textContent, e.currentTarget);
    });
  }

  init().catch((err) => {
    console.error(err);
    document.getElementById("results-count").textContent = "Failed to load data/catalog.json";
  });
})();
