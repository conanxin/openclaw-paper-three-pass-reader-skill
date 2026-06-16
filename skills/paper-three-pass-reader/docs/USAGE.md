# Usage Guide

This document shows how to use `paper-three-pass-reader` end-to-end. Every example assumes you are at the repository root unless noted otherwise.

---

## 1. Render the bundled sample (no network, no paper needed)

The repo ships with a worked example built from S. Keshav's *How to Read a Paper* (2007). Use it to verify your setup, to learn the schema, or as a template for your own reading.

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
    --input skills/paper-three-pass-reader/examples/sample_paper_reading.json \
    --output paper-reading-output
```

Open `paper-reading-output/index.html` in any browser. The page is fully offline — no fetch, no CDN.

---

## 2. Start a fresh reading for a new paper

### 2a. Create the skeleton

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
    --output paper-reading-output \
    --title "Attention Is All You Need"
```

This produces:

```
paper-reading-output/
├── README.md
├── index.html       # placeholder page
├── assets/{style.css, app.js}
├── data/            # 8 empty JSON files
└── reports/         # 12 placeholder Markdown files
```

### 2b. Fill `data/paper_reading.json` as you read

Open `data/paper_reading.json`. The schema is documented in `OUTPUT_SCHEMA.md`. Fill the fields as you complete each stage:

- Stage 0 → `paper_metadata`, `intake_quality`, `source_resolution`, `candidate_papers`
- Stage 1 → `five_cs`, `pass1.*`
- Stage 2 → `pass2.*`, `claims_evidence_map`, `figures_tables`
- Stage 3 → `pass3.*`, `glossary`, `limitations`, `reproduction_plan`, `open_questions`, `final_checklist`

### 2c. Re-render

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
    --input paper-reading-output/data/paper_reading.json \
    --output paper-reading-output
