# paper-three-pass-reader

A local-first **three-pass paper reading skill** for Hermes / OpenClaw agents and humans.
It implements S. Keshav's *How to Read a Paper* method (2007) as a reproducible, evidence-disciplined workflow that ends in an interactive HTML page you can read offline or publish to GitHub Pages.

> Read once, read the right way, and walk away with a page that proves you understood the paper.

---

## What this skill is

A single-skill package that takes **any of the things that hint at a paper** — a PDF, an arXiv URL, a DOI, a title, a screenshot of the title page, an abstract, a social media post, a GitHub repo, or just a topic — and produces:

1. A canonical **paper identity** (Stage 0: Intake & Resolution)
2. A **first-pass triage** with the Five Cs (Stage 1)
3. A **second-pass understanding** with a Claims → Evidence map (Stage 2)
4. A **third-pass reconstruction** with critique and reproduction plan (Stage 3)
5. A **self-contained interactive HTML page** that holds all of it

The skill is **local-only**, **static**, and **no backend**. The HTML page works straight from `file://`.

---

## When to use it

Use `paper-three-pass-reader` when:

- You have a paper (or a strong hint at one) and want to **understand it rigorously**, not just summarise it.
- You're preparing for a reading group, a literature review, a thesis chapter, or a project that depends on a specific paper.
- You want a durable artifact (HTML page + JSON + Markdown reports) you can re-read, share, or publish.
- You're an AI agent and want a paper-reading workflow with explicit **evidence labels** instead of vibes-based summarisation.

Do **not** use it when you only need a quick "what's this paper about?" blurb — that's `pdf-to-markdown-pipeline` or a single LLM call.

---

## Supported inputs

Stage 0 normalises any of these into a canonical paper:

| Input type | Examples |
|---|---|
| `complete_paper` | PDF file, full text, LaTeX source, HTML paper |
| `paper_url` | arXiv, DOI, publisher (ACM/IEEE/Springer/Nature/ScienceDirect), OpenReview, PubMed/bioRxiv/medRxiv |
| `paper_identifier` | arXiv ID, DOI, OpenReview ID |
| `paper_title` | "How to Read a Paper" |
| `paper_metadata` | title + author(s) + year + venue |
| `paper_excerpt` | abstract, introduction, conclusion, BibTeX, citation |
| `paper_image` / `paper_screenshot` | photo of a printed page, slide screenshot, poster |
| `paper_topic` | method/model/dataset/benchmark/author/conference clue |
| `project_or_repo` | GitHub repo or project page that accompanies a paper |
| `ambiguous_clue` | a social-media post or screenshot mentioning a paper |

The intake step always outputs an `intake_quality.json` and a `reading_mode` so you know whether the skill is operating on **full text**, **partial text**, **abstract only**, or **screenshot only**.

---

## The three-pass method

This skill faithfully implements Keshav (2007), *How to Read a Paper*:

### Pass 1 — Bird's-eye view (5–10 minutes)

- Read the **title, abstract, introduction, section headings, conclusions, references**.
- Glance at the figures and skim the math.
- Try to answer the **Five Cs**:
  - **Category** — what type of paper is this?
  - **Context** — what other papers does it relate to?
  - **Correctness** — do the assumptions and method seem valid?
  - **Contributions** — what are the paper's main contributions?
  - **Clarity** — is the paper well-written?
- Decide whether to read further. The skill records this decision explicitly.

### Pass 2 — Understand the content (≈1 hour)

- Read the paper with greater care, but **skip the proofs**.
- Identify the **main ideas, claims, evidence, and figures/tables**.
- Build a **Claims → Evidence map**: every load-bearing claim is paired with the figure/table/section that supports it (or flagged as "needs verification").

### Pass 3 — Reconstruct the paper (1–4 hours, for the deep dive)

- Re-read the paper **as if you were the author**: identify the implicit assumptions, the hidden decisions, the failure modes.
- Build a **method reconstruction**: if you had to re-implement this paper from scratch, what would you build?
- Write a **critical review**: limitations, scope, threat to validity, and the **reproduction plan** that would let you (or someone else) re-run the key experiment.

