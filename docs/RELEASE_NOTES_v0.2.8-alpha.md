# Release Notes — paper-three-pass-reader v0.2.8-alpha

**Date:** 2026-06-15
**Tag:** v0.2.8-alpha
**Previous:** v0.2.7-alpha (kept immutable)

## Summary

This release makes downstream consumers use the structured top-level
`source_resolution` block that v0.2.7 introduced. Renderer, audit,
fill-pack, and the zh-CN quality gate all read it through a single
shared utility. Legacy `intake_quality.source_resolution` list is still
supported.

## Why v0.2.8 instead of moving v0.2.7

v0.2.7-alpha was already published (tag → `e7a7f1e`). Published tags
are treated as immutable, so this consumer layer lands as v0.2.8-alpha
rather than force-moving the old tag.

## Included

- **New `source_resolution_utils.py`** — stdlib-only helper that
  exposes `is_structured_source_resolution`,
  `get_source_resolution`, `legacy_source_resolution_to_structured`,
  `summarize_source_resolution`, and `validate_source_resolution`.
  The helper upgrades legacy list / dict inputs on the fly.
- **Renderer Resolver Trail section** — `templates/index.html` adds a
  new `#resolver-trail` card that shows Resolver status, Match type,
  Confidence, Matched paper / id, Matched arXiv ID, Matched repo,
  Resolver source, Source resolution step, Candidate count, Top 3
  candidates, a "Degraded fallback" badge and an error callout. Fully
  localised for zh-CN.
- **Audit source-resolution validation** — `audit_paper_reading.audit`
  adds a `source_resolution` field to the OrderedDict result. WARNs
  on legacy-only, WARNs on missing block (non-weak modes), WARNs on
  `matched` without identity, WARNs on missing confidence, FAILs on
  `error` with no degraded / warning marker.
- **Fill-pack source-resolution checklist** — `fill-pack/00_README.md`
  (zh-CN and en) embeds a Source Resolution 摘要 block plus a
  Source Resolution Checklist the agent must tick off before Stage 0
  closes.
- **zh-CN quality gate source_resolution_check** —
  `quality_gate_zh_cn.run_quality_gate` adds a `source_resolution_check`
  field; the warnings surface as recommendations and never fail the
  gate on their own.
- **Legacy fallback** — v0.2.5 samples that only carry
  `intake_quality.source_resolution` continue to render / audit /
  fill-pack / quality-gate. The shared utility upgrades them.
- **Validation expanded to 210 checks** — `scripts/validate.sh` step
  15 covers utility import, structured read, legacy fallback,
  matched / zh-CN / degraded renderer markers, audit JSON
  `source_resolution` block, quality gate `source_resolution_check`,
  fill-pack Source Resolution summary, zh-CN markers, and re-checks
  of the v0.2.6 runner smoke + p3pr dry-run smoke.

## Compatibility

- Existing run JSON remains readable.
- Legacy `intake_quality.source_resolution` list is still supported.
- Existing pages remain unchanged.
- Existing tags are not moved. v0.2.6-alpha, v0.2.7-alpha stay where
  they are.
- No external API changes.

## Notes

- The structured `source_resolution` block remains local and
  hint-based. Adding a paper is still a one-file edit to
  `data/resolver_hints.json`.
- `confidence` may be the string label (`high` / `medium` / `low`)
  or a float in `[0.0, 1.0]`. Both are accepted by the renderer and
  the audit.
- Run `python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "<hint>"`
  to debug a failing resolution.

## Smoke runs

`runs/source-resolution-consumers-smoke-20260615/` contains four
canonical samples (matched, degraded, legacy-only, zh-cn) plus their
rendered pages, audit JSON, fill-pack directories, and quality-gate
JSON. All are referenced by `scripts/validate.sh` step 15.
