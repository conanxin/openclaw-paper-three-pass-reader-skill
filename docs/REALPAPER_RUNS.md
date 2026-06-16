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

## P3PR-V0.2.2-FULLTEXT-AUTO-FILL-SMOKE (pointer)

A real full-text run on arXiv:2503.08102 ("AI-native Memory 2.0: Second Me", Mindverse.ai, 2025) exercises the v0.2.1-alpha `--fill-pack` + `--audit` flow end-to-end. The PDF was downloaded, text was extracted via pdftotext -layout, the runner produced a draft + fill-pack, the agent filled the draft in 12 claims / 7 figures-tables / 18 glossary / 12 checklist, and the final audit returned PASS with 0 errors / 0 warnings. The page is published at `https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/`.

Full details in [`docs/AUTOFILL_RUNS.md`](AUTOFILL_RUNS.md) and [`docs/PHASE_P3PR_V0_2_2_FULLTEXT_AUTO_FILL_SMOKE_REPORT.md`](PHASE_P3PR_V0_2_2_FULLTEXT_AUTO_FILL_SMOKE_REPORT.md).

## P3PR-V0.2.3-ZH-CN-OUTPUT (pointer)

A Chinese full-text run on arXiv:2503.08102 ("Second Me") that exercises the v0.2.3 zh-CN language support end-to-end. The runner writes `target_language` and `ui_language` to the draft, the audit checks for Chinese content, and the renderer localizes the UI to Chinese. The page is published at `https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/`. Audit: PASS, 0 errors / 0 warnings.

Full details in [`docs/AUTOFILL_RUNS.md`](AUTOFILL_RUNS.md) and [`docs/PHASE_P3PR_V0_2_3_ZH_CN_OUTPUT_REPORT.md`](PHASE_P3PR_V0_2_3_ZH_CN_OUTPUT_REPORT.md).

## P3PR-V0.2.4-ZH-CN-QUALITY-GATE (pointer)

The Second Me Chinese run (`second-me-human-inspired-memory-cn/`) was re-checked with the new `quality_gate_zh_cn.py` script: status PASS, 75/75 CJK coverage, 0 long English blobs, 12 claims / 14 glossary / 12 checklist, 9 `[Paper evidence]` / 3 `[Author claim]`. A new bad sample at `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/` was created to demonstrate the gate's FAIL path (4 errors, 4 warnings).

Full details in [`docs/AUTOFILL_RUNS.md`](AUTOFILL_RUNS.md) and [`docs/PHASE_P3PR_V0_2_4_ZH_CN_QUALITY_GATE_REPORT.md`](PHASE_P3PR_V0_2_4_ZH_CN_QUALITY_GATE_REPORT.md).

## P3PR-HTML-YOU-AND-YOUR-RESEARCH-1

- Input: https://www.cs.virginia.edu/~robins/YouAndYourResearch.html
- Input kind: `paper_url`
- Reading mode: `full_text`
- Language: `zh-CN`
- Category: research advice talk / essay / methodology lecture
- Page: https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/
- Report: `docs/PHASE_P3PR_HTML_YOU_AND_YOUR_RESEARCH_REPORT.md`

A full-text Chinese reading page for Richard W. Hamming's 1986 Bell Communications Research colloquium
transcript. The HTML (82,911 bytes) was fetched with `curl -L` and parsed with `html.parser.HTMLParser`
into 14,454 words of plain text. The runner was used to bootstrap a draft + fill-pack + audit, then
the agent filled the draft in zh-CN (12 claims / 13 glossary / 11 final-checklist items, 18 paper-
outline anchors, all evidence-labelled). Audit returned **PASS** and the zh-CN quality gate returned
**WARN** (only a 1-warning long-English-blob note on the embedded Newton / Pasteur quotes, by design).
Project-wide `scripts/validate.sh` returned **210/0 PASS**. The page was published in multi-page mode
into the `you-and-your-research-cn/` site-path of `conanxin/paper-reading-pages` on `gh-pages`;
`curl -I -L` against the page URL, the site root, and `published_pages.json` all return HTTP/2 200.
No new project tag / release was created.

---

## v0.2.9-alpha re-publish: *You and Your Research* (zh-CN)

Same run as the v0.2.8 section above (`runs/you-and-your-research-20260615/`). v0.2.9 polished the rendered HTML:

- Five Cs cards no longer leak raw `{'label': ...}` dicts; each card now shows `value` + `evidence_label` + `note`.
- `{% else %}` template tag no longer leaks; the mini-template engine has a real `else` branch.
- Footer now reads `paper-three-pass-reader v0.2.9-alpha` (no stale `v0.1.0-alpha`).
- Claims-Evidence table now shows real `C01` / `C02` / `…` IDs.
- Glossary chips now show term + Chinese term + Chinese definition in an explicit body block.
- The `Reproduction Plan` section is renamed `实践计划 / Practical Plan` and exposes 7/30/90-day plans, success criteria, and risks.
- The `Figures & Tables` section now shows `原文无传统图表` plus 5 conceptual notes (Hamming's 5 most-quoted frameworks).
- The `Related Work` section is renamed `相关脉络` and shows a clean fallback for essay-mode inputs.

Project-wide `scripts/validate.sh` returns **220/0 PASS** (210 v0.2.8 baseline + 10 new step-16 essay / talk checks). Audit returns **PASS** (claims=12, glossary=13, checklist=11, no DRAFT placeholders). The zh-CN quality gate still returns **WARN** for the embedded Newton / Pasteur direct quote, by design. The page was re-published in multi-page mode into the same `you-and-your-research-cn/` site-path; all three live URLs (`/`, `/you-and-your-research-cn/`, `/published_pages.json`) return HTTP/2 200. The v0.2.9-alpha tag and GitHub Release are created on the upstream skill repo.

---

## v0.2.11 published-pages remediation (consumer pages only)

The v0.2.10 published-pages regression audit
(`runs/published-pages-audit-20260615/audit.json`) reported 8 pages FAIL with
`template_leak` + `old_footer` + `missing_resolver_trail` (16 error-level issues
in total). All 8 pages had been rendered with the v0.2.9 renderer already
shipping in this repo, but their published `index.html` on the `gh-pages` branch
of `conanxin/paper-reading-pages` still served the pre-v0.2.9 output.

| Slug | Local run | Reading mode |
|------|-----------|--------------|
| attention-is-all-you-need | runs/attention-is-all-you-need-20260615 | full_text |
| weakinput-title-attention-is-all-you-need | runs/weakinput-20260615/case-title-attention | full_text (paper_title) |
| weakinput-abstract-how-to-read-a-paper | runs/weakinput-20260615/case-abstract-keshav | abstract_only |
| weakinput-screenshot-how-to-read-a-paper | runs/weakinput-20260615/case-screenshot-keshav | screenshot_only |
| weakinput-repo-bert | runs/weakinput-20260615/case-repo-bert | full_text (project_or_repo) |
| runner-title-attention | runs/runner-smoke-20260615/runner-title-attention | partial_text |
| second-me-fulltext-autofill | runs/v022-fulltext-autofill-secondme-20260615/second-me-fulltext-autofill | full_text |
| second-me-human-inspired-memory-cn | runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn | zh-CN |

Action: re-render each page with the v0.2.9 renderer (no `paper_reading.json`
content changes — no claim fabrication, no glossary fabrication) and re-publish
to the same `site-path` in multi-page mode. Rendered output is archived under
`runs/p3pr-v0211-remediation-20260616/render-output/`. The full plan and report
live in `docs/PHASE_P3PR_V0_2_11_PUBLISHED_PAGES_REMEDIATION_PLAN.md` and
`docs/PHASE_P3PR_V0_2_11_PUBLISHED_PAGES_REMEDIATION_REPORT.md`.

After-audit (`runs/published-pages-audit-20260615-remediation/audit.json`):

- pages: PASS=9, WARN=1, FAIL=0 (was PASS=1, WARN=1, FAIL=8)
- issues: error=0, warning=3, info=8 (was error=16, warning=10, info=15)
- remaining 3 warnings are all on the **index page** (by design — manifest page,
  no per-paper sections). No FAIL.
- `template_leak`: 8 → 0. `old_footer`: 8 → 0. `missing_resolver_trail`: 8 → 1 (index).

Project-wide `scripts/validate.sh` returns **225/0 PASS** (220 v0.2.9 baseline +
5 new step-17 published-pages audit checks). No skill code changed; no new
project tag or release was created — this is a consumer-pages-only remediation.
The 8 page commits land on the `gh-pages` branch of `conanxin/paper-reading-pages`
and are visible in the published-pages repo history.

---

## v0.2.15-alpha — `p3pr url` dogfood

| Field | Value |
|---|---|
| **Phase** | P3PR-V0.2.15-URL-SUBCOMMAND-DOGFOOD |
| **Date** | 2026-06-16 |
| **Skill code changed** | true (`p3pr.py` publish-gate + `validate.sh` step 20l) |
| **Source** | https://www.cs.virginia.edu/~robins/YouAndYourResearch.html (Hamming) |
| **Run dir** | `runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn` |
| **Slug** | `you-and-your-research-url-dogfood-cn` (not published — bug surfaced and stub removed) |
| **Reading mode** | `full_text` (78,593 chars extracted) |
| **Input kind** | `paper_url` (CLI subcommand `p3pr url`) |
| **Bug surfaced** | `p3pr --publish` pushed a 404 stub when render was skipped (audit/qg FAILED) |
| **Bug fix** | `p3pr.py` now hard-BLOCKs on missing `paper-reading-output/index.html`; regression-guard added at `validate.sh` step 20l |
| **Validation** | 263/0 PASS (was 261/0 at v0.2.14-alpha) |
| **Live audit** | 11/11 PASS, 0 fail, 0 warn |
| **Report** | `docs/PHASE_P3PR_V0_2_15_URL_SUBCOMMAND_DOGFOOD_REPORT.md` |
| **Release** | `v0.2.15-alpha` (release notes: `docs/RELEASE_NOTES_v0.2.15-alpha.md`) |

Note: this is a dogfood / plumbing-validation run, not a content run. The dogfood
page itself is **not** a published artifact — the broken stub from the initial run
was removed from `gh-pages` and the manifest entry was deleted. The fix prevents
future regressions. To produce a real published dogfood page, the next phase
must drive an LLM fill stage to make the audit PASS, then re-publish.