---

## Output directory

Every run creates a `paper-reading-output/` directory:

```
paper-reading-output/
├── README.md
├── index.html                 # interactive reading page
├── assets/
│   ├── style.css
│   └── app.js
├── data/
│   ├── intake_quality.json
│   ├── candidate_papers.json
│   ├── source_resolution.json
│   ├── paper_metadata.json
│   ├── paper_outline.json
│   ├── paper_reading.json
│   ├── claims_evidence_map.json
│   └── figures_tables.json
└── reports/
    ├── stage0_intake_report.md
    ├── pass1_first_pass.md
    ├── pass1_five_cs.md
    ├── pass1_reading_decision.md
    ├── pass2_main_ideas.md
    ├── pass2_figures_tables.md
    ├── pass2_claims_evidence_map.md
    ├── pass2_key_references.md
    ├── pass3_reconstruction.md
    ├── pass3_critical_review.md
    ├── pass3_reproduction_plan.md
    └── final_reading_report.md
```

`index.html` is a single-file artifact with:

- Hero Summary, Paper Metadata, Intake Status
- 1-sentence / 3-sentence / 10-sentence summary
- Paper Map, Five Cs dashboard
- Pass 1 / Pass 2 / Pass 3 tabs
- Claims-Evidence Map (filterable)
- Figures & Tables, Glossary
- Method Reconstruction, Limitations, Related Work
- Reproduction Plan, Open Questions
- "Do I understand this paper?" checklist

---

## Quick start

### Render a sample page (no network needed)

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input skills/paper-three-pass-reader/examples/sample_paper_reading.json \
  --output paper-reading-output
```

Then open `paper-reading-output/index.html` in any browser.

### Create an empty skeleton for a new paper

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
  --output paper-reading-output \
  --title "Attention Is All You Need"
```

### Publish the page to GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish reading page for XYZ"
```

The script refuses to **create** a new repo silently — if `conanxin/paper-reading-pages` does not exist it prints the exact `gh repo create` command and stops.

### Two-stage workflow (URL → fill → finalize → publish)

The recommended daily workflow as of v0.3.0-alpha is two stages:

```bash
# Stage 1 — draft + fill-pack (no publish, no render)
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
    --zh --full --no-publish \
    --slug you-and-your-research \
    --output-root runs/2026-06-16 \
    --title "You and Your Research" \
    --authors "Richard W. Hamming"

# (you / an agent edits runs/2026-06-16/you-and-your-research/work/paper_reading.json
#  per the fill-pack in runs/2026-06-16/you-and-your-research/fill-pack/)

# Stage 2 — audit + zh-CN quality gate + render + publish + published-pages audit
./p3pr finalize runs/2026-06-16/you-and-your-research --publish
```

`finalize` is a thin wrapper that runs the four standard post-fill scripts (audit, quality gate, render, publish) and prints a fixed `P3PR_FINALIZE_STATUS` summary block. It carries the v0.2.15 publish-gate: if `paper-reading-output/index.html` is missing after render, finalize BLOCKs and never reaches the publisher. As of v0.2.18, the gh-pages site-path and the published page title are auto-inferred from `paper_reading.json` (explicit `--site-path` / `--page-title` still override), and the summary block is enriched with `P3PR_SITE_PATH`, `P3PR_PAGE_TITLE`, `P3PR_READING_MODE`, `P3PR_LANGUAGE`, `P3PR_AUDIT_STATUS`, `P3PR_QUALITY_GATE_STATUS`, `P3PR_WARNING_COUNT`, `P3PR_WARNING_SUMMARY`, and a state-aware `P3PR_NEXT_ACTION`. See [`skills/paper-three-pass-reader/docs/USAGE.md`](skills/paper-three-pass-reader/docs/USAGE.md) §"v0.2.18-alpha" for the full flag list and dry-run output.

### Manage runs and audit the site (v0.2.19)

```bash
# What's local, what's online
./p3pr status
./p3pr status --runs --offline --json-output status_runs.json

# Is the toolchain healthy
./p3pr doctor --offline
./p3pr doctor --full    # also runs scripts/validate.sh

