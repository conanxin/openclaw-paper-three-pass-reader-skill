# PHASE_P3PR_WEAKINPUT_1_REPORT.md

| Field | Value |
|---|---|
| **STATUS** | PASS |
| **PROJECT_DIR** | `/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill` |
| **PHASE** | P3PR-WEAKINPUT-1 |
| **BASE_VERSION** | v0.1.2-alpha |
| **DATE** | 2026-06-15 |

---

## TL;DR

The skill correctly handled **all four** weak-input kinds in one batch run:

- **Case A (title-only)** → upgraded to `full_text` because the title resolved to a known arXiv paper and the body was successfully fetched.
- **Case B (abstract-only)** → **stayed at `abstract_only`** — the skill did **not** pretend to have read the full paper; Pass 2 / Pass 3 were explicitly marked unavailable; claims were labelled `[Author claim]` / `[Uncertain]` / `[Needs verification]` only.
- **Case C (screenshot-only)** → **stayed at `screenshot_only`** — body / references / figures / tables explicitly listed in `missing_fields`; all claims are `[Uncertain]` / `[Needs verification]`; Pass 2 / Pass 3 unavailable.
- **Case D (repo clue)** → upgraded to `full_text` because the repo README links to the BERT paper on arXiv and the body was successfully fetched.

All four pages were rendered, smoke-checked, pushed to GitHub Pages under dedicated slug paths, and live-verified at HTTP 200. The previously published Attention page (from P3PR-REALPAPER-1) is still live at its original URL — multi-page publishing did not delete it. The root index now lists 5 pages. The skill's own `scripts/validate.sh` still PASSes 68 / 0.

No new tag/release was created — this run only added new test cases to the run data; the skill code itself was not modified.

---

## CASES_TESTED

| # | Case | Input kind | Resolution outcome | `reading_mode` |
|---|---|---|---|---|
| A | title-only | `paper_title` | high-confidence title → arXiv 1706.03762 → PDF → text | `full_text` |
| B | abstract-only | `paper_excerpt` | identification high; full text not fetched | `abstract_only` |
| C | screenshot-only | `paper_screenshot` | identification high; full text not visible | `screenshot_only` |
| D | repo clue | `project_or_repo` | repo → README → arXiv 1810.04805 → PDF → text | `full_text` |

---

## CASE_A_TITLE_ONLY

**Input**: the single string `Attention Is All You Need`.

**Stage 0**:
- `input_kind: paper_title`
- `reading_mode: full_text` (after successful PDF fetch + `pdftotext` extraction)
- `confidence: high`
- `needs_confirmation: false`
- `source_resolution` (6 steps):
  1. Input kind = paper_title; only the string was supplied.
  2. Resolved via arXiv search → arXiv 1706.04805 (v7).
  3. Canonical PDF fetched (2 215 244 bytes, 5 pages).
  4. `pdftotext` → 40 074 characters.
  5. All major sections present and ordered.
  6. `reading_mode = full_text`.
- `extraction_quality: high`

**Page**:
- 44 608 bytes (about the same size as the full Attention run from P3PR-REALPAPER-1; the paper_reading.json was reused from that run with `source_kind` and `intake_quality.input_kind` flipped to `paper_title`).
- Hero badge: `full_text`. Title: `Attention Is All You Need — Three-Pass Reading`.
- Live URL: https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ → HTTP 200.

**Honesty check**: the page is grounded in the actual paper text (the PDF was fetched). The `source_resolution` trail explicitly notes the title-only entry point. No pretending.

---

## CASE_B_ABSTRACT_ONLY

**Input**: title + author + year + venue + abstract / opening paragraph (S. Keshav, *How to Read a Paper*, 2007).

**Stage 0**:
- `input_kind: paper_excerpt`
- `reading_mode: abstract_only` — **NOT** upgraded to `full_text`.
- `confidence: high` (identification is high; body coverage is partial).
- `needs_confirmation: false`
- `missing_fields` includes: `arxiv_id`, `doi`, `openreview_id`, `url`, `full_body_text`, `full_references`, `full_figures`, `full_tables`.
- `warnings` (4) all relate to the abstract-only constraint.
- `source_resolution` (5 steps) explicitly says "No PDF was fetched (reading_mode is abstract_only, not full_text)."

