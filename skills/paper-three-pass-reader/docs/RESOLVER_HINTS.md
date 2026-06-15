# Resolver Hints — v0.2.6

This document describes the **shared resolver hints** that drive paper / repo / arXiv resolution across the entire paper-three-pass-reader stack. The single source of truth is one JSON file; the resolver helper, the CLI, the runner, the validation, and the docs all read from it.

---

## 1. Why unify

Before v0.2.6 the same paper / repo hints were duplicated in **two places**:

- `p3pr.py` had its own `HINTS` dict (used for dry-run resolution).
- `run_paper_reading.py` had its own `RESOLVER_HINTS` dict (used for canonical metadata).

That meant:

- Adding a new paper required editing two files and remembering to keep them in sync.
- The CLI's resolver was a fuzzy substring matcher; the runner's was a fuzzy substring matcher; neither handled arXiv ids cleanly.
- There was no way to test the resolver in isolation.
- The `p3pr` CLI could not distinguish "title matched" from "alias matched" from "arxiv id matched".

v0.2.6 fixes all of that.

---

## 2. The data source

`skills/paper-three-pass-reader/data/resolver_hints.json`

```json
{
  "schema_version": "0.2.6",
  "papers": [
    {
      "id": "attention-is-all-you-need",
      "canonical_title": "Attention Is All You Need",
      "aliases": ["attention is all you need", "transformer paper", "transformers"],
      "authors": ["Ashish Vaswani", "..."],
      "year": "2017",
      "venue": "NeurIPS 2017",
      "arxiv_id": "1706.03762",
      "paper_url": "https://arxiv.org/abs/1706.03762",
      "pdf_url": "https://arxiv.org/pdf/1706.03762",
      "repo_urls": [],
      "default_slug": "attention-is-all-you-need",
      "field": "NLP / sequence transduction",
      "notes": "Introduced the Transformer architecture based solely on attention mechanisms."
    }
  ],
  "repo_hints": [
    {
      "repo_url": "https://github.com/google-research/bert",
      "paper_id": "bert",
      "match_patterns": ["google-research/bert", "github.com/google-research/bert"]
    }
  ]
}
```

Anchor papers shipped today (5): `attention-is-all-you-need`, `bert`, `how-to-read-a-paper`, `second-me`, `paper-three-pass-reader-skill`.

To add a new paper, add an entry to `papers` and (optionally) a matching entry to `repo_hints` if you want a GitHub URL fragment to resolve to that paper.

---

## 3. The resolver helper

`skills/paper-three-pass-reader/scripts/resolver_hints.py` (stdlib-only).

```python
from resolver_hints import (
    load_hints,
    resolve_title,
    resolve_arxiv,
    resolve_repo,
    resolve_any,
    paper_to_runner_overrides,
)
```

All four resolvers return a uniform dict:

```python
{
  "status": "matched" | "ambiguous" | "not_found",
  "match_type": "title" | "alias" | "arxiv" | "repo" | "none",
  "confidence": "high" | "medium" | "low",
  "paper": {...},            # the canonical paper entry (or {} for not_found)
  "candidates": [...],       # list of candidate paper entries (ambiguous / matched)
  "source_resolution_step": "title_resolver: matched canonical/alias of attention-is-all-you-need"
}
```

Matching rules:

- **Title**: case-insensitive, whitespace- and quote-collapsed. Exact match wins; substring is fuzzy with `low` confidence and an `ambiguous` status if more than one paper matches.
- **Alias**: each paper can carry an `aliases` list. Same matching rules as title.
- **arXiv**: id is extracted from a bare id (`2503.08102`) or an arXiv URL. Match is exact on `arxiv_id`.
- **Repo**: GitHub URL is normalized to `owner/repo`. Matched against `match_patterns` first, then against any paper's `repo_urls` as a fallback.

---

## 4. The standalone CLI

```bash
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "Attention Is All You Need"
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py repo https://github.com/google-research/bert
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py arxiv 2503.08102
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py any "second me" --input-kind paper_title
```

Output is JSON, easy to read for humans and easy to parse for tests.

---

## 5. How the runner and CLI use it

### `p3pr.py`

- Imports `load_hints`, `resolve_title`, `resolve_arxiv`, `resolve_repo`, `resolve_any` from `resolver_hints`.
- The historical local `HINTS` dict is gone.
- All `p3pr` subcommands (`arxiv`, `title`, `abstract`, `screenshot`, `repo`, `pdf`) call `_resolve_hint()` which now delegates to the shared resolver.
- The dry-run summary now prints resolver diagnostics:
  ```
  P3PR_RESOLVER_STATUS: matched
  P3PR_RESOLVER_MATCH_TYPE: title
  P3PR_CANONICAL_TITLE: Attention Is All You Need
  P3PR_ARXIV_ID: 1706.03762
  P3PR_DEFAULT_SLUG: arxiv-1706.03762
  ```
