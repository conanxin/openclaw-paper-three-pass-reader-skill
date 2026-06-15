# Weak-input runs — paper-three-pass-reader

This document indexes **weak-input** end-to-end runs produced by `paper-three-pass-reader`. A weak-input run is one where the input is **not** a complete PDF/HTML/text — it is a single weak hint (title, abstract, OCR transcript, or repo URL). The skill must do Stage 0 honestly: identify the paper, fetch what it can, and tag `reading_mode` accurately so the page never pretends to have read more than it has.

Each run has a unique ID of the form `P3PR-WEAKINPUT-N`.

---

## P3PR-WEAKINPUT-1

| Field | Value |
|---|---|
| **Run ID** | P3PR-WEAKINPUT-1 |
| **Run date** | 2026-06-15 |
| **Run dir** | `runs/weakinput-20260615/` |
| **Skill version** | v0.1.2-alpha |
| **Validation** | `scripts/validate.sh` → 68 PASS / 0 FAIL |
| **Phase report** | [`docs/PHASE_P3PR_WEAKINPUT_1_REPORT.md`](PHASE_P3PR_WEAKINPUT_1_REPORT.md) |

The run exercised four distinct weak-input kinds and verified the skill's intake discipline on each.

### Case A — title-only

| Field | Value |
|---|---|
| Input file | `runs/weakinput-20260615/inputs/title-only-attention.md` |
| Input content | the single string `Attention Is All You Need` |
| `input_kind` | `paper_title` |
| Resolution path | title → arXiv search → arXiv 1706.03762 → PDF fetch → `pdftotext` |
| `reading_mode` | **`full_text`** (full body obtained from the canonical arXiv PDF) |
| Local page | `runs/weakinput-20260615/case-title-attention/paper-reading-output/index.html` (44 608 bytes) |
| GitHub Pages | https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ |
| Status | live HTTP 200 |

The skill **upgraded** the title-only input to `full_text` because the title resolved cleanly to a canonical paper and the body was successfully fetched. This is honest: the page is based on the actual paper text, and the `source_resolution` trail records every step.

### Case B — abstract-only

| Field | Value |
|---|---|
| Input file | `runs/weakinput-20260615/inputs/abstract-only-how-to-read-a-paper.md` |
| Input content | title + author + year + venue + abstract / opening paragraph (S. Keshav, *How to Read a Paper*, 2007) |
| `input_kind` | `paper_excerpt` |
| `reading_mode` | **`abstract_only`** — explicitly **NOT** upgraded to `full_text` |
| Local page | `runs/weakinput-20260615/case-abstract-keshav/paper-reading-output/index.html` (18 141 bytes) |
| GitHub Pages | https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ |
| Status | live HTTP 200 |

The skill does **not** pretend to have read the full paper. Pass 2 main ideas are marked with `[Author claim]` for things grounded in the abstract and `[Uncertain]` / `[Needs verification]` for things that are common knowledge but not visible in the supplied text. Pass 3 is explicitly `[unavailable — abstract-only run]`. The reading decision is `SEEK_FULL_TEXT`.

### Case C — screenshot-only / OCR transcript

| Field | Value |
|---|---|
| Input file | `runs/weakinput-20260615/inputs/screenshot-only-how-to-read-a-paper.md` |
| Input content | OCR / VLM transcript of a partial screenshot (title page + visible section headings + visible method fragments for S. Keshav, *How to Read a Paper*) |
| `input_kind` | `paper_screenshot` |
| `reading_mode` | **`screenshot_only`** |
| `extraction_quality` | `medium` |
| `confidence` | `medium` |
| Local page | `runs/weakinput-20260615/case-screenshot-keshav/paper-reading-output/index.html` (19 493 bytes) |
| GitHub Pages | https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ |
| Status | live HTTP 200 |

The skill records `missing_fields` explicitly (full_body, references, figures, tables, etc.). Every claim is `[Uncertain]` or `[Needs verification]`. The Hero badge visibly displays `screenshot_only` in red. Pass 2 / Pass 3 are explicitly `[unavailable — screenshot-only run]`.

### Case D — GitHub repo clue

| Field | Value |
|---|---|
| Input file | `runs/weakinput-20260615/inputs/repo-clue-bert.md` |
| Input content | `https://github.com/google-research/bert` |
| `input_kind` | `project_or_repo` |
| Resolution path | repo → README → linked paper arXiv 1810.04805 → PDF fetch → `pdftotext` |
| `reading_mode` | **`full_text`** (full body obtained) |
| Local page | `runs/weakinput-20260615/case-repo-bert/paper-reading-output/index.html` (34 804 bytes) |
| GitHub Pages | https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ |
| Status | live HTTP 200 |

The `source_resolution` trail records the repo → README → paper → PDF → extraction sequence. The page is grounded in the actual BERT paper text (6 pages, 64 321 characters, all major sections present).

---

## Reading-mode matrix

| Case | Input kind | Resolution successful? | `reading_mode` |
|---|---|---|---|
| A — title-only | `paper_title` | yes (arXiv → PDF → text) | `full_text` |
| B — abstract-only | `paper_excerpt` | identification yes, full text not fetched | `abstract_only` |
| C — screenshot-only | `paper_screenshot` | identification yes, full text not visible | `screenshot_only` |
| D — repo clue | `project_or_repo` | yes (repo → README → arXiv → PDF → text) | `full_text` |

All four cases match what the spec allows:

- A and D upgrade to `full_text` because the body was actually obtained.
- B and C stay at the partial mode they were given, even though the paper could in principle be found — the skill does NOT upgrade an `abstract_only` or `screenshot_only` input to `full_text` without actually fetching the body.

---

## How to add a new weak-input run

For each new weak-input case:

1. Create `runs/<run-slug>-<YYYYMMDD>/inputs/<case-slug>.md` describing what the user supplied.
2. Create `runs/<run-slug>-<YYYYMMDD>/case-<case-slug>/{source,extracted,work,paper-reading-output}/` directories.
3. If the run can fetch a PDF: download to `source/`, extract text to `extracted/`. Update `reading_mode` accordingly.
4. Write `work/paper_reading.json`:
   - Set `source_kind` and `intake_quality.input_kind` to the actual weak-input kind.
   - Set `reading_mode` to `full_text` only if the body is in `extracted/`.
   - Fill `intake_quality.source_resolution` with the actual decision trail.
   - For partial runs, mark Pass 2 / Pass 3 content as `[unavailable — <mode> run]` and use `[Author claim]` / `[Uncertain]` / `[Needs verification]` for everything that isn't actually grounded in the available text.
5. Render with `python3 skills/paper-three-pass-reader/scripts/render_page.py --input work/paper_reading.json --output paper-reading-output`.
6. Smoke-check: mandatory sections present, reading-mode badge in hero, claims table uses only allowed labels for partial runs.
7. Publish with `publish_output_to_github.sh --site-path <slug> --page-title "Title"`.
8. Append a row to this file under a new `P3PR-WEAKINPUT-N` heading.
9. Write `docs/PHASE_P3PR_WEAKINPUT_<N>_REPORT.md`.
10. Commit + push the run data and the report.
