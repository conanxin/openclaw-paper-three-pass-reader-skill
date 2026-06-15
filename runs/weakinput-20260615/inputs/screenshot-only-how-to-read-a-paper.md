# Input case: screenshot-only / OCR transcript

The user provided a screenshot of part of the paper (or the OCR/VLM transcript of one). The visible text below is what the OCR / VLM returned. Nothing else is available.

## Clue

```
Source: photo of printed title page + a portion of the body

Visible text from screenshot:

Title: How to Read a Paper
Author: S. Keshav
Affiliation: University of Waterloo
Year: 2007
Venue: SIGCOMM Computer Communication Review (CCR)

Section headings visible in the screenshot:
- Abstract
- Introduction
- The Three-Pass Approach
- The First Pass

Method fragments visible:
- First pass (5–10 minutes): read title, abstract, intro, section headings,
  conclusion, references; glance at figures and skim the math.
- The first pass answers the Five Cs: Category, Context, Correctness,
  Contributions, Clarity.
- Second pass (~1 hour): read the body with care, skipping proofs.
- Third pass (1–4 hours): re-implement the paper as if you were its author.
```

## Expected Stage 0 behaviour

- `input_kind: paper_screenshot`
- `reading_mode: screenshot_only` — do NOT pretend to have read the full paper.
- `extraction_quality: medium` (visible headings + method fragments, but body and references are mostly missing).
- `confidence: medium` (paper identification is high from title + author + venue; body coverage is low).
- `missing_parts` MUST include at least: `full_body`, `full_references`, `figures`, `tables`, `claims_map_completeness`.
- `source_resolution` trail: screenshot → OCR/VLM → partial text → `screenshot_only`.
- Pass 1 is allowed but only as a "preliminary reading from visible fragments".
- Pass 2 / Pass 3 must be marked unavailable until full text is available.
- All claims must carry `[Uncertain]` or `[Needs verification]` — no `[Paper evidence]` for content beyond what's literally in the screenshot.
- The Intake Status panel in the page must visibly display `screenshot_only` in red.