# Live audit of every page on the site
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
    --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
    --site-root https://conanxin.github.io/paper-reading-pages \
    --include-root --warn-only
```

`status` and `doctor` are 100% read-only — they never write to runs, never
modify the working tree, never `chmod` anything, never re-authenticate `gh`.
See [`skills/paper-three-pass-reader/docs/STATUS_AND_DOCTOR.md`](skills/paper-three-pass-reader/docs/STATUS_AND_DOCTOR.md) for the full flag list and JSON shapes.

### Run validation

```bash
bash scripts/validate.sh
```

This is a **smoke check**, not a test suite. It runs 305 sub-checks across
23 steps: required files, sample render, mandatory page sections, every
subcommand, every published page, every block path in v0.2.15 / v0.2.17 /
v0.2.18 / v0.2.19, slugify behavior, summary block fields, the v0.2.15
publish-gate, the v0.2.18 finalize UX, status JSON shape, fake-manifest file
support, malformed-run regression, doctor offline / quick modes, dirty-tree-
as-WARN invariant.

---

## Design rationale (short version)

- **Why intake first?** Because guessing the paper is the most common failure mode. Two papers can share a name, a DOI can resolve to the wrong thing, and a screenshot might show only a figure, not the title.
- **Why three passes?** Because the same paper is a different artifact at 5 minutes, 1 hour, and 4 hours. The skill records what mode each section was written in.
- **Why Five Cs?** Because Keshav's framework survives when everything else changes — it's the cheapest way to keep yourself honest on Pass 1.
- **Why a Claims-Evidence map?** Because "the paper says X" is meaningless without the figure, table, or section that proves X.
- **Why an HTML page?** Because reading is interactive. Tabs, accordions, and a confidence filter let the same page serve a 5-minute skim and a 4-hour reconstruction.
- **Why distinguish full text / partial / abstract / screenshot?** Because pretending you read the paper when you only saw the abstract is the failure mode this skill exists to prevent.

The full rationale is in [`skills/paper-three-pass-reader/docs/DESIGN_RATIONALE.md`](skills/paper-three-pass-reader/docs/DESIGN_RATIONALE.md).

---

## Evidence discipline

Every interpretive statement in the page and reports carries a label:

- `[Paper evidence]` — direct quote or paraphrase from the paper text
- `[Figure/Table evidence]` — grounded in a specific figure/table
- `[Author claim]` — claim attributed to the authors, not yet independently checked
- `[Agent inference]` — the agent's interpretation, not in the paper itself
- `[Uncertain]` — confidence is low, evidence is thin
- `[Needs verification]` — flagged for follow-up

If you see a load-bearing claim without a label, treat it as `[Needs verification]`.

---

## Limitations (v0.1.1-alpha)

- Sample data uses S. Keshav's *How to Read a Paper* itself — a meta choice. The full pipeline works on any paper, but only the Keshav sample is pre-built into the repo.
- Stage 0 is **input-driven** — it does not fetch the paper itself. You provide the paper (or the strong hint) and the skill normalises it.
- The HTML page is **static**. There is no annotation persistence, no notes sync, no shared state.
- No PDF parsing, OCR, or web scraping is included. Bring your own text or URL.
- `publish_output_to_github.sh` is intentionally minimal — it will not roll back, retry, or reconcile. If a push fails, read the error.

## Multi-page publishing (v0.1.1+)

To publish several papers into one GitHub Pages repo, use the slug mode:

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output runs/attention-is-all-you-need-20260615/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --site-path attention-is-all-you-need \
  --page-title "Attention Is All You Need"
```

The page is copied into `gh-pages/attention-is-all-you-need/` and the repo root becomes a tiny index (`index.html` + `published_pages.json`) that lists every published page. Each call adds (or updates) one entry; other pages are preserved. The script validates the slug and refuses anything outside `[A-Za-z0-9._-]+`.

> **v0.1.2-alpha note:** the multi-page cleanup step was hardened so that re-publishing one paper never deletes another paper's subdirectory on `gh-pages`. Already-published pages survive intact.

---