- When the resolver finds an arXiv id (via title / alias / repo), the CLI auto-derives the slug prefix from `screenshot-` / `abstract-` / `repo-` / `title-` to `arxiv-`. The user can still override with `--slug`.

### `run_paper_reading.py`

- Imports `load_hints` from `resolver_hints`.
- The historical `RESOLVER_HINTS` dict is now auto-built from `resolver_hints.json`. It is still indexed by lowercased canonical title + aliases + repo URL, so any code that imports `r.RESOLVER_HINTS["attention is all you need"]` continues to work.
- `_resolve_hint()` now prefers the shared resolver (`resolve_any`) and falls back to the legacy substring matcher if the resolver returns `not_found` or raises.

---

## 6. Adding a new paper

1. Open `skills/paper-three-pass-reader/data/resolver_hints.json`.
2. Add an entry to `papers` with at minimum: `id`, `canonical_title`, `aliases` (can be empty), `arxiv_id` (or `null`), `paper_url` (or `null`), `default_slug`, `field`.
3. (Optional) Add a `repo_hints` entry if a GitHub URL should resolve to this paper.
4. Run `python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "<your title>"` to confirm.
5. Run `bash scripts/validate.sh` — the new paper will be covered by the v0.2.6 check set.

---

## 7. Boundaries

- The shared resolver does **no network search**. It only matches against the curated `resolver_hints.json`.
- Unknown input does **not** fail the CLI. It logs `P3PR_RESOLVER_STATUS: not_found`, keeps the weak-mode default, and shows the user how to proceed.
- The resolver is **not** an LLM. It returns structured data only. Quality of paper reading still comes from the agent / human filling the fill-pack.

---

## 8. Validation

Step 13 of `scripts/validate.sh` covers this unification:

- 13a: `resolver_hints.json` exists, parses, and has the 5 anchor papers.
- 13b: `resolver_hints.py` loads via stdlib import.
- 13c: `resolve_paper_hint.py` CLI works for title / repo / arxiv / any.
- 13d: unknown input returns `not_found` cleanly.
- 13e: aliases work (e.g. `transformers` → Attention).
- 13f: `p3pr.py` no longer has a local `HINTS` dict.
- 13g: `p3pr.py` imports from `resolver_hints`.
- 13h: `run_paper_reading.py` imports from `resolver_hints`.
- 13i: runner `RESOLVER_HINTS` back-compat dict has ≥ 8 keys (we ship 26).
- 13j: historical keys still resolve correctly.
- 13k: `p3pr` dry-run shows resolver details.
- 13l: `p3pr title` dry-run auto-resolves to arXiv 1706.03762.
- 13m: `p3pr repo` dry-run auto-resolves BERT to arXiv 1810.04805.
- 13n: `p3pr screenshot` v0.2.6 smoke auto-detects arXiv from transcript.

Total: 28 new checks in step 13. Total validation: 179/0 PASS as of v0.2.6.

---

## Structured `source_resolution` block (v0.2.7)

As of v0.2.7, every draft writes a top-level `source_resolution` object that records
the full resolver trail, not just a flat match. The block has these keys:

| key | type | meaning |
| --- | --- | --- |
| `steps` | list | ordered resolver attempts (auto-detect, overlay, etc.) |
| `hint_input` | str | the original user hint text |
| `resolver_source` | str | which call produced the final match (e.g. `p3pr-cli`, `runner-auto`, `overlay`) |
| `resolver_helper` | str | module path of the helper that ran |
| `resolver_status` | str | `matched \| weak \| ambiguous_clue \| error` |
| `resolver_match_type` | str | `title \| alias \| repo \| arxiv \| abstract \| overlay` |
| `confidence` | float | 0.0–1.0 |
| `matched_paper_id` | str | canonical paper id from `resolver_hints.json` |
| `matched_canonical_title` | str | canonical title |
| `matched_arxiv_id` | str | arXiv id, if known |
| `matched_alias` | str | the alias that matched, if any |
| `matched_repo` | str | the repo URL that matched, if any |
| `candidates` | list | alternative candidates considered |
| `source_resolution_step` | str | which step produced the final result |

The CLI writes its resolver result to `work/resolver_source.json` and the runner reads
that file via `--resolver-source`, overlaying the CLI's match on top of its own
auto-detect. A CLI-resolved paper id always wins over a weak auto-detect.

The legacy flat `intake_quality.source_resolution` list is preserved for back-compat
with v0.2.5 smokes and pre-v0.2.7 readers.

---

## Resolver degradation behaviour (v0.2.7)

The runner's resolver helper call is wrapped in `try/except`. If the helper raises
on every call, the runner:

1. Records `resolver_status=error` in `source_resolution`.
2. Sets `degraded=ambiguous_clue` in `source_resolution`.
3. Appends a warning to `intake_quality.warnings`.
4. Continues with rc=0 and still writes `paper_reading.json`.

This means a broken helper can never fail a run. A hostile-resolver test in
`scripts/validate.sh` step 14 forces the helper to raise on every call and asserts
all four behaviours above. The full validation remains PASS at 195/0.
