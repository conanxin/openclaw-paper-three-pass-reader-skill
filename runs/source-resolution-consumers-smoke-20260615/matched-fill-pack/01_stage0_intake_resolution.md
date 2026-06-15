# 01. Stage 0 — Intake and Resolution

## Goal

Confirm Stage 0 parsing is correct. Is this actually the canonical paper? Is the arXiv ID / DOI valid? Does `needs_confirmation` need to flip to false?

## Allowed materials

- The original input in `input/input.md`.
- External lookup of arXiv / DOI / OpenReview / publisher (for *confirmation* only — do not download the body).
- Runner resolver hint (if any).

## Forbidden

- Do not download the PDF or extract full text. The runner does not auto deep-read.
- Do not auto-promote an ambiguous clue into a canonical paper. If `needs_confirmation = true`, keep it true.

## JSON fields to fill

- `paper_metadata.title`
- `paper_metadata.authors`
- `paper_metadata.year`
- `paper_metadata.identifiers.arxiv_id`
- `paper_metadata.identifiers.doi`
- `intake_quality.ambiguities`
- `intake_quality.source_resolution`

## Evidence label rules

Stage 0 evidence is plain prose; only `intake_quality` sources may carry labels.

## Output format

Edit `work/paper_reading.json` directly. No `[DRAFT]` should remain in this stage.

## Stop condition

intake_quality.needs_confirmation = false AND paper_metadata.title matches arXiv exactly.
