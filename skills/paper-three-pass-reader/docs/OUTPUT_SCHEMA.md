# Output Schema

This document explains the JSON schema that drives `paper-three-pass-reader`. The authoritative machine-readable schema is [`templates/paper_reading.schema.json`](../templates/paper_reading.schema.json).

---

## Top-level shape

```json
{
  "schema_version": "0.1.0",
  "paper_metadata":     { ... },
  "intake_quality":     { ... },
  "summaries":          { ... },
  "five_cs":            { ... },
  "pass1":              { ... },
  "pass2":              { ... },
  "pass3":              { ... },
  "claims_evidence_map":[ ... ],
  "figures_tables":     [ ... ],
  "glossary":           [ ... ],
  "limitations":        [ ... ],
  "reproduction_plan":  { ... },
  "open_questions":     [ ... ],
  "final_checklist":    [ ... ],
  "paper_outline":      [ ... ],
  "source_resolution":  { ... },
  "candidate_papers":   [ ... ]
}
```

Required (per the JSON schema `required` array): `schema_version`, `paper_metadata`, `intake_quality`, `summaries`, `five_cs`, `pass1`, `pass2`, `pass3`, `claims_evidence_map`, `figures_tables`, `glossary`, `limitations`, `reproduction_plan`, `open_questions`, `final_checklist`.

The remaining fields (`paper_outline`, `source_resolution`, `candidate_papers`) are highly recommended but not strictly required.

---

## Field reference

### `paper_metadata`

Canonical identity of the paper. Required: `title`, `authors`, `year`. Recommended: `venue`, `identifiers`.

```json
{
  "title": "How to Read a Paper",
  "authors": ["S. Keshav"],
  "year": 2007,
  "venue": "SIGCOMM Computer Communication Review",
  "identifiers": {
    "arxiv_id":      null,
    "doi":           null,
    "openreview_id": null,
    "url":           null
  },
  "source_kind":   "complete_paper",
  "reading_mode":  "full_text"
}
```

| Enum | Values |
|---|---|
| `source_kind` | `complete_paper`, `paper_url`, `paper_identifier`, `paper_title`, `paper_metadata`, `paper_excerpt`, `paper_image`, `paper_screenshot`, `paper_topic`, `project_or_repo`, `ambiguous_clue` |
| `reading_mode` | `full_text`, `partial_text`, `abstract_only`, `screenshot_only` |

### `intake_quality`

```json
{
  "input_kind":         "complete_paper",
  "reading_mode":       "full_text",
  "confidence":         "high",
  "needs_confirmation": false,
  "missing_fields":     [],
  "warnings":           []
}
```

`confidence` ∈ `{low, medium, high}`. Set `needs_confirmation: true` whenever the agent has a ranked shortlist rather than a confirmed paper.

### `summaries`

Three summary lengths. The page renders all three side by side.

```json
{
  "one_sentence":   "...",
  "three_sentence": ["...", "...", "..."],
  "ten_sentence":   ["...", "...", "..."]
}
```

`three_sentence` must have exactly 3 entries. `ten_sentence` should have 8–10 entries (the page does not enforce 10; under-shooting is allowed for very short papers).

### `five_cs`

```json
{
  "category":      "...",   // what type of paper is this?
  "context":       "...",   // what does it relate to?
  "correctness":   "...",   // do assumptions and method seem valid?
  "contributions": ["..."], // 1–3 bullets
  "clarity":       "..."    // is the paper well-written?
}
```

### `pass1`

```json
{
  "bird_eye_notes":     "...",
  "decision":           "CONTINUE_FULL",
  "decision_rationale": "..."
}
```

`decision` ∈ `{CONTINUE_FULL, CONTINUE_PARTIAL, STOP, SEEK_REFERENCES_FIRST}`.

### `pass2`

```json
{
  "main_ideas": [
    "...",
    "..."
  ],
  "key_references": [
    {
      "title":   "...",
      "authors": ["..."],
      "year":    2007,
      "why":     "..."
    }
  ]
}
```

### `pass3`

```json
{
  "method_reconstruction": [
    "1. ...", "2. ...", "..."
  ],
  "critical_review": [
    "...", "..."
  ]
}
```

### `claims_evidence_map`

Array of claim records. Every load-bearing claim in the paper should have a row.

```json
{
  "claim_id":          "C-001",
  "claim_text":        "...",
  "evidence_label":    "[Author claim]",
  "evidence_location": "Section 1, paragraph 3",
  "evidence_kind":     "paper_text",
  "confidence":        "high",
  "notes":             "...",
  "needs_verification": false
}
```

