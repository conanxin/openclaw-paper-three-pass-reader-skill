# Runner — paper-three-pass-reader (v0.2.1-alpha)

The `run_paper_reading.py` script is a **one-command runner** that turns a paper-shaped input into a standard run directory + draft `paper_reading.json` + (optionally) an Agent Fill Pack + (optionally) an audit + (optionally) a rendered HTML page + (optionally) a published GitHub Page.

It does **not** read the paper for you. It produces a **draft** that a human or an agent fills in. Its job is to enforce intake discipline, write the standard run layout, and keep the workflow repeatable.

---

## Usage

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input <string>            # raw input
    --input-file <path>         # OR: path to a file containing the input
    --input-kind <kind>         # required: one of the 11 input kinds
    --slug <slug>               # required: [A-Za-z0-9._-]+
    --output-root <path>        # required: where to create the run directory
    [--title <title>]           # override paper title
    [--authors <a,b,c>]         # override authors
    [--year <year>]             # override year
    [--arxiv-id <id>]           # override arXiv ID
    [--paper-url <url>]         # override URL
    [--reading-mode <mode>]     # override reading mode
    [--render]                  # render the page after writing the draft
    [--publish]                 # publish the rendered page to GitHub Pages
    [--repo <owner/repo>]       # target repo for --publish
    [--branch gh-pages]         # branch for --publish (default gh-pages)
    [--site-path <slug>]        # site path for --publish (default = --slug)
    [--page-title <title>]      # page title for --publish
    [--fill-pack]               # (v0.2.1) write an Agent Fill Pack to <run>/fill-pack/
    [--audit]                   # (v0.2.1) run audit_paper_reading.py after the draft
    [--audit-warn-only]         # (v0.2.1) treat audit WARN as PASS for render/publish
    [--agent-profile <p>]       # (v0.2.1) default|strict|beginner|researcher|engineer
    [--language <lang>]         # (v0.2.1) zh-CN|en
    [--max-claims <n>]          # (v0.2.1) max claims in fill-pack (default 8)
    [--max-figures <n>]         # (v0.2.1) max figure entries in fill-pack (default 6)
```

`--help` shows the full list.

---

## What the runner creates

```
<output-root>/<slug>/
├── input/
│   └── input.md               # captured raw input (audit trail)
├── source/                    # empty — operator drops PDFs here
├── extracted/                 # empty — operator drops pdftotext output here
├── work/
│   └── paper_reading.json     # the DRAFT
└── paper-reading-output/       # populated only if --render
    ├── index.html
    ├── assets/{style.css, app.js}
    ├── data/  (8 JSON mirrors)
    └── reports/ (12 markdown files)
```

The runner never writes to `source/` or `extracted/` — those are reserved for the operator to provide the actual PDF and extracted text.

---

## Reading-mode discipline

The runner enforces strict reading-mode rules:

| `--input-kind` | Forced `reading_mode` (unless `--reading-mode` is passed) |
|---|---|
| `paper_excerpt` | `abstract_only` |
| `paper_screenshot` | `screenshot_only` |
| other kinds | derived from hint (built-in resolver table) or `partial_text` |

For `abstract_only` and `screenshot_only`:

- Pass 2 / Pass 3 are explicitly marked `[DRAFT — unavailable until body is available]`.
- Claims in the draft are labelled `[Needs verification]`.
- `intake_quality.missing_fields` includes `full_body_text`, `full_references`, `full_figures`, `full_tables`.

The runner **never** pretends to have read more than it has.

---

## Built-in resolver hints

The runner ships with a small, hand-curated hint table for smoke testing and for known canonical papers. **It does not perform any network search.** Unknown inputs become `ambiguous_clue` drafts with `needs_confirmation = true` and `confidence = low`.

| Input | Hint |
|---|---|
| `Attention Is All You Need` | arXiv 1706.03762 (Vaswani et al., 2017) |
| `How to Read a Paper` | S. Keshav, SIGCOMM CCR 2007 |
| `BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding` | arXiv 1810.04805 (Devlin et al., 2018) |
| `https://github.com/google-research/bert` | → BERT paper (same as above) |
| `https://github.com/conanxin/openclaw-paper-three-pass-reader-skill` | → this repo |

For unknown inputs, the runner writes:

```json
{
  "intake_quality": {
    "needs_confirmation": true,
    "confidence": "low",
    "warnings": [
      "Input did not match any built-in resolver hint.",
      "Canonical identification is NOT confirmed; needs human confirmation."
    ],
    "source_resolution": [
      "Input kind = <kind>.",
      "Input string: <input>.",
      "No resolver hint matched. needs_confirmation = true.",
      "Runner did NOT fetch the paper body."
    ]
  }
}
```

---

## Examples

### Title-only

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "Attention Is All You Need" \
    --input-kind paper_title \
    --slug runner-title-attention \
    --output-root runs/runner-smoke-20260615 \
    --render
```

Output: `runs/runner-smoke-20260615/runner-title-attention/paper-reading-output/index.html` with `reading_mode = full_text` (resolved via hint).

### Abstract-only

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "abstract excerpt of How to Read a Paper" \
    --input-kind paper_excerpt \
    --slug runner-abstract-keshav \
    --output-root runs/runner-smoke-20260615 \
    --render
```

Output: `reading_mode = abstract_only` (forced by `paper_excerpt` kind).

### Screenshot-only transcript

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "OCR transcript of How to Read a Paper screenshot" \
    --input-kind paper_screenshot \
    --slug runner-screenshot-keshav \
    --output-root runs/runner-smoke-20260615 \
    --render
```

Output: `reading_mode = screenshot_only` (forced by `paper_screenshot` kind).

### Repo clue

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "https://github.com/google-research/bert" \
    --input-kind project_or_repo \
    --slug runner-repo-bert \
    --output-root runs/runner-smoke-20260615 \
    --render
```

Output: `reading_mode = full_text` (hint matched → `arxiv_id = 1810.04805`).

### Render an existing draft

If you already have a draft in `work/paper_reading.json`, just use `render_page.py`:

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
    --input runs/runner-smoke-20260615/runner-title-attention/work/paper_reading.json \
    --output runs/runner-smoke-20260615/runner-title-attention/paper-reading-output
```

### Publish to GitHub Pages

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "Attention Is All You Need" \
    --input-kind paper_title \
    --slug runner-title-attention \
    --output-root runs/runner-smoke-20260615 \
    --render --publish \
    --repo conanxin/paper-reading-pages \
    --branch gh-pages \
    --page-title "Runner Smoke: Attention Is All You Need"
```

The page URL is `https://<owner>.github.io/<repo>/<slug>/`. The repo root becomes a small index page listing every published page.

---

## Editing the draft and re-rendering

The runner produces a DRAFT with `[DRAFT]` placeholders. After filling the draft with real content:

```bash
# Edit work/paper_reading.json — replace [DRAFT] placeholders with real summaries,
# claims, figures, references, etc. Use the schema in
# skills/paper-three-pass-reader/templates/paper_reading.schema.json as a guide.

# Re-render the page:
python3 skills/paper-three-pass-reader/scripts/render_page.py \
    --input work/paper_reading.json \
    --output ../paper-reading-output

# Or, in one shot with the runner (only re-renders and re-publishes):
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "Attention Is All You Need" \
    --input-kind paper_title \
    --slug runner-title-attention \
    --output-root runs/runner-smoke-20260615 \
    --render --publish \
    --repo conanxin/paper-reading-pages \
    --branch gh-pages \
    --page-title "Runner Smoke: Attention Is All You Need (v2)"
```

The `--render` and `--publish` steps are idempotent on the file system; the publish script will overwrite the previous page in `gh-pages/<slug>/`.

---

## Boundaries

The runner **does not**:

- Search the web or arXiv for the paper.
- Fetch the PDF.
- Extract text from a PDF.
- Read the paper for you.
- Use an external LLM API.
- Decide what the paper says.

The runner **does**:

- Enforce intake discipline.
- Write a standard run layout.
- Generate a DRAFT `paper_reading.json` with the right shape, the right `reading_mode`, the right `input_kind`, the right `missing_fields`, the right `[DRAFT]` markers, and the right warnings.
- Optionally render the page from the draft.
- Optionally publish the page to GitHub Pages.

If you want a paper-reading agent that fills in the draft automatically, that is a planned v0.3 capability (LLM-driven filler), not v0.2.

---

## Files

- `skills/paper-three-pass-reader/scripts/run_paper_reading.py` — the runner (stdlib only).
- `skills/paper-three-pass-reader/scripts/render_page.py` — used by `--render`.
- `skills/paper-three-pass-reader/scripts/publish_output_to_github.sh` — used by `--publish`.
- `skills/paper-three-pass-reader/templates/paper_reading.schema.json` — schema for the draft (and the final JSON).