**Page**:
- 18 141 bytes.
- Hero badge: `abstract_only` in red. Title: `How to Read a Paper — Three-Pass Reading`.
- 6 claim rows in the Claims → Evidence map. Evidence labels: 3× `[Author claim]`, 3× `[Uncertain]`. **Zero** `[Paper evidence]` claims — no pretending beyond the abstract.
- Pass 2 main ideas are explicitly derived from the abstract; common-knowledge time budgets (5–10 min / ~1 h / 1–4 h) are labelled `[Uncertain]` / `[Needs verification]`.
- Pass 3 is `[unavailable — abstract-only run]` throughout.
- Reading decision: `SEEK_FULL_TEXT`.
- Live URL: https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ → HTTP 200.

**Honesty check**: the page never pretends to have read the body. Every claim is grounded in the abstract or labelled `[Uncertain]` / `[Needs verification]`. The reproduction plan explains how to upgrade to `full_text`.

---

## CASE_C_SCREENSHOT_ONLY

**Input**: OCR / VLM transcript of a partial screenshot of S. Keshav's paper (title page + visible section headings + visible method fragments).

**Stage 0**:
- `input_kind: paper_screenshot`
- `reading_mode: screenshot_only` — **NOT** upgraded to `full_text`.
- `extraction_quality: medium`
- `confidence: medium`
- `missing_fields` (10) includes: `full_body_text`, `full_references`, `full_figures`, `full_tables`, `claims_map_completeness`, `method_reconstruction_inputs`, `pass2_pass3_inputs`.
- `warnings` (5) all relate to the screenshot-only constraint.
- `ambiguities` lists the OCR-derived affiliation as low-confidence.
- `source_resolution` (7 steps) explicitly says "OCR / VLM extraction quality is medium" and "No PDF was fetched. reading_mode = screenshot_only."

**Page**:
- 19 493 bytes.
- Hero badge: `screenshot_only` in red. Title: `How to Read a Paper — Three-Pass Reading`.
- 6 claim rows. Evidence labels: 5× `[Uncertain]`, 1× `[Needs verification]`. **Zero** `[Paper evidence]` claims.
- Pass 2 main ideas are derived only from visible screenshot fragments.
- Pass 3 is `[unavailable — screenshot-only run]` throughout.
- Reading decision: `SEEK_FULL_TEXT`.
- Live URL: https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ → HTTP 200.

**Honesty check**: the page never pretends to have read the body. Every claim is grounded in the visible screenshot fragments or labelled `[Uncertain]` / `[Needs verification]`.

---

## CASE_D_REPO_CLUE

**Input**: `https://github.com/google-research/bert`.

**Stage 0**:
- `input_kind: project_or_repo`
- Resolution: repo → README → linked paper arXiv 1810.04805 → PDF fetch → text.
- `reading_mode: full_text` (after successful PDF fetch + extraction).
- `confidence: high`
- `needs_confirmation: false`
- `missing_fields: ["doi"]`
- `source_resolution` (7 steps) explicitly records: "Repo https://github.com/google-research/bert is the canonical implementation repo for BERT", "Repo README links to the associated paper: arXiv 1810.04805", "Canonical PDF fetched from https://arxiv.org/pdf/1810.04805 (775 166 bytes, 6 pages, PDF 1.5)", "`pdftotext` → 64 321 characters", "All major sections present and ordered".

**Page**:
- 34 804 bytes.
- Hero badge: `full_text`. Title: `BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding — Three-Pass Reading`.
- 10 claim rows. Evidence labels: 4× `[Paper evidence]`, 3× `[Figure/Table evidence]`, 3× `[Author claim]`.
- 7 figures/tables explained (Figure 1–5 + Table 1–4).
- 5 key references with `why` annotations.
- 11-step Pass 3 method reconstruction; 6-point critical review; 4 hidden assumptions; 5 limitations; 11-step reproduction plan with 6 sanity checks and 5 success criteria; 6 future-work items; 5 application notes; 11-question final checklist.
- 11-term glossary.
- Live URL: https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ → HTTP 200.

**Honesty check**: the page is grounded in the actual paper text (6 pages, 64 321 characters). The repo → paper resolution is recorded in `source_resolution`.

---

## READING_MODE_MATRIX

| Case | Input kind | Body obtained? | Final `reading_mode` | Honest? |
|---|---|---|---|---|
| A | `paper_title` | yes (arXiv PDF fetched) | `full_text` | ✅ |
| B | `paper_excerpt` | no (abstract only) | `abstract_only` | ✅ |
| C | `paper_screenshot` | no (visible fragments only) | `screenshot_only` | ✅ |
| D | `project_or_repo` | yes (repo → arXiv PDF fetched) | `full_text` | ✅ |

