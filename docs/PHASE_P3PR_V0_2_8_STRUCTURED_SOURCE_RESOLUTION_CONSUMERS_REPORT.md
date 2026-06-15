# PHASE P3PR-V0.2.8 — Structured Source-Resolution Consumers — Report

- STATUS: PASS
- PROJECT_DIR: /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill
- BASE_VERSION: v0.2.7-alpha
- TARGET_VERSION: v0.2.8-alpha

## PROBLEM

In v0.2.7 the runner started emitting a structured top-level
`source_resolution` object as the canonical paper-identity trail. v0.2.8 makes
every downstream consumer actually read it:

1. The renderer should display a Resolver Trail section.
2. The audit should validate the structured object.
3. The fill-pack should explain it and include a checklist.
4. The zh-CN quality gate should report a `source_resolution_check`.
5. Legacy `intake_quality.source_resolution` lists must keep working.

## FIX_SUMMARY

A new stdlib-only utility (`source_resolution_utils.py`) centralises the
read/validate/fallback logic. The renderer, audit, fill-pack writer, and
zh-CN quality gate all import it. The renderer adds a "Resolver Trail"
section in the page. The audit, fill-pack, and zh-CN quality gate extend
their JSON / Markdown output accordingly. Validation gains step 15 with 15
new smoke checks across the four sample types.

## SOURCE_RESOLUTION_UTILITY

`skills/paper-three-pass-reader/scripts/source_resolution_utils.py`

Public functions:

- `is_structured_source_resolution(value)` — true when the object carries the
  v0.2.7 schema (`resolver_status`, `confidence`, `structured=True`).
- `get_source_resolution(data)` — returns the top-level structured object, or
  the legacy `intake_quality.source_resolution` list converted to the
  structured shape, or an empty dict.
- `legacy_source_resolution_to_structured(legacy)` — upgrades the v0.2.5 list
  to the structured object (used by `get_source_resolution`).
- `summarize_source_resolution(data)` — renderer-friendly dict.
- `validate_source_resolution(data)` — returns `(errors, warnings)`.

`--path <json-file>` CLI mode prints a human-readable summary.

## RENDERER_CONSUMER

`skills/paper-three-pass-reader/scripts/render_page.py`

- Imports `summarize_source_resolution` / `get_source_resolution` from the
  utility.
- Adds a "Resolver Trail" section with status badge, confidence, match type,
  matched paper / arXiv ID / repo, resolver source, and legacy-fallback
  notice.
- A "Degraded fallback" badge shows when `degraded` is non-empty.
- The `zh-CN` UI map gets `解析状态` / `置信度` / `匹配 arXiv ID` labels.

## AUDIT_CONSUMER

`skills/paper-three-pass-reader/scripts/audit_paper_reading.py`

- Top-level guarded import of the utility (so a missing utility cannot crash
  the audit).
- `audit_summary` JSON now includes a `source_resolution` block with
  `status`, `structured`, `legacy_fallback`, `warnings`, `errors`, `summary`.
- The audit reports `WARN` when the structured object is missing, the
  resolver status is `error` / `ambiguous_clue`, or matched title / arXiv ID
  is empty.

## FILL_PACK_CONSUMER

`skills/paper-three-pass-reader/scripts/fill_pack_writer.py`

- `00_README.md` (both `en` and `zh-CN`) gets a **Source Resolution
  summary** section that lists: hint input, resolver status, match type,
  confidence, matched paper, matched arXiv ID, matched repo, resolver
  source, candidate count, structured trail, legacy fallback, top
  candidates, and a degraded-fallback warning when applicable.
- A **Source Resolution Checklist** is appended to `01_stage0_intake_resolution.md`
  (both languages) — five items including "ask the user to confirm identity
  when `ambiguous_clue` or `error`".
- A "Cross-links" footer points the agent at `SOURCE_RESOLUTION.md`,
  `RESOLVER_HINTS.md`, `AUDIT.md`, and `AGENT_FILL_PACK.md`.

## ZH_CN_QUALITY_GATE_CONSUMER

`skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`

- Imports the utility.
- When `target_language` / `ui_language` is `zh-CN`, the result JSON now
  includes a `source_resolution_check` block:
  ```json
  {
    "source_resolution_check": {
      "structured": true,
      "legacy_fallback": false,
      "resolver_status": "matched",
      "warnings": [],
      "errors": []
    }
  }
  ```
- Missing structured object / `error` / `ambiguous_clue` / missing matched
  title or arXiv ID → `WARN`. Existing content-quality checks remain
  unchanged.

## SMOKE_RUNS

`runs/source-resolution-consumers-smoke-20260615/`

- `structured-matched/` — Title: *Attention Is All You Need*,
  `resolver_status=matched`, `matched_paper_id=attention-is-all-you-need`,
  `matched_arxiv_id=1706.03762`.
- `structured-degraded/` — hostile resolver input, `degraded=ambiguous_clue`,
  non-empty warnings, audit reports warnings, page shows the degraded
  badge.
- `legacy-only/` — only `intake_quality.source_resolution` list (no
  top-level structured block), utility fallback succeeds, all four
  consumers still run.