Smoke runs from v0.2.0-alpha validation live at:

- `runs/runner-smoke-20260615/runner-title-attention/`
- `runs/runner-smoke-20260615/runner-abstract-keshav/`
- `runs/runner-smoke-20260615/runner-screenshot-keshav/`

---

## v0.2.1-alpha additions

The runner gained three concerns:

### 1. `--fill-pack`

Writes `<run_dir>/fill-pack/` containing 11 markdown files (00_README through 10_quality_gate) plus `prompts.json`, `field_checklist.json`, and `draft_status.json`. These are task instructions for an agent or human to fill in the draft JSON.

See `docs/AGENT_FILL_PACK.md` for the full design.

### 2. `--audit`

After writing the draft JSON, the runner invokes `audit_paper_reading.py` and writes:

- `<run_dir>/work/audit_result.json` — full audit JSON.
- `<run_dir>/reports/audit_summary.md` — markdown summary.

If audit status is FAIL, the runner refuses to render or publish (unless `--audit-warn-only` is set).

See `docs/AUDIT.md`.

### 3. Reading-mode + agent-profile tuning

- `--agent-profile` (default / strict / beginner / researcher / engineer) — tunes the fill-pack tone.
- `--language` (zh-CN / en) — fill-pack language.
- `--max-claims` / `--max-figures` — caps for the fill-pack checklists.

## Combined example

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
    --input "Attention Is All You Need" \
    --input-kind paper_title \
    --slug fillpack-title-attention \
    --output-root runs/fill-pack-smoke-20260615 \
    --reading-mode partial_text \
    --fill-pack --audit --audit-warn-only \
    --render
```

This produces:

- `runs/fill-pack-smoke-20260615/fillpack-title-attention/work/paper_reading.json`
- `runs/fill-pack-smoke-20260615/fillpack-title-attention/work/audit_result.json`
- `runs/fill-pack-smoke-20260615/fillpack-title-attention/reports/audit_summary.md`
- `runs/fill-pack-smoke-20260615/fillpack-title-attention/fill-pack/` (11 md + 3 json)
- `runs/fill-pack-smoke-20260615/fillpack-title-attention/paper-reading-output/index.html`

## Smoke runs from v0.2.1-alpha

- `runs/fill-pack-smoke-20260615/fillpack-title-attention/`
- `runs/fill-pack-smoke-20260615/fillpack-abstract-keshav/`
- `runs/fill-pack-smoke-20260615/fillpack-screenshot-keshav/`

## v0.2.3 — Language output

The runner carries a `--language` flag (default `zh-CN`) into the draft JSON via two top-level fields:

```json
{
  "target_language": "zh-CN",
  "ui_language": "zh-CN"
}
```

- `target_language` is read by the **audit** to decide whether to check for Chinese characters in interpretive fields.
- `ui_language` is read by the **renderer** to decide whether to apply the Chinese UI label map.

Both default to the value passed to `--language`. If the flag is omitted, the default is `zh-CN` (this matches the project's home user being Chinese-first).

Example (Chinese full-text run on arXiv:2503.08102):

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "arXiv:2503.08102 — Second Me: Human-Inspired Memory Mechanism for LLM Agents" \
  --input-kind paper_identifier \
  --slug second-me-human-inspired-memory-cn \
  --output-root runs/second-me-zh-cn-20260615 \
  --title "Second Me: Human-Inspired Memory Mechanism for LLM Agents" \
  --arxiv-id "2503.08102" \
  --paper-url "https://arxiv.org/abs/2503.08102" \
  --reading-mode full_text \
  --language zh-CN \
  --fill-pack \
  --audit
```

After the runner finishes, follow the fill-pack instructions in Chinese to fill the draft, then re-audit. The renderer will produce a Chinese UI page because the JSON carries `ui_language = "zh-CN"`.

## v0.2.4 — Quality gate integration

The runner gained a `--quality-gate` flag (no-op for non-zh-CN runs):

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "arXiv:2503.08102 — Second Me" \
  --input-kind paper_identifier \
  --slug second-me-human-inspired-memory-cn \
  --output-root runs/second-me-zh-cn-20260615 \
  --language zh-CN \
  --fill-pack --quality-gate
