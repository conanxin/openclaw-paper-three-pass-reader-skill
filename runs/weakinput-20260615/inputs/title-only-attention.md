# Input case: title-only

The user provided only the title of the paper. No authors, no abstract, no PDF, no URL.

## Clue

```
Attention Is All You Need
```

## Expected Stage 0 behaviour

- `input_kind: paper_title`
- High-confidence title → canonical paper resolution (well-known landmark paper).
- If full text can be obtained from arXiv (1706.03762), `reading_mode: full_text`.
- `source_resolution` trail: title clue → arXiv search → canonical paper → PDF fetch → `pdftotext` → `full_text`.
- No pretending. If the PDF cannot be fetched or parsed, drop back to `partial_text` and flag it.
