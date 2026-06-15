# Audit — paper-three-pass-reader (v0.2.1-alpha)

> New in v0.2.1-alpha. `audit_paper_reading.py` is a structural + reading-mode
> discipline check. It is **not** a truth judgment about the paper.

## What the audit checks

1. **JSON shape** — Top-level required keys (`schema_version`, `paper_metadata`, `intake_quality`, `summaries`, `five_cs`, `pass1`, `pass2`, `pass3`, `claims_evidence_map`, `figures_tables`, `glossary`, `limitations`, `reproduction_plan`, `open_questions`, `final_checklist`).
2. **Enum validity** — `reading_mode` ∈ {`full_text`, `partial_text`, `abstract_only`, `screenshot_only`}. `input_kind` ∈ the 11 valid kinds. `evidence_label` ∈ the 6 valid labels.
3. **Reading-mode discipline** — In `abstract_only` / `screenshot_only`:
   - `pass2.method_summary` and `pass3.method_reconstruction` should not be filled with non-DRAFT content (they are warns, not errors, to avoid false positives when the operator legitimately filled them from the abstract).
   - `screenshot_only` must have body-related entries (`full body`, `references`, `figures`, or `tables`) in `intake_quality.missing_fields`.
4. **full_text completeness** — When `reading_mode = full_text`, no `[DRAFT]` placeholders should remain in `pass1` / `pass2` / `pass3` (warn-level).
5. **Claims-Evidence Map** — Each claim has `evidence_label` ∈ whitelist. `full_text` requires ≥ 5 claims. `abstract_only` / `screenshot_only` prefer `[Author claim]` / `[Uncertain]` / `[Needs verification]`.
6. **Final checklist** — At least 5 questions. `full_text` recommends ≥ 8.
7. **Draft placeholder count** — Reported as a recommendation, not an error (fresh runner drafts always have many).

## What the audit does NOT check

- Whether the paper's claims are true.
- Whether `correctness` is actually correct.
- Whether the `reproduction_plan` would actually reproduce the paper.
- Whether the `category` is the right category.
- Anything about figure / table content quality.

These are operator responsibilities. The audit is a structural discipline tool, not a paper reviewer.

## Usage

### Standalone

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/<root>/<slug>/work/paper_reading.json
```

Exit codes:
- `0` — PASS or WARN (depending on `--warn-only`).
- `1` — FAIL.
- `2` — Usage error (file not found, JSON parse failure).

### With JSON output

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/<root>/<slug>/work/paper_reading.json \
  --json-output runs/<root>/<slug>/work/audit_result.json
```

Output JSON shape:

```json
{
  "status": "PASS|WARN|FAIL",
  "reading_mode": "...",
  "input_kind": "...",
  "schema_version": "...",
  "counts": {
    "claims_total": ...,
    "claims_with_valid_evidence": ...,
    "final_checklist_questions": ...,
    "draft_placeholders": ...
  },
  "errors": [...],
  "warnings": [...],
  "recommendations": [...]
}
```

### From the runner

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug myrun \
  --output-root runs/ \
  --audit --render
