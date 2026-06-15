# paper-three-pass-reader v0.2.10-alpha

## Summary

This release adds **published-pages regression audit** — a stdlib-only tool that reads `published_pages.json`, fetches every live page, and produces a structured report of renderer regressions, so that the team can make evidence-based decisions about which pages to republish next.

No published page is changed by this release. The audit is read-only by design.

## What changed

### New: `skills/paper-three-pass-reader/scripts/audit_published_pages.py`

A new stdlib-only CLI tool. Reads `published_pages.json` (live URL or local file), fetches every page, and produces a JSON + Markdown audit report covering:

- **HTTP / fetch** — non-200 responses and empty bodies.
- **Template tag leak** — `{% %}` / `{{ }}` / `{% else %}` / `{# #}` / `No key references recorded`.
- **Old footer** — pages still showing `v0.1.0-alpha`.
- **Raw Python dict** — pages still showing `{'label': …}`.
- **zh-CN UI markers** — pages whose slug has `-cn` but which lack 5+ of the 6 zh-CN UI markers.
- **Resolver Trail** — pages missing the v0.2.8+ Resolver Trail / 解析状态 block.
- **Claims-Evidence** — pages missing Claims / Evidence sections, pages with empty `<code></code>` claim IDs.
- **Glossary** — pages missing Glossary / 关键术语, or with chips that have no explicit `chip-body` definition block.
- **Essay / talk** — pages whose slug matches `you-and-your-research / essay / talk / lecture / keynote` and which lack `实践计划 / 结构说明 / 相关脉络`.
- **Self-test** — a `--selftest-dir <dir>` mode that runs six synthetic pages through the same checks (template leak / raw dict / old footer / essay / zh-CN weak / pass) and reports which expected codes were detected.

### New: `skills/paper-three-pass-reader/docs/PUBLISHED_PAGES_AUDIT.md`

The canonical reference for the audit tool: what it checks, the PASS/WARN/FAIL semantics, the JSON + Markdown output format, and when to run it.

### New: `scripts/validate.sh` step 17

`scripts/validate.sh` now includes a 17th step that runs the audit's selftest mode. The step:

1. Runs `audit_published_pages.py --help` to make sure the script is wired up.
2. Creates 6 temporary synthetic pages under a `mktemp -d` directory.
3. Runs the audit in `--selftest-dir` mode and writes the JSON + Markdown reports.
4. Verifies the JSON report contains `pages_total / pages_checked / issues_by_severity / pages / recommendations`.
5. Verifies the Markdown report contains `## Summary / ## Pages / ## Recommendations`.
6. Verifies each synthetic page triggered its expected issue code (template_leak, raw_dict, old_footer, essay_missing_markers, zh_cn_markers_weak, pass).
7. Verifies the `fake-pass` page ended at `PASS`.

Validation: **225/0 PASS** (was 220/0 PASS at v0.2.9).

### New: `runs/published-pages-audit-20260615/audit.json` + `audit.md`

The first live audit run. It found that 8 of the 9 published pages (all rendered before v0.2.9) still carry legacy-render artefacts. The v0.2.9-re-published `you-and-your-research-cn` page passes 0/0. The audit result is stored in `runs/published-pages-audit-20260615/audit.json` (machine-readable) and `audit.md` (human-readable).

## Live audit at release time

| Pages | Pass | Warn | Fail |
|---|---|---|---|
| 9 (manifest) + 1 (root) | 1 | 1 | 8 |

| Failing page | Most common issues |
|---|---|
| `attention-is-all-you-need` | template_leak, old_footer, missing_resolver_trail, missing_claims_section, missing_glossary |
| `weakinput-title-attention-is-all-you-need` | same as above |
| `weakinput-abstract-how-to-read-a-paper` | same as above |
| `weakinput-screenshot-how-to-read-a-paper` | same as above |
| `weakinput-repo-bert` | same as above |
| `runner-title-attention` | same as above |
| `second-me-fulltext-autofill` | same as above |
| `second-me-human-inspired-memory-cn` | template_leak, old_footer, missing_resolver_trail, missing_claims_section, no_visible_claim_id |

This is the audit's expected first run. The 8 failing pages were rendered before v0.2.9; they will be re-rendered (deliberately, one at a time) in a future cycle. The audit's `recommendations` block lists them.

## Compatibility

- No breaking changes to the renderer, the template, the runner, the CLI, or the manifest schema.
- All previously-published pages remain published and reachable. No tag is moved.
- Existing `paper_reading.json` files are still rendered correctly by the v0.2.9 renderer.
- The audit tool itself is fully stdlib-only and can be re-run on any host with Python 3.11+.

## Known minor warnings

- The audit's first live run reports `FAIL` overall because 8 of 9 pages still carry legacy artefacts. This is **expected** and **intentional** — the audit's purpose is to surface those pages for a future re-render cycle, not to silently rewrite them.

## What is NOT in this release

- No auto-bulk republish. The audit is read-only.
- No re-render of the 8 failing pages. That is a future release (likely v0.2.11).
- No new UI features, no new reading modes, no new evidence labels.
