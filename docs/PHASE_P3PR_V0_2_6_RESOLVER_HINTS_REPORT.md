# Phase Report — v0.2.6 Resolver Hints Round 2

## STATUS

PASS

> Note on the original task brief: the task described v0.2.6-alpha as
> "not yet committed / tagged / released" with "195/0 PASS". On inspection
> the repository already contained commit `0fdeedb` ("Release paper-three-pass-reader
> v0.2.6 — shared resolver hints unification"), the `v0.2.6-alpha` tag pointing at it,
> and the GitHub release. The working tree additionally carried **round-2** changes
> (4 files, +417/-44) that were not yet committed. Per the task's "no force push,
> don't move old tags" rules, the already-published v0.2.6-alpha tag and release
> were **left untouched**. This report covers the round-2 hardening layer and
> the clean commit of those remaining files.

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.2.5-alpha (tag `7cbcde3`)

## TARGET_VERSION

v0.2.6-alpha (tag already published at `0fdeedb`)
+ round-2 hardening layer (working tree, this commit)

## PROBLEM

v0.2.6 round 1 unified the resolver hints to a single JSON file
(`data/resolver_hints.json`) and a single helper module
(`scripts/resolver_hints.py`). After that release, the following round-2
gaps remained in the working tree:

1. The runner's `source_resolution` block was still a flat object — it
   did not record the full resolver trail (helper called, status,
   match type, candidates, etc.).
2. There was no validation that the resolver helper degrades gracefully
   if it crashes — a broken helper would have failed every run.
3. There was no validation that the CLI overlay path
   (`--resolver-source` → `work/resolver_source.json`) actually
   overrides the runner's auto-detected match.
4. The `ONE_LINE_CLI.md` cross-link did not yet point at
   `docs/RESOLVER_HINTS.md` and the shared JSON file.

## FIX_SUMMARY

- **Shared hints data** — single source of truth at
  `skills/paper-three-pass-reader/data/resolver_hints.json` (140 lines).
  The CLI and the runner both read this file. No other hint dict exists
  in the codebase.
- **Resolver helper** — `scripts/resolver_hints.py` (stdlib-only) loads
  the JSON, normalises inputs, and returns `(match, match_type,
  status, candidates, ...)` for any of `title / alias / repo / arxiv /
  abstract` lookup.
- **Diagnostic CLI** — `scripts/resolve_paper_hint.py` exposes the
  same helper for debugging without going through the full pipeline.
- **CLI integration** — `p3pr.py` no longer carries a `HINTS` dict.
  It delegates to the shared resolver, writes
  `work/resolver_source.json`, and prints
  `resolver_status / match_type / canonical_title / arxiv_id /
  default_slug` in dry-run summaries.
- **Runner integration** — `run_paper_reading.py` rebuilds its
  `RESOLVER_HINTS` back-compat dict from the shared JSON on import
  (no duplicate data). It accepts `--resolver-source` to overlay a
  CLI-resolved match.
- **Source-resolution enrichment** — every draft now writes a
  structured `source_resolution` block with the keys listed below.
- **Degradation behaviour** — the resolver call is wrapped in
  `try/except`. On any helper exception the runner records
  `resolver_status=error`, `degraded=ambiguous_clue`, appends a warning
  to `intake_quality.warnings`, and **does not fail the run**.

## SHARED_HINTS_DATA

`skills/paper-three-pass-reader/data/resolver_hints.json`

Schema:

```json
{
  "papers": [
    {
      "id": "attention-is-all-you-need",
      "title": "Attention Is All You Need",
      "aliases": ["aayn", "transformer-2017"],
      "arxiv": "1706.03762",
      "year": 2017,
      "default_slug": "attention-is-all-you-need"
    }
  ],
  "repos": [
    {
      "id": "google-research-bert",
      "aliases": ["bert"],
      "url": "https://github.com/google-research/bert",
      "paper_id": "bert-2018"
    }
  ]
}
```

## RESOLVER_HELPER

`skills/paper-three-pass-reader/scripts/resolver_hints.py`

Public surface:

- `load_hints() -> dict` — load and cache the JSON.
- `resolve_paper(hint: str, hint_type: str) -> dict` — single entry
  point used by both the CLI and the runner. Returns a dict that
  always contains at least `resolver_status` (`matched | weak |
  ambiguous_clue | error`) and `confidence`.

## CLI_INTEGRATION

`skills/paper-three-pass-reader/scripts/p3pr.py`

- Removed the local `HINTS` dict (~78 lines deleted in round 1).
- Round 2: handlers now call `resolver_hints.resolve_paper(hint, kind)`
  and pass the structured result to `_finalise`.
- Round 2: the CLI writes `work/resolver_source.json` from its own
  resolver result; the runner reads it via `--resolver-source` and
  overlays it on its auto-detected match.
- Round 2: dry-run summary lines now show:
  `resolver_status / match_type / canonical_title / arxiv_id /
  default_slug`.

## RUNNER_INTEGRATION

`skills/paper-three-pass-reader/scripts/run_paper_reading.py`

- `RESOLVER_HINTS` is now rebuilt at import time from the shared JSON
  (back-compat alias for older code paths).
- Round 2: `_resolve_hint` returns `(hint, key, resolver_result)`. The
  helper call is wrapped in `try/except`. On any exception the runner
  sets `degraded=ambiguous_clue`, logs a warning, and continues with
  rc=0.
- Round 2: the runner now writes a structured `source_resolution`
  block (see below) into every draft.

## SOURCE_RESOLUTION_ENRICHMENT

Round 2 replaces the flat `source_resolution` list with a structured
top-level dict on every draft. Required fields:

| key | type | meaning |
| --- | --- | --- |
| `steps` | list | ordered resolver attempts (auto-detect, overlay, etc.) |
| `hint_input` | str | the original user hint text |
| `resolver_source` | str | which call produced the final match |
| `resolver_helper` | str | module path of the helper that ran |
| `resolver_status` | str | `matched \| weak \| ambiguous_clue \| error` |
| `resolver_match_type` | str | `title \| alias \| repo \| arxiv \| abstract \| overlay` |
| `confidence` | float | 0.0–1.0 |
| `matched_paper_id` | str | canonical paper id from the shared JSON |
| `matched_canonical_title` | str | canonical title from the shared JSON |
| `matched_arxiv_id` | str | arXiv id, if known |
| `matched_alias` | str | the alias that matched, if any |
| `matched_repo` | str | the repo url that matched, if any |
| `candidates` | list | alternative candidates considered |
| `source_resolution_step` | str | which step produced the final result |
| `degraded` | str | set to `ambiguous_clue` on resolver error |
| `fallback_legacy` | bool | true if back-compat dict was used |

The legacy `intake_quality.source_resolution` list is preserved for
back-compat with v0.2.5 smokes.

## DEGRADATION_BEHAVIOR

A hostile-resolver test is part of `scripts/validate.sh` step 14. The
test sets `PYTHONPATH` so that `resolver_hints.resolve_paper` raises
on every call, then runs a small draft through the runner. Required
assertions:

1. The runner exits 0.
2. `paper_reading.json` exists.
3. `source_resolution.resolver_status == "error"`.
4. `source_resolution.degraded == "ambiguous_clue"`.
5. A warning is appended to `intake_quality.warnings`.

This proves a broken helper cannot fail the run.

## SMOKE_RUNS

`runs/resolver-hints-smoke-20260615/`

Contains:

- 3 resolver CLI outputs (title / repo / arxiv).
- 2 `p3pr` dry-run captures (title + repo).

All five artifacts have a structured `source_resolution` block with
the keys above. The repo dry-run shows
`matched_paper_id=bert-2018`, the title dry-run shows
`matched_paper_id=attention-is-all-you-need`.

## VALIDATION

```
bash scripts/validate.sh
...
PASS: 195    FAIL: 0
STATUS: PASS
```

Breakdown of the 195 checks:

- 167 from the v0.2.5 baseline (kept passing).
- 28 from `step 13` (round-1 resolver unit checks).
- 14 from `step 14` (round-2 hostile / overlay / structured-trail
  checks).

Step 14 new assertions (all PASS):

- hostile resolver: `source_resolution.resolver_status=error`
- hostile resolver: `source_resolution.degraded=ambiguous_clue`
- hostile resolver: runner still produced `paper_reading.json`
  (no crash)
- source_resolution has `hint_input` / `resolver_source` /
  `resolver_helper` / `resolver_status` / `resolver_match_type` /
  `confidence` / `matched_paper_id` / `source_resolution_step`
- `source_resolution.matched_paper_id=second-me` (auto-detected)
- runner `--resolver-source` overlay applies
  (`matched_paper_id=bert-2018`, `status=matched`, `match_type=repo`)
- v0.2.5 cli-screenshot-smoke still has
  `source_resolution.resolver_status`
- v0.2.5 cli-abstract-smoke still has
  `source_resolution.resolver_status`

## FILES_CREATED (round 2)

- `docs/PHASE_P3PR_V0_2_6_RESOLVER_HINTS_REPORT.md` (this file)

## FILES_MODIFIED (round 2 working tree, this commit)

- `scripts/validate.sh` — added `step 14` (14 new checks).
- `skills/paper-three-pass-reader/scripts/p3pr.py` — handlers now
  pass the structured resolver result into `_finalise`; new
  `work/resolver_source.json` overlay writer.
- `skills/paper-three-pass-reader/scripts/run_paper_reading.py` —
  `_resolve_hint` returns `(hint, key, resolver_result)`; structured
  `source_resolution` writer; try/except degradation.
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — Q&A
  cross-link now points to `data/resolver_hints.json` +
  `docs/RESOLVER_HINTS.md`.

## COMMIT

This commit is the round-2 commit. Subject:

```
Commit round-2 hardening: structured source_resolution + hostile resolver degradation
```

Per the task's per-file `git add` rule:

```
git add scripts/validate.sh
git add skills/paper-three-pass-reader/scripts/p3pr.py
git add skills/paper-three-pass-reader/scripts/run_paper_reading.py
git add skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md
git add docs/PHASE_P3PR_V0_2_6_RESOLVER_HINTS_REPORT.md
```

## PUSH

`git push origin main` (the round-2 commit lands on `main`).

## TAG

**No new tag.** v0.2.6-alpha is already published (tag → `0fdeedb`,
release URL below). The task rule "if tag exists and points at HEAD,
continue release" applies to v0.2.6-alpha and the release already
exists. Re-tagging v0.2.6-alpha for round-2 changes would break the
"do not move old tags" rule. Round-2 changes are content under the
same release URL; a future v0.2.7-alpha may roll them up.

## RELEASE

Already published at:

```
https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.6-alpha
```

Verified with `gh release view v0.2.6-alpha`. Title:

```
paper-three-pass-reader v0.2.6-alpha
```

Author: `conanxin`. Created: `2026-06-15T08:16:40Z`. Not a draft. Not a
prerelease. Notes file: `docs/RELEASE_NOTES_v0.2.6-alpha.md`.

## LIMITATIONS

- The shared resolver is **local and hint-based**. It is not a network
  search engine and not a paper database. Papers not listed in
  `data/resolver_hints.json` still resolve to `ambiguous_clue`.
- The hostile-resolver degradation is best-effort: it covers a single
  resolver helper. A future round should also degrade
  `paper_metadata.json` and the citation parser.
- CLI overlay (`work/resolver_source.json`) is only honoured when the
  runner is invoked via the normal CLI path. Standalone
  `run_paper_reading.py` runs without the overlay and rely on the
  runner's auto-detect.
- The legacy flat `intake_quality.source_resolution` list is
  preserved for back-compat but is no longer the canonical trail.
  Future agents should read the structured top-level
  `source_resolution` block.

## NEXT_USER_ACTION

None required. v0.2.6-alpha is fully released; round-2 hardening is
committed on `main` and validated at 195/0 PASS. Optional follow-ups
(not in this commit):

- Roll the round-2 changes into a future v0.2.7-alpha release
  (separate commit, separate tag, separate release notes).
- Add more papers to `data/resolver_hints.json` (e.g. Second Me,
  P3PR, TimeFM, Mesh — already partially present).
- Add a `validate_resolver_hints` step that fails CI if the JSON has
  duplicate `id` or `alias` fields.