- `zh-cn-structured/` — `target_language=zh-CN`, page labels in Chinese.

All four samples are rendered to `paper-reading-output`, audited, gated
(`zh-CN` only), and fill-pack'd (both languages).

## VALIDATION

`scripts/validate.sh`

- Step 15 — 15 new checks:
  - utility imports cleanly
  - utility reads structured source_resolution from matched sample
  - legacy-only sample produces fallback summary and a legacy warning
  - matched render contains "Resolver status" / "Confidence" / "arXiv ID"
  - zh-cn render contains `解析状态` / `置信度` / `匹配 arXiv ID`
  - degraded render contains "Degraded fallback" badge + "Resolver status"
  - audit JSON includes `source_resolution` block with `summary`
  - quality_gate_zh_cn JSON includes `source_resolution_check`
  - matched / degraded / legacy-only / zh-cn fill-pack 00_README has the
    "Source Resolution" summary
  - zh-cn fill-pack 00_README has `解析状态` / `输入线索`
  - v0.2.6 runner smoke still has structured source_resolution
  - p3pr dry-run smoke still has structured resolver output
- Final tally: **PASS: 210  FAIL: 0**
- Status: `STATUS: PASS`

## FILES_CREATED

- `skills/paper-three-pass-reader/scripts/source_resolution_utils.py`
- `skills/paper-three-pass-reader/docs/SOURCE_RESOLUTION.md`
- `docs/RELEASE_NOTES_v0.2.8-alpha.md`
- `docs/PHASE_P3PR_V0_2_8_STRUCTURED_SOURCE_RESOLUTION_CONSUMERS_REPORT.md`
  (this file)
- `runs/source-resolution-consumers-smoke-20260615/structured-matched/`
- `runs/source-resolution-consumers-smoke-20260615/structured-degraded/`
- `runs/source-resolution-consumers-smoke-20260615/legacy-only/`
- `runs/source-resolution-consumers-smoke-20260615/zh-cn-structured/`
  (each smoke dir contains: `paper_reading.json`, rendered `index.html`,
  `assets/`, `data/`, `reports/`, plus `fill-pack/`)

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/render_page.py`
  (Resolver Trail section, utility import)
- `skills/paper-three-pass-reader/scripts/audit_paper_reading.py`
  (utility import, `source_resolution` block, guarded import for
  Pyright / lint)
- `skills/paper-three-pass-reader/scripts/fill_pack_writer.py`
  (Source Resolution summary, Source Resolution Checklist, Cross-links)
- `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`
  (utility import, `source_resolution_check` block, new rules)
- `skills/paper-three-pass-reader/templates/index.html`
  (Resolver Trail section skeleton, mini renderer support)
- `skills/paper-three-pass-reader/templates/style.css`
  (`badge-warn` style for the degraded badge)
- `scripts/validate.sh` (step 15)
- `README.md` (v0.2.8 highlights)
- `README.zh-CN.md` (v0.2.8 highlights)
- `CHANGELOG.md` (v0.2.8-alpha entry)
- `skills/paper-three-pass-reader/docs/RESOLVER_HINTS.md` (cross-link)
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` (cross-link)
- `skills/paper-three-pass-reader/docs/RUNNER.md` (cross-link)
- `skills/paper-three-pass-reader/docs/AUDIT.md` (cross-link)
- `skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md` (cross-link)
- `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md` (cross-link)
- `skills/paper-three-pass-reader/docs/OUTPUT_SCHEMA.md` (cross-link)
- `skills/paper-three-pass-reader/docs/USAGE.md` (cross-link)

## COMMIT

- Branch: `main`
- Commit subject: `Consume structured source resolution across pipeline`
- Commit includes all of the files above.

## PUSH

- `git push origin main` — succeeded.

## TAG

- `git tag -a v0.2.8-alpha -m "v0.2.8-alpha"` — created and points at the
  v0.2.8 commit.
- `git push origin v0.2.8-alpha` — succeeded.

## RELEASE

- `gh release create v0.2.8-alpha --title "paper-three-pass-reader
  v0.2.8-alpha" --notes-file docs/RELEASE_NOTES_v0.2.8-alpha.md` —
  succeeded.
- URL: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.8-alpha

## LIMITATIONS

- The structured `source_resolution` object is not persisted on disk by
  the renderer — it lives only in `paper_reading.json` and in the rendered
  page. Future versions may want a top-level `source_resolution.json` for
  archival.
- Hostile-resolver smoke exercises one failure shape; the schema validator
  is generic but the `degraded` field only carries a string label.
- The new resolver-trail UI section uses the `zh-CN` UI map labels; other
  languages (e.g. ja-JP) fall back to the English labels until their UI
  map is extended.

## NEXT_USER_ACTION

- Verify the GitHub Release page renders the notes correctly.
- (Optional) Provide additional resolver inputs (PDF path, GitHub repo
  URLs) to exercise the renderer in a real run.
- (Optional) Pin the v0.2.8-alpha tag as a `latest` in a downstream
  project that depends on the `paper-three-pass-reader` skill.
