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
