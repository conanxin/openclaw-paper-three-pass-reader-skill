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

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
    --output paper-reading-output \
    --repo conanxin/paper-reading-pages \
    --branch gh-pages \
    --message "Publish reading page for XYZ"
```

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
