# Release Notes — v0.2.4-alpha

## Overview

Adds a dedicated **zh-CN quality gate** that goes beyond "does this draft have Chinese?" to "is the Chinese explanation actually a reading?". The gate catches specific failure modes that the structural audit misses: English carryover, shallow glossary/claims/checklist, full_text mode with no `[Paper evidence]` claims, and missing Pass 2/3 in full_text mode.

## What changed

### New script: `quality_gate_zh_cn.py`

Stdlib-only Python script. Checks:

| Check | Default threshold | Failure mode |
| --- | --- | --- |
| `target_language == "zh-CN"` | required | FAIL |
| `ui_language == "zh-CN"` | required | WARN |
| CJK coverage on main interpretive fields | ≥ 50% | FAIL if below |
| Long English blobs (≥ 30 ASCII chars, no CJK) per field | 0 | WARN if any |
| Glossary entries | ≥ 10 | FAIL if below |
| Glossary definitions contain Chinese | all | WARN if any missing |
| Claims-Evidence map entries | ≥ 8 | FAIL if below |
| Evidence labels are valid enums | all | FAIL if any invalid |
| full_text: at least one `[Paper evidence]` or `[Figure/Table evidence]` | ≥ 1 | WARN if missing |
| full_text: not all claims are `[Author claim]` | not all | WARN if all |
| At least one of (claim_text, comment) contains Chinese | ≥ 50% | WARN if below |
| Final checklist items | ≥ 8 | FAIL if below |
| Final checklist questions are in Chinese | ≥ 50% | WARN if below |
| full_text: Pass 2 main_ideas non-empty | required | FAIL if empty |
| full_text: Pass 3 method_reconstruction non-empty | required | FAIL if empty |
| Summaries.one_sentence non-empty | required | FAIL if empty |
| Summaries.three_sentence has ≥ 1 non-empty item | required | FAIL if empty |
| Summaries.ten_sentence has ≥ 5 non-empty items | recommended | recommendation |

Output is a JSON report + human-readable summary. Exit code 0 on PASS or WARN (under `--warn-only`), 1 on FAIL.

### Audit `--quality-gate` integration

`audit_paper_reading.py --quality-gate` runs the quality gate after the structural audit on a `zh-CN` draft. Without the flag, the audit prints a hint to re-run with `--quality-gate`.

### Runner `--quality-gate` integration

`run_paper_reading.py --quality-gate` (only effective with `--language zh-CN`) runs the quality gate after the audit. Writes `work/quality_gate_zh_cn.json` and `reports/quality_gate_zh_cn.md`. Quality-gate FAIL blocks `--render` and `--publish` unless `--audit-warn-only` is set.

### Fill-pack `11_zh_cn_quality_gate.md`

New step in the agent fill pack explaining what the quality gate checks, how to fix common failures, and why "has CJK chars" is not enough.

### Bad zh-CN sample

`runs/quality-gate-smoke-20260615/bad-zh-cn-draft/` declares `target_language = zh-CN` but is all-English with empty glossary and 2-item checklist. The quality gate returns FAIL with 4 errors and 4 warnings. This guards against the quality gate becoming a rubber stamp.

### Validation extended

`scripts/validate.sh` now has 129 checks (was 120). New step 11 covers: quality-gate script help, executable, Second Me zh-CN PASS, bad sample FAIL, runner `--quality-gate` flag, audit `--quality-gate` flag, fill-pack `11_zh_cn_quality_gate.md` present, audit `--quality-gate` integration PASS, audit default hint on zh-CN run.

### Documentation

- New `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md`.
- Updated `README.md`, `CHANGELOG.md`, `skills/paper-three-pass-reader/docs/RUNNER.md`, `AUDIT.md`, `AGENT_FILL_PACK.md`, `USAGE.md`, `docs/AUTOFILL_RUNS.md`, `docs/REALPAPER_RUNS.md`.
- New `docs/RELEASE_NOTES_v0.2.4-alpha.md` (this file).
- New `docs/PHASE_P3PR_V0_2_4_ZH_CN_QUALITY_GATE_REPORT.md`.

## Design notes

- The quality gate is **structural + bilingual-discipline**, not LLM-truth-judging. It does not score translation quality subjectively.
- Evidence labels remain fixed English enums for audit compatibility. Explanatory text around them is Chinese.
- The default zh-CN thresholds (8 claims, 10 glossary, 8 checklist, 50% CJK ratio) are tuned for full_text real-paper readings, not weak-mode drafts. For weak-mode drafts, use `--warn-only` or skip the gate.
- The gate is intentionally conservative: false positives (flagging a long English blob that is actually a method name) are acceptable; false negatives (passing an English carryover) are not.

## Validation

- `scripts/validate.sh`: **129/0 PASS** (was 120/0).

## Migration guide

Existing `zh-CN` drafts from v0.2.3 will still pass audit. To take advantage of the quality gate, re-run with `--quality-gate` (via runner or audit) and fix any FAILs.

## Artifacts

- Skill repo: `conanxin/openclaw-paper-three-pass-reader-skill`
- Tag: `v0.2.4-alpha`
- Chinese page: https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/ (preserved from v0.2.3)
- Bad sample: `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/`
- Quality gate script: `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`
- Release: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.4-alpha