```

When `--quality-gate` is set and `--language == zh-CN`:

1. After the audit, the runner invokes `quality_gate_zh_cn.py` and writes:
   - `work/quality_gate_zh_cn.json` — JSON report
   - `reports/quality_gate_zh_cn.md` — markdown summary
2. If the quality gate returns FAIL and `--audit-warn-only` is not set, the runner blocks `--render` and `--publish`.
3. If the quality gate returns PASS or WARN (under `--warn-only`), the runner proceeds as usual.

The quality gate checks: language fields, CJK coverage, English-blob carryover, glossary / claims / checklist counts, full_text `[Paper evidence]` discipline, Pass 2/3 presence. See [`ZH_CN_QUALITY_GATE.md`](ZH_CN_QUALITY_GATE.md) for the full spec.

## v0.2.5 — `p3pr` one-line CLI

The runner is still the underlying engine, but v0.2.5 added a thin shell shim that chains runner + fill-pack + audit + quality-gate + render + publish into one command.

```bash
./p3pr arxiv 2503.08102 --zh --full --publish
./p3pr title "Attention Is All You Need" --zh --full --publish
./p3pr abstract path/to/abstract.md --zh --publish
./p3pr screenshot path/to/transcript.md --zh --publish
./p3pr repo https://github.com/google-research/bert --zh --full --publish
./p3pr pdf path/to/paper.pdf --zh --full --publish
```

See [`ONE_LINE_CLI.md`](ONE_LINE_CLI.md) for the full flag list. The CLI does NOT do any deep reading itself — the fill-pack is the task description for the agent / human.

The CLI is implemented in `skills/paper-three-pass-reader/scripts/p3pr.py` and shells out to `run_paper_reading.py` (this file) internally. So everything in this document applies to the CLI's runner step too.

## v0.2.14 — `--input` and `--input-file` together + `paper_url`

The runner now accepts **both** `--input` and `--input-file` at the same time:

- `--input` is the audit-trail / hint-lookup string (e.g. a URL or a paper
  title).
- `--input-file` is the body that gets captured into `input/input.md` and
  shown to the agent / human as the captured raw input.

This was added to support the new `p3pr url` subcommand: the CLI fetches
the URL itself, extracts the body via stdlib `html.parser`, and passes the
URL as `--input` and the extracted text path as `--input-file`. The runner
then records both in `input/input.md`:

```markdown
# Captured input for run <slug>

- input_kind: `paper_url`
- input: `https://example.com/article.html`
- input_file: `runs/.../<slug>/extracted/page.txt`
- runner: paper-three-pass-reader v0.2.0-alpha
- captured_at: 2026-06-16T...

## Raw input (from --input-file)

