# zh-CN Quality Gate — paper-three-pass-reader (v0.2.4-alpha)

## What problem it solves

`audit_paper_reading.py` (v0.2.1+) checks **JSON shape and reading-mode discipline**. It does NOT judge whether the paper-reading explanation is actually a reading. In v0.2.3 we added a 50% CJK coverage check on 5 fields, but it can be gamed:

- A field that has one Chinese character followed by a long English paragraph passes the CJK check.
- A glossary with all-English definitions passes the CJK check.
- A 2-item final checklist with "yes" answers passes any completeness check.
- A full_text draft with all `[Author claim]` claims (no `[Paper evidence]`) is suspicious but structurally valid.

The **zh-CN quality gate** is a second-line check that catches these specific failure modes.

## What it is

A new stdlib-only script: `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`. It runs after the structural audit and reports its own PASS / WARN / FAIL.

It is **not** an LLM truth judgment. It is **not** a translation-quality scorer. It is a **structural + bilingual-discipline** gate.

## What it checks

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

## Usage

Standalone:

```bash
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/myrun/work/paper_reading.json \
  --json-output runs/myrun/work/quality_gate_zh_cn.json
```

Via the runner:

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "..." --input-kind paper_title --slug <slug> --output-root <root> \
  --language zh-CN --fill-pack --quality-gate
```

When the runner uses `--quality-gate`, it:

1. Runs the audit (if `--audit`).
2. Runs the quality gate (writes `work/quality_gate_zh_cn.json` + `reports/quality_gate_zh_cn.md`).
3. If the quality gate is FAIL and `--audit-warn-only` is NOT set, blocks `--render` and `--publish`.

Via the audit:

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/myrun/work/paper_reading.json \
  --quality-gate
```

When the audit uses `--quality-gate` and the draft is `zh-CN`, it runs the quality gate after the structural audit and exits non-zero on quality-gate FAIL.

Without `--quality-gate`, the audit prints a hint at the bottom of its output:

> `[hint] target_language/ui_language = zh-CN. Re-run with --quality-gate to invoke skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py.`

## How to fix common failures

| Failure | Fix |
| --- | --- |
| CJK coverage < 50% | Translate English explanations to Chinese. Keep English terms on first occurrence with Chinese gloss. |
| Long English blob in a field | That field is direct English carryover. Translate it. |
| glossary < 10 | Add terms. Each term should have a Chinese definition. |
| claims < 8 | Add claims. In full_text mode, at least one should be `[Paper evidence]` with an `evidence_location` (e.g. `§2.1`, `p.5`, `Table 1`). |
| final_checklist < 8 | Add checklist items; write questions in Chinese. |
| full_text all `[Author claim]` | Mark at least one core claim as `[Paper evidence]` with a specific `evidence_location` referencing a paper section. |
| Pass 2 / Pass 3 empty | Re-walk steps 03-07 of the fill-pack. First fill `main_ideas`, then `method_reconstruction`. |

## Why evidence labels stay in English

Evidence labels (`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`) are **fixed English enums** that the audit and quality gate both parse literally. Translating them would break the audit's enum check and the quality gate's label-distribution check. So:

- **Labels are always in English.**
- **Text around the labels** (`notes`, `comment`, `claim_text`) is in the chosen language.
- Paper titles, method names, benchmark names, author names stay in the form the author wrote them.

## Why "has CJK chars" alone is not enough

A 1-character-CJK field with a 200-character English paragraph passes the CJK check. So the gate also checks:

- **Structural depth** — claims, glossary, checklist, pass 2/3.
- **Evidence discipline** — `[Paper evidence]` claims must exist for a real reading.
- **Carryover detection** — long English blobs without CJK are flagged.

The gate is intentionally conservative. False positives (a long English blob that is actually a method name) are acceptable; false negatives (passing an English carryover) are not.

## Thresholds for weak modes

The defaults (8 claims, 10 glossary, 8 checklist, 50% CJK) are tuned for **full_text** real-paper readings. For **abstract_only / partial_text / screenshot_only** drafts, the structural audit already disallows Pass 2/3 in those modes, and the quality gate should be run with `--warn-only` (or not at all). The flag is documented:

```bash
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/weak-myrun/work/paper_reading.json \
  --warn-only
```

In `--warn-only` mode, FAIL still exits non-zero but WARN does not.

## Customizing thresholds

```bash
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/myrun/work/paper_reading.json \
  --min-cjk-ratio 0.4 \
  --min-claims 5 \
  --min-glossary 6 \
  --min-checklist 5
```

These are useful for short papers, position papers, or non-research blog-style inputs.

## See also

- [`docs/ZH_CN_QUALITY_GATE.md`](../../docs/ZH_CN_QUALITY_GATE.md) — the original doc was at this path; this file mirrors it.
- The fill-pack step `11_zh_cn_quality_gate.md` explains the same rules to the agent.
- The runner / audit / renderer code: `run_paper_reading.py` (search `--quality-gate`), `audit_paper_reading.py` (search `--quality-gate`), `quality_gate_zh_cn.py`.

## v0.2.5 — `p3pr` one-line CLI integration

The CLI (`p3pr.py` at `skills/paper-three-pass-reader/scripts/p3pr.py`) wraps the runner + audit + quality gate + render + publish. It enables / disables the quality gate based on:

- `--language zh-CN` (default) → quality gate runs
- `--language en` → quality gate is silently skipped
- `--no-quality-gate` → never runs the quality gate
- `--publish` + quality-gate FAIL → BLOCKED (CLI prints `P3PR_STATUS: BLOCKED`)
- `--publish` + `--allow-draft-publish` + quality-gate FAIL → publishes anyway (status `WARN`)

When the CLI's quality gate is the failure, the printed `P3PR_NEXT_ACTION` is the recipe from this doc's "How to fix common failures" table.