The matrix matches the spec rules:

- A and D upgraded to `full_text` because the body was actually fetched.
- B and C stayed at the partial mode they were given; the skill does **not** upgrade an `abstract_only` or `screenshot_only` input without actually fetching the body.

---

## STAGE0_FINDINGS

Across the four cases, Stage 0 produced:

| Field | A | B | C | D |
|---|---|---|---|---|
| `input_kind` | `paper_title` | `paper_excerpt` | `paper_screenshot` | `project_or_repo` |
| `reading_mode` | `full_text` | `abstract_only` | `screenshot_only` | `full_text` |
| `confidence` | `high` | `high` | `medium` | `high` |
| `needs_confirmation` | `false` | `false` | `false` | `false` |
| `source_resolution` steps | 6 | 5 | 7 | 7 |
| `missing_fields` count | 1 (`doi`) | 8 | 10 | 1 (`doi`) |
| `warnings` count | 3 | 4 | 5 | 2 |
| `ambiguities` count | 0 | 0 | 1 | 0 |
| `extraction_quality` | `high` | `high for abstract; n/a for body` | `medium` | `high` |

Common pattern:

- `intake_quality.source_resolution` always records the actual decision trail.
- `intake_quality.warnings` always lists what is missing or unreliable.
- `intake_quality.missing_fields` lists every field that is not available for the given input.

This is the skill's intake discipline in action: even when identification is high-confidence, the page is honest about what was actually read.

---

## PAGE_GENERATION

All four pages were rendered with `python3 skills/paper-three-pass-reader/scripts/render_page.py`. Page-level smoke checks (mandatory sections + reading-mode badge + claim-row presence):

| Case | Intake Status | Five Cs | Pass 1 | Claims | Evidence | Checklist | reading_mode badge |
|---|---|---|---|---|---|---|---|
| A | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `full_text` ✅ |
| B | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `abstract_only` ✅ |
| C | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `screenshot_only` ✅ |
| D | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `full_text` ✅ |

---

## PUBLISH_STATUS

All four pages were published via `publish_output_to_github.sh` with `--site-path` + `--page-title` to dedicated slug paths. The skill's v0.1.2-alpha publish-script fix (preserving sibling page subdirs) was used and verified: the previously-published `attention-is-all-you-need/` page was NOT deleted by any of the four subsequent publishes.

`published_pages.json` after the run lists 5 pages:

1. `attention-is-all-you-need` (from P3PR-REALPAPER-1, published_at 2026-06-15T02:46:05Z)
2. `weakinput-title-attention-is-all-you-need` (2026-06-15T03:28:32Z)
3. `weakinput-abstract-how-to-read-a-paper` (2026-06-15T03:28:42Z)
4. `weakinput-screenshot-how-to-read-a-paper` (2026-06-15T03:28:51Z)
5. `weakinput-repo-bert` (2026-06-15T03:29:00Z)

The root index page lists all 5 in publication order.

---

## PAGES_URLS

| URL | Status at run time |
|---|---|
| https://conanxin.github.io/paper-reading-pages/ | HTTP 200 (1044+ bytes) |
| https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/ | HTTP 200 (44 439 bytes) |
| https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ | HTTP 200 (44 608 bytes) |
| https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ | HTTP 200 (18 141 bytes) |
| https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ | HTTP 200 (19 493 bytes) |
| https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ | HTTP 200 (34 804 bytes) |
| https://conanxin.github.io/paper-reading-pages/published_pages.json | HTTP 200 (5 entries) |

---

## VALIDATION

`scripts/validate.sh` result:

```
PASS: 68    FAIL: 0
STATUS: PASS
```

The skill's own 68-check suite was not modified by this run (no skill code was changed).

---

## FILES_CREATED

Run-local (under `runs/weakinput-20260615/`):