```
<extracted plain text body>
```
```

Callers that only pass `--input` (most existing callers) continue to
work unchanged; only callers that want to pass both benefit.

### `input_kind=paper_url`

The runner accepts `paper_url` as an `input_kind` (alongside `complete_paper`,
`paper_identifier`, `paper_title`, `paper_excerpt`, `paper_screenshot`,
`project_or_repo`). When `input_kind=paper_url` and `--paper-url` is given:

- `paper_metadata.identifiers.url` is set to the user-supplied URL.
- `paper_metadata.source_kind` is `"paper_url"`.
- `intake_quality.source_resolution` records the URL as `hint_input` and
  `resolver_source = "user_supplied_url"` (via the CLI overlay).
- `intake_quality.ambiguities` and `warnings` note that no resolver hint
  was matched (the URL did not hit any built-in paper).

The CLI uses this combination together with the new
`--input-file <extracted/page.txt>` to support the `p3pr url` workflow.
See [`USAGE.md`](USAGE.md#v0214-alpha-p3pr-url-subcommand) for the full
end-to-end flow.

---

## v0.2.17-alpha: the runner is now fronted by `p3pr finalize <run-dir>`

v0.2.17 adds a second CLI entry point, `p3pr finalize`, that orchestrates the
**second stage** of a P3PR run on an already-filled run directory. It is
implemented in `p3pr.py` (`handle_finalize`) and uses the same underlying
scripts that the runner uses — `audit_paper_reading.py`, `quality_gate_zh_cn.py`,
`render_page.py`, and `publish_output_to_github.sh`.

When `p3pr finalize` is invoked, it does **not** call `run_paper_reading.py`
(because the run has already been produced and the JSON has already been
filled); it calls the audit / quality-gate / render / publish scripts
directly. This is by design: the runner is the right tool for the **first**
stage, and finalize is the right tool for the **second** stage.

The runner's own publish-path is unchanged. The runner is still the
recommended entry point for new runs that do not yet have a fill-stage:

```bash
./p3pr url <url> --zh --full --no-publish   # stage 1 (runner fills draft)
# ... agent / human fills paper_reading.json per fill-pack ...
./p3pr finalize <run-dir> --publish         # stage 2 (finalize + publish)
```

`p3pr finalize` also enforces the v0.2.15 publish-gate: if
`paper-reading-output/index.html` is missing after render, finalize BLOCKs
with `P3PR_FINALIZE_STATUS: BLOCKED` and never reaches the publisher. This
prevents 404 stubs on `gh-pages` from a fill that didn't actually produce
rendered HTML.

See [`USAGE.md`](USAGE.md) § "v0.2.17-alpha: `p3pr finalize <run-dir>` — the
second-stage CLI" for the full flag list and summary block spec.

## v0.2.18-alpha: `p3pr finalize` UX polish (auto-inference + richer summary)

`finalize` now infers the gh-pages site-path and the published page title from
`paper_reading.json` — no more passing `--site-path` / `--page-title` on the
two-stage flow. The summary block is also enriched.

### Inference precedence

- **site-path** — explicit `--site-path` → `paper_metadata.page_slug` /
  `slug` / `default_slug` → slugified `paper_metadata.title` → run-dir basename.
  CJK-only titles reach the run-dir fallback (no pypinyin dependency).
- **page-title** — explicit `--page-title` → `paper_metadata.page_title` → for
  zh-CN runs `paper_metadata.title_zh` / `title_zh_cn` → `paper_metadata.title`
  → run-dir basename. The English title is preserved (no auto-translation).

### Richer summary block

Every finalize exit now prints `P3PR_READING_MODE`, `P3PR_LANGUAGE`,
`P3PR_SITE_PATH`, `P3PR_PAGE_TITLE`, `P3PR_AUDIT_STATUS`,
`P3PR_QUALITY_GATE_STATUS`, `P3PR_WARNING_COUNT`, `P3PR_WARNING_SUMMARY` (up
to 3 actual warnings, `|`-joined, with `... (+N more)` when longer), and a
state-aware `P3PR_NEXT_ACTION` one-liner.

### Dry-run

`./p3pr finalize <run-dir> --publish --dry-run` now prints the inferred
`site_path` and `page_title` with source attribution. No side effects.

### Compatibility

All v0.2.15 / v0.2.17 publish guards are preserved (verified by validation
step 22). Validation 293/0 PASS. See
[`USAGE.md`](USAGE.md) § "v0.2.18-alpha: `p3pr finalize <run-dir>` UX
polish" for the full flag list and dry-run output.

## v0.2.19-alpha: `p3pr status` + `p3pr doctor` — read-only observability

The runner side of the project is unchanged in v0.2.19. The CLI gained two
read-only observability subcommands: `p3pr status` and `p3pr doctor`.

### `p3pr status`

Scans `runs/` and reads `published_pages.json` (default URL, or `--manifest-file`
for a local copy, or `--offline` to skip the fetch). Each run is classified
into one of: `draft` / `filled` / `audited` / `rendered` /
`rendered_with_warnings` / `published` / `blocked` / `unknown`. The
classification comes from the runner's own artifacts (`work/paper_reading.json`,
`work/audit_*.json`, `work/quality_gate_zh_cn.json`,
`paper-reading-output/index.html`) plus a cross-reference to the manifest
slugs. `status` never writes to runs.

### `p3pr doctor`

Runs 7 read-only health-check groups: local env, required scripts, required
data/docs, git state, gh CLI / auth, optional `scripts/validate.sh`, light
HEAD probe of the site. Default is `--quick` (no validation); `--full` runs
`scripts/validate.sh`. Dirty working tree and missing gh surface as WARN
(with a recommendation line), never FAIL. doctor never auto-fixes.

### Compatibility

All v0.2.15 / v0.2.17 / v0.2.18 publish guards and finalize UX are
preserved. Validation 305/0 PASS (was 293 at v0.2.18; +12 new sub-checks
in step 23). See
[`USAGE.md`](USAGE.md) § "v0.2.19-alpha: `p3pr status` + `p3pr doctor`" and
[`STATUS_AND_DOCTOR.md`](STATUS_AND_DOCTOR.md) for the full flag list,
JSON shapes, and run-status taxonomy.
