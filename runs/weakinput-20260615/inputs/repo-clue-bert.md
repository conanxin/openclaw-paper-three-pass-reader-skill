# Input case: GitHub repo clue

The user gave a GitHub repo URL and asked the skill to find the associated paper and read it.

## Clue

```
GitHub repo: https://github.com/google-research/bert

"Find the associated paper and create a three-pass reading page if full text can be obtained."
```

## Expected Stage 0 behaviour

- `input_kind: project_or_repo`
- Resolution: repo `google-research/bert` → associated paper
  - title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding"
  - authors: Devlin, Chang, Lee, Toutanova
  - arXiv: 1810.04805
- If the arXiv PDF can be fetched and parsed, `reading_mode: full_text`.
- If fetching fails (network or extraction quality too low), `reading_mode: partial_text` — do NOT pretend `full_text`.
- `source_resolution` trail: repo clue → canonical paper via repo README / paper link / arXiv search → PDF fetch → extraction result.
- Pass 1 / Pass 2 / Pass 3 only if `reading_mode` supports them. If `partial_text`, Pass 3 is a labelled speculative reconstruction.
