# Input case: abstract-only

The user provided only the abstract / opening paragraph of the paper. No full body.

## Clue

```
Title: How to Read a Paper
Author: S. Keshav
Year: 2007
Venue: SIGCOMM Computer Communication Review

Abstract excerpt:
"Researchers spend a great deal of time reading research papers. However, this
experience is often taken for granted and few people are taught how to read a
paper effectively. This paper proposes a simple three-pass method for reading
a research paper, with the first pass giving a bird's-eye view, the second pass
giving a deeper understanding, and the third pass reconstructing the paper as
if you were its author."
```

## Expected Stage 0 behaviour

- `input_kind: paper_excerpt`
- `reading_mode: abstract_only` — do NOT pretend to have read the full paper.
- Stage 0 must reflect that the full body is missing.
- `source_resolution` trail: abstract clue → canonical paper identification → `abstract_only`.
- Pass 2 / Pass 3 must be explicitly marked unavailable.
- Claims map entries must use `[Author claim]`, `[Uncertain]`, or `[Needs verification]` — no `[Paper evidence]` for claims that are not grounded in the abstract.
- `reading_decision: SEEK_FULL_TEXT` (the obvious next step).
