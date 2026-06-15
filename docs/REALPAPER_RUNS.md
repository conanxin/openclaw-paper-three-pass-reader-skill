# Real-paper runs — paper-three-pass-reader

This document is an index of **real paper** end-to-end runs produced by `paper-three-pass-reader` v0.1.0-alpha. A "real paper run" means:

1. A real research paper was the input (not the bundled Keshav sample).
2. The PDF was actually downloaded and parsed for Stage 0.
3. `paper_reading.json` is grounded in the paper's actual text — not the Keshav sample.
4. The interactive page was rendered, validated, and published to GitHub Pages.
5. A phase report was committed to the skill repo.

Each run has a unique ID of the form `P3PR-REALPAPER-N`.

---

## P3PR-REALPAPER-1

| Field | Value |
|---|---|
| **Paper** | Attention Is All You Need (Vaswani et al., 2017) |
| **arXiv** | 1706.03762v7 (last updated 2 Aug 2023) |
| **Original publication** | NIPS 2017 (Long Beach, CA, USA) |
| **Run ID** | P3PR-REALPAPER-1 |
| **Run date** | 2026-06-15 |
| **Run dir** | `runs/attention-is-all-you-need-20260615/` |
| **Source PDF** | `runs/attention-is-all-you-need-20260615/source/attention-is-all-you-need.pdf` (≈ 2.2 MB, 5 pages) |
| **Extracted text** | `runs/attention-is-all-you-need-20260615/extracted/attention-is-all-you-need.txt` (40 074 chars via `pdftotext` 24.02.0) |
| **Work JSON** | `runs/attention-is-all-you-need-20260615/work/paper_reading.json` |
| **Local page** | `runs/attention-is-all-you-need-20260615/paper-reading-output/index.html` |
| **GitHub Pages** | https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/ |
| **GitHub Pages root** | https://conanxin.github.io/paper-reading-pages/ |
| **GitHub Pages repo** | https://github.com/conanxin/paper-reading-pages (`gh-pages` branch) |
| **Phase report** | [`docs/PHASE_P3PR_REALPAPER_1_ATTENTION_REPORT.md`](PHASE_P3PR_REALPAPER_1_ATTENTION_REPORT.md) |

### Reading mode

`full_text` — all major sections (Abstract, Introduction, Background, Model Architecture, Why Self-Attention, Training, Results, Conclusion, References) present in the extracted text.

### Stage-0 summary

| Field | Value |
|---|---|
| `input_kind` | `paper_identifier` |
| `source_kind` | `paper_identifier` |
| `reading_mode` | `full_text` |
| `confidence` | `high` |
| `extraction_quality` | high (40 074 chars from `pdftotext`; all sections present) |
| `needs_confirmation` | `false` |

### Pass-1 decision

`CONTINUE_FULL` — the paper is one of the most-cited methods papers in modern NLP; the Pass-2 and Pass-3 artifacts are warranted.

### Pass-2 highlights

- 10 claims in the Claims → Evidence map (all six evidence labels used).
- 6 figures/tables explained (Transformer architecture, Scaled Dot-Product Attention, Multi-Head Attention, hyperparameters, BLEU + training cost, constituency parsing F1).
- 6 key references with `why` annotations.
- 7 main ideas from Pass-2 close reading.

### Pass-3 highlights

- 11-step method reconstruction.
- 7-point critical review.
- 5 hidden assumptions.
- 6 explicit limitations.
- 11-step reproduction plan with 6 sanity checks and 5 success criteria.
- 7 future-work items.
- 5 application notes.

### Final page URL (GitHub Pages)

https://conanxin.github.io/paper-reading-pages/

Verified `HTTP 200` on 2026-06-15, content-type `text/html; charset=utf-8`, body matches the local rendered HTML (44 309 bytes, title `Attention Is All You Need — Three-Pass Reading`).

---

## How to add a new run

For each new real-paper run:

1. Create `runs/<paper-slug>-<YYYYMMDD>/` with `source/`, `extracted/`, `work/`, `paper-reading-output/` subdirs.
2. Download the PDF to `source/`, extract text to `extracted/`.
3. Fill `work/paper_reading.json` based on the **actual paper text**, not the sample.
4. Render the page: `python3 skills/paper-three-pass-reader/scripts/render_page.py --input runs/.../work/paper_reading.json --output runs/.../paper-reading-output`.
5. Smoke-check the page (mandatory sections present, evidence labels visible, claim filter wired).
6. Push to GitHub Pages with `publish_output_to_github.sh` (use `--site-path <slug> --page-title "Title"` for multi-page mode in v0.1.1+).
7. Write `docs/PHASE_P3PR_REALPAPER_<N>_<slug>_REPORT.md`.
8. Append a row to this file under a new `P3PR-REALPAPER-N` heading.
9. Commit + push the run data, the report, and this index.

## v0.1.1 multi-page layout

As of v0.1.1-alpha, the GitHub Pages repo (`conanxin/paper-reading-pages`) holds a small root index plus one subdirectory per published paper:

```
https://conanxin.github.io/paper-reading-pages/                      <- root index
https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/
https://conanxin.github.io/paper-reading-pages/<next-slug>/          <- future papers
```

The root index is regenerated from `published_pages.json` on every publish call. To publish a new paper, run the `publish_output_to_github.sh` with `--site-path <new-slug> --page-title "Title"`. The script preserves other page subdirs and upserts (not duplicates) the manifest entry for the slug.

## v0.1.2-alpha release note

`v0.1.2-alpha` is the release that includes the publish-script fix after `v0.1.1-alpha`. `v0.1.1-alpha` remains immutable and was not force-moved.

Specifically:

- The multi-page index mode cleanup step (the one that runs when both `--site-path` and `--page-title` are passed) used to use a `find … -exec rm` pattern that wiped **all** non-infrastructure root entries — including other published pages' subdirectories. v0.1.2-alpha replaces it with an explicit list of stale-file names (`README.md`, `data/`, `reports/`, `index.html.bak`, `README.zh-CN.md`); unknown directories are now left alone, so re-publishing one paper cannot accidentally delete another paper's slug page.
- The published tags are now treated as immutable by policy: `v0.1.0-alpha` and `v0.1.1-alpha` are not moved by any future release. New fixes ship as new tags (`v0.1.2-alpha`, …).
- No schema, no page template, no three-pass design changes.

## P3PR-WEAKINPUT-1 (pointer)

See [`docs/WEAKINPUT_RUNS.md`](WEAKINPUT_RUNS.md) for the full weak-input run index. P3PR-WEAKINPUT-1 (2026-06-15) exercises four weak-input kinds (title-only, abstract-only, screenshot-only, repo-clue) on the same skill version. Two of the four cases upgrade to `full_text` after a successful PDF fetch; two stay at their partial mode and never pretend to have read more than the supplied text.