```

The script overwrites `index.html`, refreshes all `data/*.json` mirrors, and regenerates every `reports/*.md`.

---

## 3. Input examples

### 3a. PDF input

Drop the PDF somewhere and feed its path as the `source_kind` value plus a small wrapper:

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
    --output paper-reading-output \
    --title "Whatever — from PDF"
# Edit data/paper_reading.json:
#   paper_metadata.source_kind = "complete_paper"
#   paper_metadata.identifiers.url = "file:///abs/path/to/paper.pdf"
#   intake_quality.input_kind = "complete_paper"
#   intake_quality.reading_mode = "full_text"
```

> The skill does **not** extract text from the PDF itself. Provide the text upstream (via `pdf-to-markdown-pipeline` or your own reader) and feed the result into `paper_reading.json`.

### 3b. Title-only input

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
    --output paper-reading-output \
    --title "How to Read a Paper"
# Edit data/paper_reading.json:
#   paper_metadata.source_kind = "paper_title"
#   intake_quality.input_kind  = "paper_title"
#   intake_quality.reading_mode = "abstract_only"   # until you find the PDF
#   intake_quality.warnings     = ["Title only — abstract not yet fetched"]
```

When you later find the abstract or the full PDF, edit the file and re-render.

### 3c. Screenshot input

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
    --output paper-reading-output \
    --title "(from screenshot — see data/intake_quality.json)"
# Edit data/paper_reading.json:
#   paper_metadata.source_kind = "paper_screenshot"
#   intake_quality.input_kind  = "paper_screenshot"
#   intake_quality.reading_mode = "screenshot_only"
#   intake_quality.warnings     = [
#     "OCR/VLM not run; only visual inspection so far.",
#     "Title, authors and year were inferred from the screenshot."
#   ]
```

If you later run OCR or VLM and produce text, paste the text into `paper_metadata` and update `reading_mode` to `partial_text` or `full_text`.

### 3d. arXiv input

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
    --output paper-reading-output \
    --title "(arXiv 2301.12345)"
# Edit data/paper_reading.json:
#   paper_metadata.identifiers.arxiv_id = "2301.12345"
#   paper_metadata.identifiers.url      = "https://arxiv.org/abs/2301.12345"
#   paper_metadata.source_kind          = "paper_identifier"
#   intake_quality.input_kind           = "paper_identifier"
```

### 3e. GitHub repo input

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
    --output paper-reading-output \
    --title "(paper for github.com/HazyResearch/safari)"
# Edit data/paper_reading.json:
#   paper_metadata.source_kind = "project_or_repo"
#   intake_quality.input_kind  = "project_or_repo"
#   intake_quality.warnings    = [
#     "Repo identified; accompanying paper not yet located — see candidate_papers.json."
#   ]
```

Fill `candidate_papers.json` with a ranked shortlist of papers that might be associated with the repo, then ask the user to confirm.

---

## 4. Reading modes

```bash
# Pass 1 only — quick triage, no Pass 2 / Pass 3 content
# Just leave pass2.* and pass3.* empty in paper_reading.json and re-render.

# Full reading — all three passes deep
# Fill everything.
```

The HTML page surfaces the reading mode as a badge in the hero. Pass 2 and Pass 3 sections degrade gracefully when empty (no errors, but the timeline dots are not "done").

---

## 5. Publish the page to GitHub Pages

### 5a. Single-page mode (legacy)

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
    --output paper-reading-output \
    --repo conanxin/paper-reading-pages \
    --branch gh-pages \
    --message "Publish reading page for XYZ"
```

The entire `gh-pages` branch is replaced with the output dir. Use this when the repo only ever holds one page.

### 5b. Multi-page mode (v0.1.1+)

When the repo holds several papers, use `--site-path` so each paper lives in its own subdirectory:

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
    --output runs/attention-is-all-you-need-20260615/paper-reading-output \
    --repo conanxin/paper-reading-pages \
    --branch gh-pages \
    --site-path attention-is-all-you-need \
    --page-title "Attention Is All You Need"
```

The page lives at `https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/`. The repo root becomes a small index page listing every published paper. Re-publishing the same paper updates the entry (no duplicate); other papers are untouched.

The script refuses `--site-path` values outside `[A-Za-z0-9._-]+` (no path separators, no whitespace).

Prerequisites:

- `gh` CLI installed and authenticated (`gh auth status`).
- Target repo `conanxin/paper-reading-pages` already exists and is visible to your `gh` account.
- The script **will not** silently create the repo. If it does not exist, the script prints the exact `gh repo create` command.

See `GITHUB_PAGES_PUBLISHING.md` for the full flow.

---

## 6. Validate before publishing

```bash
bash scripts/validate.sh
```

This is a **smoke check**, not a test suite. It verifies file presence, JSON validity, the sample render, and that the page contains the expected sections.

---

## 7. Working with agents

The skill is designed so an AI agent can fill `paper_reading.json` stage by stage:

1. The agent performs Stage 0 and updates `paper_metadata.json` + `intake_quality.json` + `source_resolution.json`.
2. The agent performs Stage 1 and updates `five_cs` + `pass1.*`.
3. … and so on.
4. Between passes, the human can read `reports/passN_*.md` to check the agent's interpretation.
5. When all passes are done, run `render_page.py` to produce `index.html`.

Every interpretive statement in the JSON should carry an evidence label so the human can audit the agent's reading at a glance.

---

## v0.2.1-alpha: fill pack + audit

The runner now supports `--fill-pack` and `--audit`. Use these when you want another agent (or a human) to fill in the draft JSON in a guided way.

### Generate draft + fill pack + audit + render (one command)

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "Attention Is All You Need" \
    --input-kind paper_title \
    --slug myrun \
    --output-root runs/ \
    --reading-mode partial_text \
    --fill-pack --audit --audit-warn-only --render
```

### Audit only

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
    --input runs/myrun/work/paper_reading.json \
    --json-output runs/myrun/work/audit_result.json
```

### Fill pack only (without render)

```bash
python3 skills/paper_reading.py \
    --input "How to Read a Paper" \
    --input-kind paper_title \
    --slug myrun \
    --output-root runs/ \
    --fill-pack
```

The fill pack lands at `runs/myrun/fill-pack/` with 11 markdown files and 3 JSON files.

### Upgrade weak → full

1. Place the body text at `runs/myrun/extracted/full_body.txt`.
2. Re-run with `--reading-mode full_text` (overrides the kind-forced mode).
3. Re-run audit; claims can now carry `[Paper evidence]` / `[Figure/Table evidence]`.


### Generate a Chinese (zh-CN) page

The skill supports first-class Chinese output. Pass `--language zh-CN` to the runner and the entire downstream pipeline (fill-pack, audit, render) will produce Chinese output:

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "arXiv:2503.08102 — Second Me: Human-Inspired Memory Mechanism for LLM Agents" \
  --input-kind paper_identifier \
  --slug second-me-human-inspired-memory-cn \
  --output-root runs/second-me-zh-cn-20260615 \
  --title "Second Me: Human-Inspired Memory Mechanism for LLM Agents" \
  --arxiv-id "2503.08102" \
  --reading-mode full_text \
  --language zh-CN \
  --fill-pack \
  --audit
```

The renderer will:

- Show Chinese UI labels: "输入解析状态" (Intake Status), "第一遍阅读" (Pass 1), "主张—证据地图" (Claims → Evidence Map), "最终理解检查表" (Final Checklist), etc.
- Keep evidence labels in English (so the audit can match them).
- Keep paper titles, method names, and author names in their original form.

### Regenerate a Chinese page from an existing English draft

If you already have an `en` draft, you can flip it to `zh-CN` and re-render. The explanatory content stays English (the renderer only localizes the UI chrome), so for a real Chinese reading you should re-run with `--language zh-CN` and re-fill.

```bash
# Quick UI flip (chrome-only, content stays English):
python3 -c "import json; p='runs/myrun/work/paper_reading.json'; d=json.load(open(p)); d['target_language']='zh-CN'; d['ui_language']='zh-CN'; open(p,'w').write(json.dumps(d,indent=2,ensure_ascii=False))"
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input runs/myrun/work/paper_reading.json \
  --output runs/myrun/paper-reading-output
```

### Run the zh-CN quality gate

After filling a zh-CN draft, run the quality gate to make sure the Chinese explanation is a real reading:

```bash
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/myrun/work/paper_reading.json \
  --json-output runs/myrun/work/quality_gate_zh_cn.json
```

The gate checks:

- Language fields are `zh-CN`.
- ≥ 50% of main interpretive fields contain CJK characters.
- No field contains a long English blob (≥ 30 ASCII chars, no CJK).
- glossary ≥ 10, claims_evidence_map ≥ 8, final_checklist ≥ 8.
- full_text: at least one `[Paper evidence]` claim; not all `[Author claim]`.
- full_text: Pass 2 main_ideas and Pass 3 method_reconstruction non-empty.

The gate is **structural + bilingual-discipline**, not an LLM truth judgment. It catches specific failure modes (English carryover, shallow glossary, missing Pass 2/3) that the structural audit alone misses.

For weak-mode drafts, pass `--warn-only` so that WARN doesn't block render:

```bash
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/weak-myrun/work/paper_reading.json \
  --warn-only
```

You can also have the runner or audit invoke it automatically:

```bash
# Via the runner (blocks render on FAIL):
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "..." --input-kind paper_title --slug <slug> --output-root <root> \
  --language zh-CN --fill-pack --quality-gate

# Via the audit (no render):
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/myrun/work/paper_reading.json \
  --quality-gate
```

### One-line CLI (v0.2.5+)

For the common case, use the `p3pr` shell shim:

```bash
./p3pr arxiv 2503.08102 --zh --full --publish
```

The CLI chains everything in this doc:

1. Builds a run layout under `runs/p3pr-cli-YYYYMMDD/<slug>/`.
2. Invokes `run_paper_reading.py` to write `work/paper_reading.json` + fill-pack.
3. Runs `audit_paper_reading.py` (with `--quality-gate` for zh-CN).
4. Runs `render_page.py`.
5. Runs `publish_output_to_github.sh`.

Every run ends with a fixed-format `P3PR_*` summary. See [`ONE_LINE_CLI.md`](ONE_LINE_CLI.md).


## v0.2.17-alpha: `p3pr finalize <run-dir>` — the second-stage CLI

`p3pr finalize` is the missing half of the daily workflow. It takes a run
directory that already has a filled `work/paper_reading.json` and runs the
second stage for you:

```bash
# Stage 1: draft + fill-pack (no publish, no render)
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
    --zh --full --no-publish \
    --slug you-and-your-research \
    --output-root runs/2026-06-16 \
    --title "You and Your Research" \
    --authors "Richard W. Hamming"

# (you / an agent edits runs/2026-06-16/you-and-your-research/work/paper_reading.json
#  per the fill-pack in runs/2026-06-16/you-and-your-research/fill-pack/)

# Stage 2: audit + zh-CN quality gate + render + publish + published-pages audit
./p3pr finalize runs/2026-06-16/you-and-your-research --publish
```

### What finalize does

1. **Reads** `<run-dir>/work/paper_reading.json` (refuses to run if missing).
2. **Audit** via `audit_paper_reading.py` → `work/audit_final.json`.
   - On `FAIL`, finalize BLOCKs — fix the JSON and re-run.
3. **zh-CN quality gate** (only if `target_language` / `ui_language` is `zh-CN`) → `work/quality_gate_zh_cn.json`.
   - On `WARN` and `--allow-warnings` set: continue.
   - On `FAIL`: BLOCK unless `--allow-draft-publish` is set.
4. **Render** via `render_page.py` → `<run-dir>/paper-reading-output/`.
5. **Hard guard:** if `paper-reading-output/index.html` does not exist after
   render, finalize BLOCKs (the v0.2.15 publish-gate). This prevents empty
   404 stubs from being pushed to `gh-pages`.
6. **Publish** (only if `--publish`): `publish_output_to_github.sh` →
   `gh-pages` of the configured repo.
7. **Published-pages audit** (default on after publish; skip with
   `--skip-published-audit`) → `<run-dir>/work/published_pages_audit_after_finalize.json`
   and `<run-dir>/reports/published_pages_audit_after_finalize.md`.

### What finalize does NOT do

- **It does not auto-fill the draft.** finalize is for the second stage; the
  first stage (filling `paper_reading.json` per the fill-pack) is the human
  / agent's responsibility. If you want LLM-driven fill, run it separately
  and then call finalize.
- **It does not re-fetch the URL.** finalize only reads what's on disk.
  If the run was created by `p3pr url`, the body is in `<run-dir>/extracted/`
  — but finalize does not consult it.
- **It does not push to a non-default repo's published-pages audit.** If
  `--repo` is not `conanxin/paper-reading-pages`, the published-pages audit
  is skipped (with a warning) to avoid false negatives.

### Flags

```text
./p3pr finalize <run-dir>
  --publish / --no-publish        (default: --no-publish)
  --repo <owner>/<name>           (default: conanxin/paper-reading-pages)
  --branch <branch>               (default: gh-pages)
  --site-path <slug>              (default: <run-dir> basename)
  --page-title <title>            (default: paper_metadata.title)
  --allow-warnings                (default: off — WARN blocks publish)
  --allow-draft-publish           (default: off — quality-gate FAIL blocks publish;
                                   audit FAIL or missing index.html still block)
  --skip-quality-gate             (default: off — auto-on for zh-CN)
  --skip-published-audit          (default: off — runs after publish)
  --dry-run                       (print plan, do nothing)
```

### Dry-run

```bash
./p3pr finalize runs/2026-06-16/you-and-your-research --publish --dry-run
```

emits a fixed `P3PR_FINALIZE_DRY_RUN` block showing what would happen, with
no side effects:

```
P3PR_FINALIZE_DRY_RUN
P3PR_RUN_DIR: .../runs/2026-06-16/you-and-your-research
would_read_json: .../work/paper_reading.json
would_audit: True (audit_paper_reading.py)
would_quality_gate: True (zh-CN detected: zh-CN/zh-CN; skip_quality_gate=False)
would_render: True (render_page.py → .../paper-reading-output)
would_publish: True (repo=conanxin/paper-reading-pages, branch=gh-pages)
site_path: you-and-your-research
page_title: You and Your Research
published_audit_after_publish: True
```

### Summary block on every exit

```text
P3PR_FINALIZE_STATUS: PASS | WARN | BLOCKED
P3PR_RUN_DIR: <run-dir>
P3PR_JSON: <run-dir>/work/paper_reading.json
P3PR_AUDIT_JSON: <run-dir>/work/audit_final.json
P3PR_QUALITY_GATE_JSON: <run-dir>/work/quality_gate_zh_cn.json (or empty)
P3PR_LOCAL_PAGE: <run-dir>/paper-reading-output/index.html
P3PR_PAGE_URL: <public URL> (or empty)
P3PR_PUBLISHED_AUDIT_JSON: <run-dir>/work/published_pages_audit_after_finalize.json (or empty)
P3PR_NEXT_ACTION: <text>
```

`P3PR_FINALIZE_STATUS` is one of `PASS` (audit PASS, qg PASS/WARN, render OK,
publish OK), `WARN` (publish OK with quality-gate WARN and no
`--allow-warnings`), or `BLOCKED` (audit FAIL, qg FAIL without override,
render FAIL, missing index.html, missing work/paper_reading.json, or publish
FAIL).

### Examples

Local render only (no publish, no network):

```bash
./p3pr finalize runs/2026-06-16/you-and-your-research --no-publish
# → P3PR_FINALIZE_STATUS: PASS or WARN
# → P3PR_PAGE_URL: (empty)
# → P3PR_LOCAL_PAGE: .../paper-reading-output/index.html
```

Publish to a custom slug:

```bash
./p3pr finalize runs/2026-06-16/you-and-your-research \
    --publish \
    --site-path you-and-your-research-2026-06-16 \
    --page-title "You and Your Research (Jun 2026 re-render)"
```

Publish even when quality-gate reports FAIL (only if you know what you're
doing — `audit FAILED` and missing `index.html` will still BLOCK):

```bash
./p3pr finalize runs/2026-06-16/you-and-your-research \
    --publish --allow-warnings --allow-draft-publish
```

---

## Cross-links

- Source resolution: see [`SOURCE_RESOLUTION.md`](SOURCE_RESOLUTION.md) for the canonical top-level `source_resolution` object and the legacy `intake_quality.source_resolution` list.
- Resolver trail in the rendered page, audit, fill-pack checklist, and zh-CN quality-gate check all consume that same object.

---

## v0.2.18-alpha: `p3pr finalize <run-dir>` UX polish

`finalize` now infers the gh-pages site-path and the published page title from
`paper_reading.json` — no more passing `--site-path` / `--page-title` on the
two-stage flow. The summary block is also enriched and the `P3PR_NEXT_ACTION`
line now tells the operator exactly what to do next.

### Recommended two-stage flow

```bash
# Stage 1 — draft + fill-pack (no publish, no render)
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
    --zh --full --no-publish

# (fill work/paper_reading.json per the fill-pack)

# Stage 2 — audit + zh-CN quality gate + render + publish + published-pages audit
./p3pr finalize <run-dir> --publish
```

The site-path and page-title come from the run's `paper_reading.json`. The
operators can still override either with `--site-path` / `--page-title`.

### Inference precedence

- **site-path** — explicit `--site-path` → `paper_metadata.page_slug` /
  `slug` / `default_slug` → slugified `paper_metadata.title` → run-dir basename.
  CJK-only titles reach the run-dir fallback (no pypinyin dependency).
- **page-title** — explicit `--page-title` → `paper_metadata.page_title` → for
  zh-CN runs `paper_metadata.title_zh` / `title_zh_cn` → `paper_metadata.title`
  → run-dir basename. The English title is preserved (no auto-translation).

### Dry-run improvements

```text
P3PR_FINALIZE_DRY_RUN: true
would_read_json: .../work/paper_reading.json
would_audit: True (audit_paper_reading.py)
would_quality_gate: True (target_language=zh-CN, ui_language=zh-CN, skip_quality_gate=False)
would_render: True (render_page.py → .../paper-reading-output)
would_publish: True (repo=conanxin/paper-reading-pages, branch=gh-pages)
inferred_site_path: you-and-your-research (source: auto from paper_reading.json / run-dir)
inferred_page_title: You and Your Research (source: auto from paper_reading.json)
P3PR_SITE_PATH: you-and-your-research
P3PR_PAGE_TITLE: You and Your Research
P3PR_READING_MODE: full_text
P3PR_LANGUAGE: zh-CN/zh-CN
published_audit_after_publish: True
```

When `--site-path` / `--page-title` is explicit the `source:` line flips to
"explicit --site-path" / "explicit --page-title" so the operator can see the
override at a glance.

### Richer summary block

Every finalize exit now prints:

```text
P3PR_FINALIZE_STATUS: PASS | WARN | BLOCKED
P3PR_RUN_DIR: <path>
P3PR_READING_MODE: full_text
P3PR_LANGUAGE: zh-CN/zh-CN
P3PR_SITE_PATH: ...
P3PR_PAGE_TITLE: ...
P3PR_JSON: .../work/paper_reading.json
P3PR_AUDIT_JSON: .../work/audit_final.json
P3PR_AUDIT_STATUS: PASS | WARN | FAIL | unknown
P3PR_QUALITY_GATE_JSON: .../work/quality_gate_zh_cn.json
P3PR_QUALITY_GATE_STATUS: PASS | WARN | FAIL | skipped | unknown
P3PR_LOCAL_PAGE: .../paper-reading-output/index.html
P3PR_PAGE_URL: https://...github.io/.../<site-path>/
P3PR_PUBLISHED_AUDIT_JSON: .../work/published_pages_audit_after_finalize.json
P3PR_WARNING_COUNT: N
P3PR_WARNING_SUMMARY: <up to 3 actual warnings, ' | '-joined, with '... (+N more)' tail>
P3PR_NEXT_ACTION: <state-aware one-liner — see below>
```

`P3PR_WARNING_SUMMARY` reads the actual warning entries from
`audit_final.json` and `quality_gate_zh_cn.json` (whichever is present), keeps
only `severity == warn|warning`, and emits up to 3 lines joined with ` | `.
Empty case: `P3PR_WARNING_COUNT: 0`, `P3PR_WARNING_SUMMARY: no warnings`.

`P3PR_NEXT_ACTION` is state-aware:

- **BLOCKED audit FAIL** — "audit FAILED. Edit `<work_json>` and re-run `./p3pr finalize <run_dir>`."
- **BLOCKED quality-gate FAIL** — "quality gate FAILED. Edit `<work_json>` and re-run finalize, or pass `--allow-draft-publish` to publish the draft as-is."
- **BLOCKED quality-gate WARN** (no publish requested) — "quality gate WARN. Re-run with `--allow-warnings` to publish, or edit `<work_json>` to address the warnings."
- **PASS** + published — "Done. Page published: `<url>`. Re-run the same command to re-publish."
- **PASS** + not published — "Done. Local page rendered. Re-run `./p3pr finalize <run_dir> --publish` to publish."
- **WARN** + non-blocking warnings — "Review N warning(s) in .../work/quality_gate_zh_cn.json (or audit_result.json). Re-run with `--allow-warnings` if acceptable."

### When to use `--allow-warnings`

Use it for English-source papers whose long English blobs in summary fields
trip the quality gate's "long English blob" warning. The warning is real but
expected for English-source drafts translated into zh-CN output. Do not use
it to silence structural errors.

### Compatibility

- All v0.2.15 / v0.2.17 publish guards are preserved (verified by validation
  step 22).
- All existing finalize flags are unchanged.
- Existing run directories and existing published pages are unchanged.
- No old tags moved.

---

## v0.2.19-alpha: `p3pr status` + `p3pr doctor` — read-only observability

As the project grows, two questions keep coming up: "where are my runs and
pages" and "is the toolchain healthy". v0.2.19 adds two read-only
observability subcommands to answer them.

### `./p3pr status`

```bash
./p3pr status                                # default: both runs + site
./p3pr status --runs                         # local runs only
./p3pr status --site                         # site manifest only
./p3pr status --offline                      # runs scan + site summary in WARN mode
./p3pr status --runs --json-output status_runs.json
./p3pr status --site --manifest-file ./local_manifest.json
```

The full flag list, run-status taxonomy, and JSON shape are documented in
[`STATUS_AND_DOCTOR.md`](STATUS_AND_DOCTOR.md).

### `./p3pr doctor`

```bash
./p3pr doctor                                # quick (no validation)
./p3pr doctor --offline                      # quick + no HTTP probes
./p3pr doctor --full                         # runs scripts/validate.sh
./p3pr doctor --skip-validation              # skip validation, still probe
./p3pr doctor --offline --json-output doctor.json
```

The 7 check groups: local env (python3, git, p3pr shim), required scripts,
required data/docs, git state, gh CLI / auth, optional `validate.sh`, light
HEAD probe of the site. Doctor never modifies runs, never runs `git clean`,
never `chmod`s anything, never re-authenticates `gh`. It just reports.

### Why dirty tree / missing gh are WARN, not FAIL

Doctor is meant to be safe to run any time, including mid-edit. A dirty
working tree is normal during development; `gh` not being logged in is only
a problem for publish flows. Both surface as WARN with a `→` recommendation
line; the operator decides what to do.

### Recommended daily checks

```bash
./p3pr status                       # what's local, what's online
./p3pr doctor --offline             # is the toolchain healthy
./p3pr doctor --full                # pre-release, also runs validation
```

### Compatibility

- All v0.2.15 / v0.2.17 / v0.2.18 publish guards and finalize UX are
  preserved (verified by validation step 23).
- All existing finalize flags are unchanged.
- Existing run directories and existing published pages are unchanged.
- No old tags moved.

---

## v0.2.9-alpha: HTML essay / talk page rendering

As of v0.2.9, the renderer classifies inputs as `essay / talk` when the paper category is one of `essay / talk / keynote / lecture / opinion / blog-distillation` and switches the page layout accordingly.

### What changes for essay / talk inputs

- `Reproduction Plan` is renamed `实践计划 / Practical Plan` and renders 7/30/90-day plans, success criteria, and risks derived from the source's own practical advice.
- `Figures & Tables` shows `原文无传统图表` followed by conceptual notes (e.g. Hamming's 5 most-quoted frameworks) instead of an empty table.
- `Related Work` is renamed `相关脉络` and shows a clean fallback note for inputs that have no formal related-work section.
- The page footer reads `paper-three-pass-reader v0.2.9-alpha` (no stale `v0.1.0-alpha` carryover).

### Re-publish the Chinese *You and Your Research* page

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output runs/you-and-your-research-20260615/you-and-your-research-cn/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --site-path you-and-your-research-cn \
  --page-title "You and Your Research：如何选择重要问题并做好研究" \
  --message "Polish You and Your Research Chinese reading page"
```

### Validation is now 220/0 PASS

`scripts/validate.sh` step 5 no longer asserts a literal `class="accordion"` — the new template uses native `<details>` markup (13 instances in the bundled sample render). The check now accepts either form via a `details / accordion` regex.

---

## v0.2.10-alpha: published-pages regression audit

`audit_published_pages.py` is the canonical tool for checking which live pages still carry legacy-render artefacts. It's read-only — it never writes to `gh-pages`, never republishes anything.

### Run the live audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --json-output runs/published-pages-audit-20260615/audit.json \
  --markdown-output runs/published-pages-audit-20260615/audit.md \
  --include-root \
  --warn-only
```

The output JSON contains per-page status (PASS / WARN / FAIL), per-issue code/severity/message/recommendation, and a top-level `recommendations` block.

### When to run

- Before any new release — make sure the previous release's "PASS page" is still passing after the renderer template was edited.
- After bumping the renderer version — catch any new regressions.
- Monthly — spot-check the live site is still healthy.
- Before deciding to republish a batch of pages — confirm which pages actually need republishing.

### Selftest

```bash
mkdir -p /tmp/p3pr-selftest
# (copy or create fake-*.html fixtures; validate.sh does this automatically)
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --selftest-dir /tmp/p3pr-selftest \
  --json-output /tmp/selftest-audit.json \
  --markdown-output /tmp/selftest-audit.md
```

The selftest is wired into `scripts/validate.sh` step 17, so `bash scripts/validate.sh` will exercise it automatically.

### Severity reference

| Code | Severity | What it means |
|---|---|---|
| `template_leak` | error | `{% %}` / `{{ }}` / `{% else %}` / `{# #}` / `No key references recorded` in the body. |
| `old_footer` | error | `v0.1.0-alpha` (any variant) in the body. |
| `raw_dict` | error | `{'label': …` raw Python dict in the body. |
| `http_error` | error | Non-200 HTTP status. |
| `empty_body` | error | Body < 200 bytes. |
| `missing_resolver_trail` | warning | No Resolver Trail / 解析状态 block. |
| `missing_claims_section` | warning | No Claims / Evidence section. |
| `missing_glossary` | warning | No Glossary / 关键术语. |
| `zh_cn_markers_weak` | warning | zh-CN page has fewer than 5 of 6 zh-CN UI markers. |
| `essay_missing_markers` | warning | Essay / talk page missing 实践计划 / 结构说明 / 相关脉络. |
| `empty_claim_id` | warning | `<code></code>` empty cells in the claims table. |
| `glossary_no_explicit_definition` | info | Glossary chips without `chip-body` definition block. |
| `no_visible_claim_id` | info | No `>C\d{2,}<` claim ID. |
| `no_evidence_label` | info | No evidence label. |

### Overall status

- `PASS` — manifest readable, every page 200, no error issues.
- `WARN` — every page 200, no error issues, but warnings exist.
- `FAIL` — manifest unreadable or at least one page has an error issue.

Pass `--strict` to promote WARN to FAIL (useful for CI gates).

See [`PUBLISHED_PAGES_AUDIT.md`](PUBLISHED_PAGES_AUDIT.md) for the full reference.

---

## v0.2.12-alpha: page-type classification + root-index exemption

The root index `<site_root>/` is a **manifest of all published pages**, not a
paper reading page. Pre-v0.2.12-alpha audits ran every page in the manifest
through the same paper-level check set, which produced three false-positive
warnings on the root index:

- `missing_resolver_trail` — by design, the index has no Resolver Trail.
- `missing_claims_section` — by design, the index has no Claims / Evidence.
- `missing_glossary` — by design, the index has no Glossary.

Starting with v0.2.12-alpha, every audited page is classified into one of four
`page_type` values: `site_index` / `paper_page` / `manifest` / `unknown`.

| `page_type` | What runs |
|---|---|
| `site_index` | Index-specific checks (title, ≥1 link, manifest reference, link-vs-manifest delta). Severe checks (template_leak, raw_dict, old_footer) still run. Paper-level checks are skipped by design. |
| `paper_page` | Full paper-level check set. |
| `manifest` | Manifest shape checks (JSON valid, `pages` list, every entry has `slug`+`title`+`path`, no duplicate slugs/paths). |
| `unknown` | Treated as `paper_page` (safe default). |

### New CLI flag

- `--include-manifest` — also audit the `published_pages.json` JSON itself
  (classified as `manifest`). Defaults to off; only enable when you want to
  check the manifest shape.

### Output JSON schema additions

- `schema_version`: bumped from `0.1.0` to `0.2.0`.
- Top-level `page_type_counts` object: `{site_index, paper_page, manifest, unknown}`.
- Each `pages[*]` entry gets a `page_type` field.

The Markdown report gains a `## Page Type Summary` table.

### Live audit example

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --include-root \
  --include-manifest \
  --json-output runs/published-pages-audit-20260615-root-index-exemption/audit.json \
  --markdown-output runs/published-pages-audit-20260615-root-index-exemption/audit.md \
  --warn-only
```

Output:

```
[audit] overall=PASS pages=10 pass=10 warn=0 fail=0
```

`page_type_counts`:

```json
{"site_index": 1, "paper_page": 9, "manifest": 0, "unknown": 0}
```

The `recommendations` block surfaces the rule:

```
Root index is treated as site_index and exempted from paper-page checks
(missing_resolver_trail / missing_claims_section / missing_glossary skipped by design).
```

### What still fails on the root index

The three severe checks (`template_leak`, `raw_dict`, `old_footer`) **still run**
on `site_index` pages — they would still be real regressions. A root index that
inadvertently leaks `{% else %}` would still fail the audit; the exemption is
only against paper-level content checks.

---

## v0.2.13-alpha: root index links to the manifest

The root index `<site_root>/` is regenerated by `publish_output_to_github.sh`
every time a page is published. As of v0.2.13-alpha, the regenerated index
carries two manifest links so users and tools can discover
`published_pages.json` from the index page itself.

### What's emitted

```html
<!-- in <head> -->
<link rel="alternate" type="application/json"
      href="published_pages.json"
      title="Published pages manifest" />

<!-- in the About section -->
<p>Machine-readable manifest: <a href="published_pages.json">published_pages.json</a>
   &middot; <a href="published_pages.json" hreflang="zh-CN">页面清单 JSON</a></p>
```

- `<link rel="alternate" type="application/json">` is the standard
  machine-readable manifest discovery convention.
- The visible `<a>` link in About is for human readers (with English and
  Chinese labels).

### How the audit reacts

`_check_site_index()` in `audit_published_pages.py` now accepts either
form. A root index that has one of these manifest links will no longer
trigger the `index_no_manifest_link` info finding.

A root index without any manifest link (older hand-written pages, etc.)
still triggers the info-level finding — the check is not silently
disabled, only satisfied by the new publisher.

### Live audit after republishing

Republish one stable page (e.g. `you-and-your-research-cn`) with the
current `publish_output_to_github.sh` to refresh the root index. Wait
for the GitHub Pages CDN to settle (~20 s), then re-run the live audit:

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --include-root --warn-only
```

Output:

```
[audit] overall=PASS pages=10 pass=10 warn=0 fail=0
```

`issues_by_severity`: `{error: 0, warning: 0, info: 8}` — one fewer than
v0.2.12-alpha (no more `index_no_manifest_link` on the live site).

### Compatibility

- `published_pages.json` schema is unchanged.
- Existing pages remain readable. Only `you-and-your-research-cn` was
  republished in this cycle (as the trigger to refresh the root index).
- Old root indexes (no manifest link) still pass — they just emit
  `index_no_manifest_link` as advisory info.

---

## v0.2.14-alpha: `p3pr url <url>` subcommand

The `url` subcommand lets you point P3PR at any HTML academic article, talk
slides, or method essay on the public web and run the full
runner / fill-pack / audit / quality-gate / render / publish pipeline.
No more hand-wired `curl + html.parser + runner`.

### What it does

```bash
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
  --zh --full --publish
```

Sub-steps:

1. Save the URL to `<run>/input/source_pointer.txt`.
2. Fetch the URL to `<run>/source/source.html` (or `<run>/source/source.pdf`
   for PDF responses, auto-detected by URL suffix / `Content-Type` / `%PDF-`
   magic bytes).
3. Run a stdlib `html.parser` extraction to plain text
   (`<run>/extracted/page.txt`). Drops `<script>` / `<style>`. Preserves
   block-level separators (`p`, headings, lists, `br`, `pre`). Captures
   `<title>`. No external dependency.
4. Hand the extracted text to the runner via
   `--input-file <extracted/page.txt> --input-kind paper_url --paper-url <url>`.
5. Optional: fill-pack, audit, quality gate, render, publish — same as the
   other subcommands.

### Reading-mode discipline

- HTML extraction produces **≥ 800 chars** → `reading_mode = full_text`.
- HTML extraction produces **< 800 chars** → `reading_mode = partial_text`.
- **PDF without extracted body** (no `pdftotext`) → stays at `partial_text`;
  we do **not** pretend a PDF without text is `full_text`. Recommendation
  in the summary will suggest `./p3pr pdf <downloaded.pdf>`.
- User `--full / --partial / --abstract-only / --screenshot-only` always
  override.

### What it is and is not

- ✅ Suitable for: HTML academic articles, talk transcripts, lecture notes,
  long-form essays, research-method posts, plain HTML paper web pages.
- ❌ **Not** suitable for: JavaScript-heavy SPA pages (the stdlib parser
  does not execute JS). For those, manually pre-extract with a JS-capable
  tool and use `./p3pr abstract path/to/text.md` instead.
- ❌ **Not** suitable for: a PDF-only URL. The CLI saves the PDF to
  `source/source.pdf` but cannot extract text without `pdftotext`. Use
  `./p3pr pdf path/to/local.pdf` for that.

### Full example

```bash
# Real URL, zh-CN, full reading, fill-pack + audit + render
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
  --zh --full --no-publish \
  --slug you-and-your-research-cn-url-smoke \
  --output-root runs/p3pr-url-smoke-20260616 \
  --title "You and Your Research" \
  --authors "Richard W. Hamming"
```

Output ends with the standard P3PR summary plus a new `P3PR_SOURCE_URL:` line:

```
P3PR_STATUS: PASS
P3PR_INPUT_KIND: paper_url
P3PR_READING_MODE: full_text
P3PR_RUN_DIR: runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke
P3PR_JSON: runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/work/paper_reading.json
P3PR_FILL_PACK: runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/fill-pack
P3PR_LOCAL_PAGE: runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/paper-reading-output/index.html
P3PR_SOURCE_URL: https://www.cs.virginia.edu/~robins/YouAndYourResearch.html
P3PR_NEXT_ACTION: Done. Page published (or local). To re-publish, run the same command.
```

### Run layout

The standard run layout is produced, with two extra files for URL inputs:

```
runs/<output-root>/<slug>/
├── input/
│   ├── input.md              # audit trail: URL + extracted body
│   └── source_pointer.txt    # just the URL, one-liner
├── source/
│   └── source.html           # raw HTML bytes
│                             # (or source.pdf for PDF responses)
├── extracted/
│   └── page.txt              # stdlib HTML→text output
├── work/
│   ├── paper_reading.json    # input_kind=paper_url, identifiers.url=<url>
│   ├── resolver_source.json  # CLI overlay
│   ├── audit_result.json
│   └── quality_gate_zh_cn.json
├── fill-pack/                # agent fill instructions
├── paper-reading-output/
│   └── index.html
└── reports/                  # audit + quality gate summaries
```

### Compatibility

- **Runner relaxes its old "only one of --input / --input-file" check.** When
  both are present, `--input` is the audit-trail / hint-lookup string and
  `--input-file` is the body. Callers that passed exactly one continue to
  work; only callers that want to pass both benefit.
- **No external dependencies.** `p3pr url` does not call out to any LLM API,
  does not need `requests` / `beautifulsoup4` / `playwright`, and does not
  require `pdftotext` for HTML input.
- **Reading mode is honest.** HTML pages with no body (error pages,
  paywalled redirects, JS-only SPAs) get `partial_text`, not `full_text`.
  PDFs without `pdftotext` stay `partial_text`.
- **Existing subcommands unchanged.** `arxiv / title / abstract / screenshot /
  repo / pdf` continue to work as before.

## v0.3.0-alpha: stable-readiness release candidate

This is the first stable-readiness release candidate for the project. No
new subcommands or features in this release. The goal is to take stock:
confirm every guard is intact, the validation suite is green, the live
site is healthy, and the documentation is consistent.

### Bug fix in v0.3.0-alpha

`p3pr doctor`'s per-check `status` is uppercase (`PASS` / `WARN` / `FAIL`)
but the summary counter dict uses lowercase keys. The `if s in summary`
lookup was always failing, so `summary.pass` / `summary.warn` /
`summary.fail` were always `0`. v0.3.0-alpha lowercases the check status
before the lookup. After the fix, the same doctor run reports
`summary: {pass: 24, warn: 1, fail: 0}`.

### v0.3.0-alpha readiness results

- `bash scripts/validate.sh` — **305 / 0 PASS**
- `./p3pr doctor --offline` / `--quick` / `--full` — 24 PASS / 1 WARN / 0 FAIL
- live `audit_published_pages.py` — 14 / 14 PASS, 0 warn, 0 fail
- URL dry-run smoke + finalize dry-run smoke — no side effects

### Not yet stable

This is `v0.3.0-alpha`, not `v0.3.0` stable. The next stable release
should follow after:

1. At least a few more real paper runs through the two-stage flow
2. One more round of `audit_published_pages.py` after the new runs land
3. A final `p3pr doctor --full` pass on a clean working tree

See
[`STABLE_READINESS_CHECKLIST.md`](../../../../docs/STABLE_READINESS_CHECKLIST.md)
for the full checklist and
[`PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md`](../../../../docs/PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md)
for this run's full phase report.

## v0.3.0 stable — DEFERRED

`v0.3.0` stable was **deferred** in
[`PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md`](../../../../docs/PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md).
The cleanroom is otherwise fully clean (validation 305/0, live audit
14/14, doctor 24/1/0, all dry-runs PASS) but `p3pr doctor` reports a
`git_working_tree` WARN from a historical backlog. `v0.3.0-alpha`
remains the latest released.