## One-command runner (v0.2.0-alpha)

`skills/paper-three-pass-reader/scripts/run_paper_reading.py` turns a paper-shaped input (title, abstract, OCR transcript, repo URL, …) into a standard run directory + draft `paper_reading.json` + (optional) rendered page + (optional) published GitHub Page.

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug runner-title-attention \
  --output-root runs/runner-smoke-20260615 \
  --render --publish \
  --repo conanxin/paper-reading-pages \
  --page-title "Runner Smoke: Attention Is All You Need"
```

The runner does **not** read the paper for you — it produces a DRAFT with `[DRAFT]` placeholders that you (or an agent) fill in. It enforces reading-mode discipline, writes the standard run layout, and keeps the workflow repeatable. See [`skills/paper-three-pass-reader/docs/RUNNER.md`](skills/paper-three-pass-reader/docs/RUNNER.md) for the full interface, examples, and boundaries.

---

## Agent fill pack + audit (v0.2.1-alpha)

The runner now supports `--fill-pack` and `--audit`. They are designed to make the runner output directly usable by another agent (or a human) for follow-up reading work.

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug myrun \
  --output-root runs/ \
  --reading-mode partial_text \
  --fill-pack --audit --audit-warn-only --render
```

What gets written:

- `runs/myrun/work/paper_reading.json` — the draft.
- `runs/myrun/work/audit_result.json` — full audit JSON (status, errors, warnings, recommendations).
- `runs/myrun/reports/audit_summary.md` — markdown summary.
- `runs/myrun/fill-pack/` — 11 markdown files (`00_README.md` … `10_quality_gate.md`) + `prompts.json` + `field_checklist.json` + `draft_status.json`.
- `runs/myrun/paper-reading-output/index.html` — rendered page (only if audit does not FAIL).

Key behaviors:

- `--audit` blocks `--render` and `--publish` if audit status = FAIL (use `--audit-warn-only` to relax).
- `--fill-pack` writes per-stage step instructions adapted to the current reading mode (weak modes carry explicit "weak-input" caveats).
- `audit_paper_reading.py` can be used standalone for any `paper_reading.json`:
  ```bash
  python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
    --input runs/myrun/work/paper_reading.json \
    --json-output runs/myrun/work/audit_result.json
  ```

The audit is **structural + reading-mode discipline** only. It does not judge whether the paper is correct.

See [`skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md`](skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md) and [`skills/paper-three-pass-reader/docs/AUDIT.md`](skills/paper-three-pass-reader/docs/AUDIT.md).

---

## Version history