```

The runner writes:
- `runs/<root>/<slug>/work/audit_result.json` — full audit JSON.
- `runs/<root>/<slug>/reports/audit_summary.md` — markdown summary.

If `--audit` is set and audit status is FAIL, the runner **refuses to render or publish** unless `--audit-warn-only` is set.

## Evidence label whitelist

Only these labels are valid:

- `[Paper evidence]` — body text directly supports.
- `[Figure/Table evidence]` — figure or table in paper directly supports.
- `[Author claim]` — author asserted in abstract / conclusion.
- `[Agent inference]` — derived by the reader / agent.
- `[Uncertain]` — cannot determine.
- `[Needs verification]` — must be checked against the body.

> Any other label (typo, ad-hoc tag) is treated as an error.

## Reading-mode × evidence-label matrix

| Reading mode | `[Paper evidence]` | `[Figure/Table evidence]` | `[Author claim]` | `[Agent inference]` | `[Uncertain]` | `[Needs verification]` |
| --- | --- | --- | --- | --- | --- | --- |
| `full_text` | OK | OK | OK | OK | OK | OK |
| `partial_text` | warn if no section | warn if no figure | OK | OK | OK | OK |
| `abstract_only` | NOT available | NOT available | preferred | OK | OK | OK |
| `screenshot_only` | NOT available | NOT available | preferred | OK | OK | OK |

> "NOT available" = the audit warns if you use this label in a weak mode. The operator must downgrade to `[Author claim]` / `[Uncertain]` / `[Needs verification]`.

## Common audit failures and fixes

| Failure | Cause | Fix |
| --- | --- | --- |
| `claims_evidence_map` has invalid label | Typo like `[paper evidence]` (lowercase) | Match the whitelist exactly. |
| `reading_mode = full_text` but `< 5 claims` | Not enough claims extracted | Add more claims; full readings usually have ≥ 5. |
| `screenshot_only` but missing body hints | `intake_quality.missing_fields` doesn't mention body parts | Add one of: `full body`, `references`, `figures`, `tables`. |
| `reading_mode = abstract_only` claims use `[Paper evidence]` | Over-claim | Downgrade to `[Author claim]` / `[Needs verification]`. |
| `final_checklist` < 5 questions | Incomplete checklist | Add at least 5 questions; full_text prefers ≥ 8. |
| `[DRAFT]` placeholders in full_text mode | Runner draft not edited | Fill in the pass content. |

## Limitations

- The audit does not validate `glossary` / `open_questions` content. It only requires they be present.
- It does not check whether the agent used the fill pack; the fill pack is advisory.
- It does not check that the page was actually rendered or published.

## Related

- `AGENT_FILL_PACK.md` — how the runner generates the fill pack.
- `OUTPUT_SCHEMA.md` — JSON shape contract.
- `DESIGN_RATIONALE.md` — why reading-mode discipline matters.

## v0.2.3 — Language check

When the draft declares `target_language` or `ui_language` as `zh-CN`, the audit adds a content check:

1. Scans 5 main interpretive fields:
   - `summaries.one_sentence`
   - `pass2.main_ideas` (joined)
   - `pass3.method_reconstruction` (joined)
   - `pass3.critical_review` (joined)
   - `glossary` (joined `definition` field of each entry)
2. Counts how many of those fields contain at least one CJK character (U+4E00–U+9FFF).
3. If fewer than 50% contain CJK, emits a **WARN**:
   > `target_language/ui_language = zh-CN but fewer than 50% of main interpretive fields contain Chinese characters (X/Y). ...`

The check intentionally does **not** flag:
- English evidence labels (`[Paper evidence]`, etc.)
- Paper titles, method names, benchmark names
- Author names

The check is a **WARN**, not a FAIL. The audit's PASS/WARN/FAIL semantics for `en` drafts are unchanged.

To verify: a fresh `paper_reading.json` with `--language zh-CN` and no manual filling should trigger the warning.

## v0.2.4 — `--quality-gate` integration

The audit gained a `--quality-gate` flag. When set on a `zh-CN` draft, the audit invokes `quality_gate_zh_cn.py` after the structural audit. The combined behaviour:

- **Without `--quality-gate`** on a `zh-CN` draft, the audit prints a hint:
  > `[hint] target_language/ui_language = zh-CN. Re-run with --quality-gate to invoke skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py.`
- **With `--quality-gate`**, the audit:
  1. Runs the structural audit (unchanged).
  2. Runs the quality gate.
  3. Writes `quality_gate_zh_cn.json` next to the audit JSON.
  4. Exits non-zero on structural-audit FAIL OR quality-gate FAIL.

The structural audit and quality gate are independent — both can run, both can pass, both can fail. The combined exit code is the OR of the two.

When the draft is `en`, the `--quality-gate` flag is silently ignored.


## Cross-links

- Source resolution: see [`SOURCE_RESOLUTION.md`](SOURCE_RESOLUTION.md) for the canonical top-level `source_resolution` object and the legacy `intake_quality.source_resolution` list.
- Resolver trail in the rendered page, audit, fill-pack checklist, and zh-CN quality-gate check all consume that same object.
