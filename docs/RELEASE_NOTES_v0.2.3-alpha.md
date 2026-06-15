# Release Notes — v0.2.3-alpha

## Overview

Adds **first-class Chinese (zh-CN) output support** to the entire pipeline. The runner, fill-pack, audit, renderer, and validation now all carry language fields. Pages can now be produced in Chinese with a localized UI while keeping evidence labels and paper names in their original form.

## Changes

### Runner (`run_paper_reading.py`)

- `make_draft` now writes `target_language` and `ui_language` at the top of the draft JSON (after `schema_version`).
- Both default to whatever `--language` was passed (default `zh-CN`).

### Renderer (`render_page.py`)

- `render_index` reads `ui_language` from the JSON.
- When `ui_language = "zh-CN"`, a deterministic English→Chinese UI label map is applied to the rendered HTML.
- The map covers: section headings, key terms, evidence labels (preserved in English), tabs, accordions, all metadata labels — 60+ mappings total.
- Backward compatible: when `ui_language` is absent or `"en"`, the renderer produces an English page (no behavioural change).

### Audit (`audit_paper_reading.py`)

- Added step 8 (language check).
- When `target_language` or `ui_language` is `zh-CN`, scans 5 main interpretive fields and warns if fewer than 50% contain CJK characters (U+4E00–U+9FFF).
- Does NOT flag evidence labels, paper titles, method names, or author names.
- The check is a WARN, not a FAIL. Does not change PASS/WARN/FAIL semantics for `en` drafts.

### Validation (`scripts/validate.sh`)

- New step 10 with 12 zh-CN checks.
- Total: 120/0 PASS (was 108/0).

### Second Me Chinese full-text run

- `runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/`
- 12 claims, 7 figure/table entries, 14 glossary terms, 12-item checklist.
- Audit: PASS, 0 errors / 0 warnings / 0 recommendations.
- Page: https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/

### Documentation

- `README.md` — new "Language support (zh-CN / en)" section + version table updated.
- `CHANGELOG.md` — v0.2.3-alpha entry.
- `skills/paper-three-pass-reader/docs/RUNNER.md` — v0.2.3 language output section.
- `skills/paper-three-pass-reader/docs/USAGE.md` — Chinese page generation example.
- `skills/paper-three-pass-reader/docs/AUDIT.md` — language check documentation.
- `skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md` — language-aware fill pack docs.
- `docs/AUTOFILL_RUNS.md` — P3PR-V0.2.3-ZH-CN-OUTPUT entry.
- `docs/REALPAPER_RUNS.md` — pointer to the new run.
- `docs/PHASE_P3PR_V0_2_3_ZH_CN_OUTPUT_REPORT.md` — full phase report.

## Design notes

- **Evidence labels are not translated.** They are fixed English enums that the audit parses literally. Translating them would break the audit's enum check.
- **Paper titles, method names, benchmark names, and author names stay in their original form.** This is intentional — the paper is what the author wrote, and we should not localize an arXiv title to a different language than the one the author used.
- **The default language is `zh-CN`.** The project's home user is Chinese-first. Set `--language en` to revert to the v0.2.2 behaviour.
- **Backward compatible.** Existing `en` drafts from v0.2.1 / v0.2.2 still render in English with no changes. The renderer only switches when the JSON explicitly says `ui_language = "zh-CN"`.

## Validation

- `scripts/validate.sh`: **120/0 PASS** (was 108/0).
- New checks: runner `--language` flag, zh-CN draft language fields, Chinese fill-pack content, Chinese UI label presence, audit Chinese-content warning, Second Me zh-CN real run audit, Second Me zh-CN page label check.

## Migration guide

Existing drafts (no `ui_language` field) continue to render in English. To upgrade:

1. **For new runs**: pass `--language zh-CN` to the runner.
2. **For existing JSON**: add `target_language` and `ui_language` to the top level and re-render. The UI will switch, but explanatory content stays in its original language.
3. **For a real Chinese reading**: re-run with `--language zh-CN` and re-fill the draft, then re-render. This is the recommended path.

## Artifacts

- Skill repo: `conanxin/openclaw-paper-three-pass-reader-skill`
- Tag: `v0.2.3-alpha`
- Commit: see git log post-commit
- Chinese page: https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/
- English page (preserved): https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/
- Release: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.3-alpha
