# PHASE P3PR-V0.2.4-ZH_CN-QUALITY-GATE-REPORT

> Generated 2026-06-15.
> Scope: add a dedicated zh-CN quality gate that goes beyond "has Chinese?" to "is the Chinese actually a reading?".
> Goal: prevent the v0.2.3 zh-CN output from being a UI-flip or English carryover.

## STATUS

PASS

## PROJECT_DIR

/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill

## BASE_VERSION

v0.2.3-alpha

## TARGET_VERSION

v0.2.4-alpha

## PROBLEM

v0.2.3-alpha's audit had a 5-field CJK coverage check, but it can be gamed:

1. A field with one Chinese character followed by a long English paragraph passes the CJK check.
2. A glossary with all-English definitions passes the CJK check.
3. A 2-item final checklist with "yes" answers passes any completeness check.
4. A full_text draft with all `[Author claim]` claims is structurally valid but suspicious.
5. A draft where the operator copy-pasted English passages from the English version would pass structurally.

There was no second-line check that catches these specific failure modes.

## FIX_SUMMARY

Added a new `quality_gate_zh_cn.py` script that:

- Scans 75+ interpretive fields for CJK coverage (50% threshold).
- Detects "long English blobs" (≥ 30 ASCII chars, no CJK) within a single field — the English carryover signal.
- Validates glossary / claims / final_checklist minimum counts.
- Validates `evidence_label` enum + distribution (full_text mode requires ≥ 1 `[Paper evidence]`).
- Validates Pass 2 / Pass 3 presence in full_text mode.
- Validates summary shape (one_sentence / three_sentence / ten_sentence non-empty).

Integrated into the audit (`--quality-gate` flag) and the runner (`--quality-gate` flag). Added a new fill-pack step (`11_zh_cn_quality_gate.md`) that explains the gate to the agent.

A bad sample (`runs/quality-gate-smoke-20260615/bad-zh-cn-draft/`) demonstrates the FAIL path.

## QUALITY_GATE_SCRIPT

- Path: `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`
- Stdlib-only. CLI: `python3 quality_gate_zh_cn.py --input <paper_reading.json> --json-output <out.json>`
- Optional flags: `--warn-only`, `--min-cjk-ratio` (0.5), `--min-claims` (8), `--min-glossary` (10), `--min-checklist` (8).
- Output: human-readable summary + JSON report.
- Exit codes: 0 on PASS / WARN (under --warn-only), 1 on FAIL, 2 on usage/IO error.

JSON output shape:

```json
{
  "status": "PASS|WARN|FAIL",
  "target_language": "zh-CN",
  "ui_language": "zh-CN",
  "reading_mode": "full_text",
  "cjk_coverage": {
    "checked_fields": 75,
    "fields_with_cjk": 75,
    "ratio": 1.0,
    "long_english_paragraphs": 0
  },
  "counts": {
    "claims": 12,
    "glossary_terms": 14,
    "checklist_items": 12
  },
  "evidence_label_distribution": {
    "[Paper evidence]": 9,
    "[Author claim]": 3
  },
  "errors": [],
  "warnings": [],
  "recommendations": []
}
```

## AUDIT_INTEGRATION

`audit_paper_reading.py` gained:

- New flag: `--quality-gate`.
- When set on a `zh-CN` draft, the audit calls `quality_gate_zh_cn.py` after the structural audit.
- Writes `quality_gate_zh_cn.json` next to the audit JSON.
- Exits non-zero on combined FAIL.
- When NOT set on a `zh-CN` draft, prints a hint:
  > `[hint] target_language/ui_language = zh-CN. Re-run with --quality-gate to invoke skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py.`

Verified: `audit_paper_reading.py --quality-gate --input <second-me-zh-cn>` returns status PASS and exit code 0. `audit_paper_reading.py --quality-gate --input <bad-sample>` returns FAIL and exit code 1.

## RUNNER_INTEGRATION

`run_paper_reading.py` gained:

- New flag: `--quality-gate`.
- When set and `--language == zh-CN`, runs `quality_gate_zh_cn.py` after the audit.
- Writes `work/quality_gate_zh_cn.json` + `reports/quality_gate_zh_cn.md`.
- Quality-gate FAIL blocks `--render` and `--publish` unless `--audit-warn-only` is set.
- For non-zh-CN runs, the flag is silently ignored.

Verified with smoke run: `run_paper_reading.py --language zh-CN --fill-pack --quality-gate` writes the quality gate artifacts and the runner summary line.

## FILL_PACK_UPDATE

`fill_pack_writer.py` now generates `11_zh_cn_quality_gate.md` in the fill-pack directory. The new file:

- Explains what the quality gate checks.
- Has a fix-table for common FAILs.
- Explains why evidence labels stay in English.
- Explains why "has CJK chars" is not enough (lists 5 specific failure modes that pass a naive check).
- Lists re-render / re-publish commands.

The new step is also referenced in the fill-pack `00_README.md` step list.

## SECONDME_ZH_CN_GATE_RESULT

```
$ python3 quality_gate_zh_cn.py --input runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/paper_reading.json
Quality gate status: PASS
target_language = 'zh-CN', ui_language = 'zh-CN', reading_mode = 'full_text'
CJK coverage: 75/75 (1.00); long_en_blobs = 0
Counts: claims=12, glossary_terms=14, checklist_items=12
Evidence labels: [Paper evidence]=9, [Author claim]=3
```

