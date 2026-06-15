# Release Notes — paper-three-pass-reader v0.2.7-alpha

**Date:** 2026-06-15
**Tag:** v0.2.7-alpha
**Previous:** v0.2.6-alpha (kept immutable)

## Summary

This release formalizes the resolver round-2 hardening that landed on
`main` after v0.2.6-alpha. v0.2.7-alpha carries no functional regressions
and no schema-breaking changes; it exists so the round-2 work is
covered by an immutable, named release.

## Why v0.2.7 instead of moving v0.2.6

`v0.2.6-alpha` was already published (commit `0fdeedb`). Published tags
are treated as immutable, so the round-2 hardening is released as
`v0.2.7-alpha` rather than force-moving the old tag.

## Included

- **Structured top-level `source_resolution` block** — every draft now
  writes a structured dict with: `steps`, `hint_input`,
  `resolver_source`, `resolver_helper`, `resolver_status`,
  `resolver_match_type`, `confidence`, `matched_paper_id`,
  `matched_canonical_title`, `matched_arxiv_id`, `matched_alias`,
  `matched_repo`, `candidates`, `source_resolution_step`.
- **CLI overlay path** — `p3pr` writes its resolver view to
  `work/resolver_source.json` and the runner reads it via
  `--resolver-source`. A CLI-resolved paper id overrides the runner's
  auto-detect.
- **Runner `--resolver-source` support** — the runner accepts a JSON
  file path and applies it as the final step on top of its
  auto-detected match.
- **Resolver helper degradation behaviour** — the helper call is
  wrapped in `try/except`. On any exception the runner records
  `resolver_status=error`, sets `degraded=ambiguous_clue`, appends a
  warning, and continues with rc=0.
- **Hostile-resolver validation** — `scripts/validate.sh` step 14
  forces the helper to raise and asserts the runner still exits 0 and
  still writes `paper_reading.json` with the expected degradation
  markers. 14 new checks in step 14.
- **Shared resolver trail validation** — the new step also checks
  that every draft has the structured `source_resolution` block with
  the expected keys, and that v0.2.5 smokes remain readable.
- **Documentation cross-link** — `ONE_LINE_CLI.md` and `RESOLVER_HINTS.md`
  both explain the structured `source_resolution` block and the
  degradation behaviour.

## Validation

- `bash scripts/validate.sh` — **195/0 PASS** (167 v0.2.5 baseline + 28
  step 13 + 14 step 14).

## Compatibility

- No schema-breaking changes. Existing run JSON remains readable.
- Existing pages remain unchanged.
- Existing tags are not moved. `v0.2.6-alpha` is preserved at `0fdeedb`.
- The legacy flat `intake_quality.source_resolution` list is preserved
  for back-compat with v0.2.5 smokes and pre-v0.2.7 readers.

## Notes

- This resolver is local and hint-based. It is not a network search
  engine and not a paper database.
- Adding a new paper / repo / alias is still a one-file edit to
  `data/resolver_hints.json`. The CLI, the runner, the tests, and the
  docs all read from that single file.
- Round-2 hardening was authored in commit `e7a7f1e` ("Commit
  round-2 hardening: structured source_resolution + hostile resolver
  degradation"). `v0.2.7-alpha` is annotated on top of `e7a7f1e` plus
  this release's documentation update.