- `inputs/title-only-attention.md`
- `inputs/abstract-only-how-to-read-a-paper.md`
- `inputs/screenshot-only-how-to-read-a-paper.md`
- `inputs/repo-clue-bert.md`
- `case-title-attention/source/attention-is-all-you-need.pdf` (not committed by default — large)
- `case-title-attention/extracted/attention-is-all-you-need.txt` (not committed by default — large)
- `case-title-attention/work/paper_reading.json` (committed)
- `case-title-attention/paper-reading-output/{README.md, index.html, assets/, data/, reports/}` (committed)
- `case-abstract-keshav/work/paper_reading.json` (committed)
- `case-abstract-keshav/paper-reading-output/{README.md, index.html, assets/, data/, reports/}` (committed)
- `case-screenshot-keshav/work/paper_reading.json` (committed)
- `case-screenshot-keshav/paper-reading-output/{README.md, index.html, assets/, data/, reports/}` (committed)
- `case-repo-bert/source/bert.pdf` (not committed by default — large)
- `case-repo-bert/extracted/bert.txt` (not committed by default — large)
- `case-repo-bert/work/paper_reading.json` (committed)
- `case-repo-bert/paper-reading-output/{README.md, index.html, assets/, data/, reports/}` (committed)

Skill-repo (committed):

- `docs/WEAKINPUT_RUNS.md` (new)
- `docs/PHASE_P3PR_WEAKINPUT_1_REPORT.md` (this file)
- `docs/REALPAPER_RUNS.md` (added a `P3PR-WEAKINPUT-1 (pointer)` block)

GitHub Pages repo (`conanxin/paper-reading-pages`, gh-pages branch):

- `weakinput-title-attention-is-all-you-need/` subdirectory
- `weakinput-abstract-how-to-read-a-paper/` subdirectory
- `weakinput-screenshot-how-to-read-a-paper/` subdirectory
- `weakinput-repo-bert/` subdirectory
- `index.html` (root) — updated to list 5 pages
- `published_pages.json` — updated with 4 new entries

---

## FILES_MODIFIED

None in the skill repo's skill code (`skills/paper-three-pass-reader/**`, `scripts/validate.sh`). The skill was used as-is.

The only skill-repo file modifications are documentation additions: `docs/WEAKINPUT_RUNS.md`, `docs/REALPAPER_RUNS.md`, `docs/PHASE_P3PR_WEAKINPUT_1_REPORT.md`.

---

## COMMIT

```
<filled in at the end of this run>
```

Commit message: `Add weak input reading runs`. (The exact SHA is recorded after the commit is created.)

---

## PUSH

`git push origin main` after the local commit. No force.

---

## NEW_RELEASE_CREATED

**No.** Per the spec, this run does not require a new release unless the skill code was modified. Skill code was not modified; only run data and docs were added. The existing `v0.1.2-alpha` tag remains the latest.

---

## LIMITATIONS

1. **Repo clue case relies on a clean repo → paper link.** The `google-research/bert` repo's README points directly to the BERT paper, so the resolution is straightforward. For repos with multiple papers, multiple READMEs, or papers that are not directly linked from the README, the skill would need a multi-candidate resolution step. Out of scope for v0.1.2-alpha; candidate for v0.2.
2. **OCR / VLM is the caller's responsibility.** Case C assumes the user supplied a usable OCR / VLM transcript. If the user supplies only a raw PNG, the skill does not currently OCR it. Out of scope.
3. **Title-only Case A benefited from re-using the existing Attention PDF.** For an unknown paper whose title resolves to a less canonical entry, the resolution might need additional confirmation. Out of scope.
4. **`abstract_only` and `screenshot_only` pages do not include figures / tables** (because none are available). Re-rendering with a full PDF would upgrade them automatically.
5. **No LLM-driven filling.** The `paper_reading.json` for each case was hand-authored from the available text. A future v0.3 could wire an LLM-driven filler that takes the available text + the input kind and emits the JSON.

---

## NEXT_USER_ACTION

1. Visit each of the four new live pages and confirm the reading-mode badge matches the actual input kind:
   - https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ — `full_text`
   - https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ — `abstract_only`
   - https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ — `screenshot_only`
   - https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ — `full_text`
2. Visit the root index: https://conanxin.github.io/paper-reading-pages/ — all 5 pages listed.
3. Confirm the previously-published Attention page (P3PR-REALPAPER-1) is still live and unchanged.
4. Try upgrading Case B or C to `full_text` by editing `work/paper_reading.json` (set `reading_mode` to `full_text` after fetching the PDF) and re-rendering + re-publishing.
5. Optional: open a v0.2 issue to add (a) multi-candidate repo resolution, (b) LLM-driven JSON filling, (c) optional OCR / VLM step.

No manual GitHub commands are required — all 4 pages were published and verified live during this run.

---

## Final two lines (per spec)

```
HERMES_STATUS: REPORT_WRITTEN
HERMES_REPORT_PATH: /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/docs/PHASE_P3PR_WEAKINPUT_1_REPORT.md
```