## BAD_SAMPLE_RESULT

```
$ python3 quality_gate_zh_cn.py --input runs/quality-gate-smoke-20260615/bad-zh-cn-draft/work/paper_reading.json
Quality gate status: FAIL
target_language = 'zh-CN', ui_language = 'zh-CN', reading_mode = 'full_text'
CJK coverage: 0/16 (0.00); long_en_blobs = 5
Counts: claims=2, glossary_terms=0, checklist_items=2
Evidence labels: [Needs verification]=1, [Author claim]=1

Errors (4):
  - CJK coverage on interpretive fields is 0.00 (0/16); minimum is 0.50.
  - glossary has 0 entries; minimum is 10.
  - claims_evidence_map has 2 entries; minimum is 8.
  - final_checklist has 2 items; minimum is 8.

Warnings (4):
  - Found 5 interpretive field(s) with a long English blob (>=30 ASCII chars without CJK).
  - reading_mode = full_text but no claim uses [Paper evidence] or [Figure/Table evidence].
  - Only 0/2 claims have Chinese in claim_text or comment.
  - Only 0/2 final_checklist questions are in Chinese.
```

Exit code: 1.

## VALIDATION

`scripts/validate.sh`: **129/0 PASS** (was 120/0). The 9 new checks under step 11 cover:

- quality_gate_zh_cn.py --help
- quality_gate_zh_cn.py executable
- Second Me zh-CN quality gate PASS
- Bad zh-CN sample quality gate FAIL
- runner --help mentions --quality-gate
- audit --help mentions --quality-gate
- zh-CN fill-pack contains 11_zh_cn_quality_gate.md
- audit --quality-gate integration PASS on Second Me zh-CN
- audit default --quality-gate hint on zh-CN run

## FILES_CREATED

- `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py` (the gate script)
- `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md` (full doc)
- `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/work/paper_reading.json` (bad sample)
- `runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/quality_gate_zh_cn.json` (PASS report)
- `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/work/quality_gate_zh_cn.json` (FAIL report)
- `docs/RELEASE_NOTES_v0.2.4-alpha.md`
- `docs/PHASE_P3PR_V0_2_4_ZH_CN_QUALITY_GATE_REPORT.md` (this file)

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/audit_paper_reading.py` — added `--quality-gate` flag and integration
- `skills/paper-three-pass-reader/scripts/run_paper_reading.py` — added `--quality-gate` flag and integration
- `skills/paper-three-pass-reader/scripts/fill_pack_writer.py` — added `11_zh_cn_quality_gate.md`
- `scripts/validate.sh` — added step 11 with 9 new checks
- `README.md` — version table + zh-CN quality gate section
- `CHANGELOG.md` — v0.2.4-alpha entry
- `skills/paper-three-pass-reader/docs/RUNNER.md` — quality gate integration section
- `skills/paper-three-pass-reader/docs/AUDIT.md` — --quality-gate integration section
- `skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md` — 11_zh_cn_quality_gate.md description
- `skills/paper-three-pass-reader/docs/USAGE.md` — quality gate usage example
- `docs/AUTOFILL_RUNS.md` — P3PR-V0.2.4-ZH-CN-QUALITY-GATE entry
- `docs/REALPAPER_RUNS.md` — pointer to the new run

## COMMIT

See git log post-commit.

## PUSH

See git log post-commit.

## TAG

`v0.2.4-alpha` (annotated, pushed to origin).

## RELEASE

https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.4-alpha

## LIMITATIONS

- The quality gate is heuristic, not exhaustive. A determined operator could still pass with a low-quality Chinese reading by gaming specific thresholds.
- Long-English-blob detection is regex-based; unusual scripts (e.g. Cyrillic, Arabic) would not be detected as "long English" but also wouldn't be CJK.
- The default thresholds (8 / 10 / 8 / 50%) are tuned for full_text real-paper readings. For position papers, blog-style inputs, or weak-mode drafts, the thresholds may be too strict — use `--min-claims 5 --min-glossary 6 --min-checklist 5 --warn-only` instead.
- The CJK regex is U+4E00–U+9FFF, which covers the CJK Unified Ideographs basic block but not CJK Extension A/B/C/D/E/F. CJK-Vietnamese or rare CJK characters in glossaries might be missed. This is a known limitation; the gate is intended for Chinese-language use, not full CJK support.

## NEXT_USER_ACTION

- Review the Second Me Chinese run's quality gate report: `runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/quality_gate_zh_cn.json` (status PASS, 75/75 CJK).
- Review the bad sample's quality gate report: `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/work/quality_gate_zh_cn.json` (status FAIL, demonstrates the gate is not a rubber stamp).
- For any new zh-CN reading, re-run with `--quality-gate` to enforce the gate.
- Optionally lower thresholds for non-research inputs (`--min-claims 5 --min-glossary 6 --min-checklist 5`).
- The Chinese page (https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/) is preserved; no re-publish needed.
- The English page (https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/) is preserved; v0.2.4 only adds the quality gate for zh-CN.
- Old tags (v0.1.0/1/2, v0.2.0/1/2/3) are NOT moved.