| Tag | Status | Purpose |
|---|---|---|
| `v0.1.0-alpha` | immutable | Initial release. |
| `v0.1.1-alpha` | immutable | Renderer hardening (loose-JSON tolerance) + multi-page publishing script. |
| `v0.1.2-alpha` | immutable | Publish-script fix that preserves sibling page subdirectories on re-publish. |
| `v0.2.0-alpha` | immutable | One-command runner for turning weak/complete inputs into a standard run layout + draft JSON + (optional) rendered/published page. |
| `v0.2.1-alpha` | immutable | Agent Fill Pack + structural audit. Runner gained `--fill-pack`, `--audit`, `--agent-profile`, `--language`, `--max-claims`, `--max-figures`. |
| `v0.2.2-alpha` | immutable | Auto-fill smoke run + runner/render robustness fixes. |
| `v0.2.3-alpha` | immutable | First-class Chinese (zh-CN) output. Runner writes `target_language` / `ui_language`; renderer localizes UI; audit checks Chinese content. |
| `v0.2.4-alpha` | immutable | zh-CN quality gate. Goes beyond "has Chinese?" to "is the Chinese actually a reading?". Catches low CJK coverage, English carryover, shallow glossary/claims/checklist, full_text with no `[Paper evidence]`. Integrated into audit (`--quality-gate`) and runner. |
| `v0.2.5-alpha` | immutable | One-line CLI `p3pr`. `./p3pr arxiv 2503.08102 --zh --full --publish` does the whole pipeline (runner + fill-pack + audit + quality gate + render + publish). 6 subcommands: arxiv / title / abstract / screenshot / repo / pdf. Enforces weak-mode / quality-gate boundaries. |
| `v0.2.6-alpha` | immutable | Shared resolver hints: `data/resolver_hints.json` is now the single source of truth, with `scripts/resolver_hints.py` and `scripts/resolve_paper_hint.py` helpers. Replaces the duplicate HINTS dict in `p3pr.py` and the duplicate `RESOLVER_HINTS` in the runner. |
| `v0.2.7-alpha` | immutable | v0.2.6 round-2 hardening, released as a new tag (v0.2.6-alpha is immutable, never re-pointed). Adds the structured top-level `source_resolution` block, the CLI→runner overlay via `work/resolver_source.json` + `--resolver-source`, and the resolver helper degradation behaviour (a broken helper now degrades to `ambiguous_clue` and the run still finishes rc=0). Validation 195/0 PASS. |
| `v0.2.10-alpha` | immutable | Published-pages regression audit. New `audit_published_pages.py` reads `published_pages.json`, fetches every page, and produces a JSON + Markdown report covering template leaks, raw dicts, old footers, weak zh-CN UI, missing Resolver Trail, missing Claims / Glossary, and essay-mode regressions. `--selftest-dir` mode is wired into `scripts/validate.sh` step 17. First live audit run found 1/9 pages at PASS. Validation 225/0 PASS. |
| `v0.2.12-alpha` | immutable | Root-index audit exemption. Adds `page_type` classification (`site_index` / `paper_page` / `manifest` / `unknown`) and exempts the root index from paper-level checks (`missing_resolver_trail` / `missing_claims_section` / `missing_glossary`). Severe checks (`template_leak` / `raw_dict` / `old_footer`) still apply to the root index. New top-level `page_type_counts` and per-page `page_type`. New `## Page Type Summary` in the Markdown report. New `--include-manifest` flag. `scripts/validate.sh` step 18 verifies the exemption against 8 selftest fixtures and the live site. Validation 236/0 PASS. |
| `v0.2.13-alpha` | immutable | Manifest link in generated root index. `publish_output_to_github.sh` now emits `<link rel="alternate" type="application/json" href="published_pages.json">` in `<head>` plus a visible `<a href="published_pages.json">` link in the About section (English + Chinese labels). `_check_site_index()` in the audit accepts both forms. The live audit's last info finding (`index_no_manifest_link`) is gone. Validation 242/0 PASS. |
| `v0.2.14-alpha` | immutable | `p3pr url <url>` subcommand. Fetch an HTML page (or PDF) from a user-supplied URL, run stdlib-only `html.parser` text extraction, and feed the result to the runner as `input_kind=paper_url` with `--input-file` + `--paper-url`. New `_HTMLTextExtractor` and `_fetch_url()` in `p3pr.py`. The runner now accepts `--input` and `--input-file` together (audit-trail string + body). Reading-mode discipline: HTML ≥800 chars → `full_text`, else `partial_text`; PDFs without body stay `partial_text`. New `P3PR_SOURCE_URL:` summary line. New `--authors` and `--year` flags exposed at CLI. Validation 261/0 PASS. Live URL smoke page (`you-and-your-research-url-smoke-cn`) published; live audit `pages=11 pass=11 warn=0 fail=0`. |
| `v0.2.15-alpha` | immutable | Block `p3pr --publish` on missing `paper-reading-output/index.html`. Surfaced by the v0.2.15 dogfood phase: the runner correctly skipped render (audit/qg FAILED) but `p3pr.py` invoked the publisher anyway and pushed a 404 stub. Hard BLOCK on missing index.html, even with `--allow-draft-publish`. New validation sub-checks at step 20l. The v0.2.15 dogfood stub was removed from `gh-pages` and the manifest. Validation 263/0 PASS. |
| `v0.3.0-alpha` | current | First **stable-readiness release candidate**. No new features. Documents: `STABLE_READINESS_CHECKLIST.md`, `RELEASE_NOTES_v0.3.0-alpha.md`, `PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md`. README.md / README.zh-CN.md Quick Start updated to show the two-stage flow + management (`status` / `doctor`) + site audit. Bug fix: `p3pr doctor` summary counter now correctly lowercases check status (was always 0/0/0 because the lookup used uppercase keys). Validation 305/0 PASS. Live audit 14/14 PASS, 0 warn, 0 fail. Doctor 24/1/0 (1 WARN is dirty working tree, expected mid-release). This is **not** v0.3.0 stable — see `STABLE_READINESS_CHECKLIST.md` §"Not yet stable". |
| `v0.2.19-alpha` | previous | `p3pr status` + `p3pr doctor` — read-only observability subcommands. `status` scans `runs/` and reads `published_pages.json`, classifying each run as `draft` / `filled` / `audited` / `rendered` / `rendered_with_warnings` / `published` / `blocked` / `unknown` and cross-referencing the manifest to flag `published` runs. `doctor` runs 7 health-check groups: local env, required scripts, required docs, git state, gh CLI / auth, optional `validate.sh`, light HEAD probe of the site. Both are read-only, both emit JSON via `--json-output`, both print fixed `P3PR_STATUS_*` / `P3PR_DOCTOR_*` summary blocks. Dirty working tree and missing gh are WARN, never FAIL. New `STATUS_AND_DOCTOR.md` doc. New validation step 23 (12 sub-checks). Validation 305/0 PASS. |
| `v0.2.18-alpha` | previous | `p3pr finalize <run-dir>` UX polish. Auto-infer the gh-pages site-path and published page title from `paper_reading.json` (explicit `--site-path` / `--page-title` still override). New summary fields: `P3PR_SITE_PATH`, `P3PR_PAGE_TITLE`, `P3PR_READING_MODE`, `P3PR_LANGUAGE`, `P3PR_AUDIT_STATUS`, `P3PR_QUALITY_GATE_STATUS`, `P3PR_WARNING_COUNT`, `P3PR_WARNING_SUMMARY` (lists up to 3 actual warnings, not a generic line). `P3PR_NEXT_ACTION` is now state-aware. Improved dry-run prints `inferred_site_path` / `inferred_page_title` with source attribution. All v0.2.15 / v0.2.17 publish guards preserved (verified by validation step 22). New validation step 22 with 14 sub-checks. Live-published dogfood at `https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-finalize-ux-cn/`. Validation 293/0 PASS. |
| `v0.2.17-alpha` | previous | `p3pr finalize <run-dir>` — the second-stage CLI. Reads `<run-dir>/work/paper_reading.json` and runs audit → zh-CN quality gate → render → optional publish → optional published-pages audit. Fixed `P3PR_FINALIZE_STATUS` summary block on every exit. With `--dry-run` prints a `P3PR_FINALIZE_DRY_RUN` plan. Carries over the v0.2.15 publish-gate: if `paper-reading-output/index.html` is missing, BLOCK. Flags: `--publish` / `--no-publish` / `--repo` / `--branch` / `--site-path` / `--page-title` / `--allow-warnings` / `--allow-draft-publish` / `--skip-quality-gate` / `--skip-published-audit` / `--dry-run`. New validation step 21 with 16 sub-checks. Live-published dogfood at `https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-finalize-cn/`. Validation 279/0 PASS. |
| `v0.2.9-alpha` | previous | Polished HTML essay / talk page rendering. Renderer no longer leaks raw `{'label': ...}` dicts, no longer leaks `{% else %}` template tags, exposes `generator_version` in the page footer, switches `Reproduction Plan` → `实践计划` for essay-mode inputs, and renders a `<details>`-based accordion. Claim IDs and glossary definitions display correctly. Re-published the Chinese *You and Your Research* page. Validation 220/0 PASS. |
| `v0.2.8-alpha` | previous | Structured `source_resolution` consumers. New `source_resolution_utils.py` is the single shared helper. Renderer, audit, fill-pack, and zh-CN quality gate all read the structured block; legacy `intake_quality.source_resolution` list is still supported via on-the-fly upgrade. Validation 210/0 PASS. |

