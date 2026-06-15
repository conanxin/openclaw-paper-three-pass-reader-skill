# Release Notes — v0.2.2-alpha

## Overview

Patch release following the v0.2.1-alpha auto-fill smoke run on arXiv:2503.08102 ("AI-native Memory 2.0: Second Me"). Two small skill bug fixes discovered during the smoke run, plus documentation.

## Changes

### Bug Fixes

- **runner (`run_paper_reading.py`)**: When `--audit` fails and `--fill-pack` is requested, the runner no longer exits immediately. The fill-pack is the task list to fix the audit findings; it must be written even when the audit returns FAIL. Render and publish are still blocked until the draft is fixed and audit passes.
- **render (`render_page.py`)**: `pass2.key_references` entries may now be either dicts (with `title`/`authors`/`year`/`why`) or plain strings. Strings are coerced to dicts with the string as `title`. This matches the existing pattern already used for `claims_evidence_map`.

### Documentation

- New `docs/AUTOFILL_RUNS.md` — indexes auto-fill runs (real PDF + fill-pack + audit flow).
- New `docs/PHASE_P3PR_V0_2_2_FULLTEXT_AUTO_FILL_SMOKE_REPORT.md` — full phase report for the Second Me smoke run.
- Updated `docs/REALPAPER_RUNS.md` — pointer to the new auto-fill run.

## Validation

- `scripts/validate.sh`: **108/0 PASS** (no regression).

## Known Issues / Notes

- Table 2 cell values in the Second Me paper were not extractable by `pdftotext -layout`; flagged `[Needs verification]` in the generated page. A richer PDF extractor (PyMuPDF, pdfplumber) could improve this in future runs.
- The task spec for this smoke run referenced terms (HMM / Me-Alignment / Mind Palace / MoE / TIME) that belong to a different paper. The skill correctly flagged these as `[Needs verification]` rather than hallucinating them.

## Artifacts

- Skill repo: `conanxin/openclaw-paper-three-pass-reader-skill`
- Tag: `v0.2.2-alpha`
- Commit: `28bb6ab`
- Published page: https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/