| Enum | Values |
|---|---|
| `evidence_label` | `[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]` |
| `evidence_kind`  | `paper_text`, `figure`, `table`, `external` |
| `confidence`     | `high`, `medium`, `low` |

### `figures_tables`

```json
{
  "id":            "F-001",
  "kind":          "figure",   // or "table"
  "number":        "1",
  "title":         "...",
  "explanation":   "...",
  "evidence_label": "[Figure/Table evidence]"
}
```

### `glossary`

```json
[
  { "term": "...", "definition": "..." }
]
```

### `limitations`

Plain string array. Each entry is a single limitation.

### `reproduction_plan`

```json
{
  "dataset":          "...",
  "baseline":         "...",
  "hardware":         "...",
  "steps":            ["1. ...", "2. ..."],
  "sanity_checks":    ["..."],
  "success_criteria": ["..."]
}
```

### `open_questions`

Plain string array. Each entry is one open question.

### `final_checklist`

```json
[
  {
    "question":   "Can I state the paper's main contribution in one sentence?",
    "answerable": true
  }
]
```

`answerable` is a hint for the page UI: items with `answerable: false` can be styled differently.

### `paper_outline`

```json
[
  {
    "title": "1. Introduction",
    "subsections": []
  }
]
```

### `source_resolution` and `candidate_papers`

```json
"source_resolution": {
  "steps": ["Input kind = ...", "Title and author identified from ..."]
},
"candidate_papers": [
  { "title": "...", "year": ..., "identifiers": { ... }, "rank": 1, "rationale": "..." }
]
```

---

## Evidence-label quick reference

| Label | Use when |
|---|---|
| `[Paper evidence]` | Direct quote or faithful paraphrase from the paper text |
| `[Figure/Table evidence]` | Grounded in a specific figure or table |
| `[Author claim]` | Claim attributed to the authors; not independently checked |
| `[Agent inference]` | The agent's interpretation, not in the paper |
| `[Uncertain]` | Confidence is low, evidence is thin |
| `[Needs verification]` | Flagged for follow-up |

If a load-bearing statement has no label, treat it as `[Needs verification]`.

---

## Versioning

`schema_version` follows semantic versioning. Breaking changes bump the major version and require a new sample file. Additive changes bump the minor version and are backward-compatible.

---

## v0.2.1-alpha: audit + fill-pack artifacts

The runner now writes two extra artifact shapes.

### `audit_result.json`

Output of `audit_paper_reading.py`:

```json
{
  "status": "PASS|WARN|FAIL",
  "reading_mode": "...",
  "input_kind": "...",
  "schema_version": "...",
  "counts": {
    "claims_total": ...,
    "claims_with_valid_evidence": ...,
    "final_checklist_questions": ...,
    "draft_placeholders": ...
  },
  "errors": [...],
  "warnings": [...],
  "recommendations": [...]
}
```

### `fill-pack/field_checklist.json`

Per-field status from `fill_pack_writer.py`:

```json
{
  "language": "zh-CN|en",
  "reading_mode": "...",
  "summary": {
    "present": N,
    "draft": N,
    "missing": N,
    "unavailable_due_to_reading_mode": N,
    "needs_verification": N
  },
  "items": [
    {
      "field": "paper_metadata.title",
      "required": true,
      "status": "present|draft|missing|unavailable_due_to_reading_mode",
      "needs_verification": true|false
    }
  ]
}
```

### `fill-pack/draft_status.json`

Aggregate:

```json
{
  "input_kind": "...",
  "reading_mode": "...",
  "confidence": "high|medium|low",
  "needs_confirmation": true|false,
  "counts": {
    "draft_fields_count": ...,
    "missing_fields_count": ...,
    "unavailable_due_to_reading_mode_count": ...,
    "needs_verification_count": ...,
    "claims_total": ...,
    "claims_with_verification_or_uncertain": ...
  },
  "can_render": true,
  "can_publish": true,
  "recommended_next_action": "..."
}
```

### `fill-pack/prompts.json`

Stage-by-stage prompt guidance for downstream agents. Shape depends on language:

- `zh-CN`: each stage is an object with `goal`, `allowed_inputs`, `forbidden`, `fields`, `evidence_labels`, `stop_condition`.
- `en`: each stage is a string summary.



## Cross-links

- Source resolution: see [`SOURCE_RESOLUTION.md`](SOURCE_RESOLUTION.md) for the canonical top-level `source_resolution` object and the legacy `intake_quality.source_resolution` list.
- Resolver trail in the rendered page, audit, fill-pack checklist, and zh-CN quality-gate check all consume that same object.