## Language support (zh-CN / en)

As of v0.2.3-alpha, the skill carries the output language through every stage:

- **Runner** writes `target_language` and `ui_language` in the draft JSON (default `zh-CN`).
- **Fill-pack** instructions are generated in the chosen language.
- **Renderer** localizes UI labels to Chinese when `ui_language = "zh-CN"`. Section headings, tabs, accordions, metadata labels, and the Five Cs all switch.
- **Audit** checks the main interpretive fields for Chinese characters when `target_language = "zh-CN"` and warns if fewer than 50% contain them.

Evidence labels stay in English (so the audit can match them): `[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`. Paper titles, method names, benchmark names, and author names also stay in the original form the author wrote them.

To regenerate a Chinese page from an existing English draft, set `ui_language` in the JSON and re-render:

```bash
python3 -c "import json,sys; p=sys.argv[1]; d=json.load(open(p)); d['target_language']='zh-CN'; d['ui_language']='zh-CN'; open(p,'w').write(json.dumps(d,indent=2,ensure_ascii=False))" runs/myrun/work/paper_reading.json
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input runs/myrun/work/paper_reading.json \
  --output runs/myrun/paper-reading-output
```

(But really, the recommended path is: re-run with `--language zh-CN` so the fill-pack is Chinese too.)

## zh-CN quality gate

As of v0.2.4-alpha, the skill has a dedicated quality gate for Chinese output. The structural audit (`audit_paper_reading.py`) checks JSON shape and reading-mode discipline. The **quality gate** (`quality_gate_zh_cn.py`) checks whether the Chinese explanation is actually a reading — not just a UI-flip or an English carryover.

The gate catches:

- **Low CJK coverage** — fewer than 50% of the main interpretive fields contain Chinese characters.
- **Long English blobs** — single field contains 30+ consecutive ASCII characters without CJK (typical English-draft carryover).
- **Shallow glossary / claims / checklist** — fewer than 10 / 8 / 8 items respectively.
- **full_text mode with no `[Paper evidence]` claims** — all claims are `[Author claim]` or `[Uncertain]`, which is suspicious for a real reading.
- **Missing Pass 2 / Pass 3 in full_text mode** — draft was not actually written.

The gate is **structural + bilingual-discipline**, not LLM-truth-judging. It does not score translation quality subjectively.

```bash
# Standalone:
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/myrun/work/paper_reading.json

# Integrated into audit:
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/myrun/work/paper_reading.json \
  --quality-gate

# Integrated into runner:
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "..." --input-kind paper_title --slug <slug> --output-root <root> \
  --language zh-CN --fill-pack --quality-gate
```

See [`skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md`](skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md).

## One-line CLI (v0.2.5+)

You can run the whole pipeline (runner + fill-pack + audit + zh-CN quality gate + render + publish) with a single command:

```bash
./p3pr arxiv 2503.08102 --zh --full --publish
./p3pr title "Attention Is All You Need" --zh --full --publish
./p3pr abstract path/to/abstract.md --zh --publish
./p3pr screenshot path/to/transcript.md --zh --publish
./p3pr repo https://github.com/google-research/bert --zh --full --publish
./p3pr pdf path/to/paper.pdf --zh --full --publish
```

The CLI is a thin shim — it does not call external LLM APIs and does not auto-fill the draft. It just chains the existing scripts. The fill-pack is the task description; the agent / human fills it.

Every run ends with a fixed-format summary:

```
P3PR_STATUS: PASS|WARN|BLOCKED|DRY_RUN
P3PR_INPUT_KIND: paper_identifier|...
P3PR_READING_MODE: full_text|abstract_only|...
P3PR_RUN_DIR: ...
P3PR_JSON: ...
P3PR_FILL_PACK: ...
P3PR_LOCAL_PAGE: ...
P3PR_PAGE_URL: ...
P3PR_NEXT_ACTION: ...
```

See [`skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md`](skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md) for the full flag list, the dry-run behaviour, and the `--publish` / `--allow-draft-publish` distinction.

---

## License

MIT — see [`LICENSE`](LICENSE).

Version: **v0.2.14-alpha**. Previous: v0.2.13-alpha (immutable, kept for reproducibility).
