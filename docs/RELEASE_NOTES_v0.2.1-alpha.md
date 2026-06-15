# Release notes — paper-three-pass-reader v0.2.1-alpha

> Released: 2026-06-15.
> Tag: `v0.2.1-alpha` (annotated).
> Compatibility: drop-in over v0.2.0-alpha. No schema breaking changes.

## Headline

This release makes the runner output directly usable by another agent (or a human). Two new flags turn a draft into a guided workflow:

- **`--fill-pack`** — writes an Agent Fill Pack (11 markdown files + 3 JSON) to `<run_dir>/fill-pack/`. Each step file is a self-contained task with goal, allowed inputs, forbidden actions, JSON fields to fill, evidence-label rules, output format, and stop condition. Weak-mode drafts get explicit "weak-input" caveats.
- **`--audit`** — runs `audit_paper_reading.py` after the draft is written. The audit is structural + reading-mode discipline only (JSON shape, enum validity, evidence-label whitelist, no over-claims in `abstract_only` / `screenshot_only`). Output is `work/audit_result.json` + `reports/audit_summary.md`. If status is FAIL, the runner refuses to render or publish (use `--audit-warn-only` to relax).

## New flags

```text
--fill-pack           # write Agent Fill Pack
--audit               # run audit after draft
--audit-warn-only     # treat WARN as PASS for render/publish gating
--agent-profile       # default | strict | beginner | researcher | engineer
--language            # zh-CN | en
--max-claims          # max claims in fill-pack (default 8)
--max-figures         # max figure entries in fill-pack (default 6)
```

## What's in the fill pack

```
fill-pack/
├── 00_README.md                  # overview, doable / not doable, commands
├── 01_stage0_intake_resolution.md
├── 02_pass1_five_cs.md
├── 03_pass2_main_ideas.md
├── 04_claims_evidence_map.md     # strictest discipline step
├── 05_figures_tables.md
├── 06_pass3_reconstruction.md
├── 07_critical_review.md
├── 08_reproduction_plan.md
├── 09_finalize_json.md
├── 10_quality_gate.md
├── prompts.json                  # machine-readable prompts (zh-CN / en)
├── field_checklist.json          # per-field status: present | draft | missing | unavailable_due_to_reading_mode
└── draft_status.json             # aggregate counts + recommended_next_action
```

## What the audit checks

1. JSON shape — all top-level required keys present.
2. Enum validity — `reading_mode`, `input_kind`, `evidence_label` ∈ whitelist.
3. Reading-mode discipline — `screenshot_only` must declare body-related missing fields; `full_text` should not have `[DRAFT]` placeholders; weak-mode claims should not use `[Paper evidence]` / `[Figure/Table evidence]`.
4. Claims-Evidence Map — every claim has a valid label; `full_text` requires ≥ 5 claims.
5. Final checklist — ≥ 5 questions; `full_text` recommends ≥ 8.

The audit does **not** check whether the paper's content is correct.

## Combined example

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug fillpack-title-attention \
  --output-root runs/fill-pack-smoke-20260615 \
  --reading-mode partial_text \
  --fill-pack --audit --audit-warn-only --render
```

Smoke runs from validation are in `runs/fill-pack-smoke-20260615/`:

- `fillpack-title-attention/`
- `fillpack-abstract-keshav/`
- `fillpack-screenshot-keshav/`

## Upgrade path: weak → full

1. Place body text in `runs/<root>/<slug>/extracted/full_body.txt`.
2. Re-run the runner with `--reading-mode full_text`.
3. Re-run audit. Claims can now carry `[Paper evidence]` / `[Figure/Table evidence]`.
4. Re-render + (optionally) re-publish.

## Validation

`scripts/validate.sh` extended to **108/0 PASS** across 9 steps. New step 9 covers:

- Runner advertises all 7 new flags.
- Audit script + fill-pack writer exist and are executable.
- Title-only fill-pack run produces all 17 expected files + audit PASS.
- Abstract-only fill-pack run: page shows `abstract_only`; audit does NOT mark FAIL.
- Screenshot-only fill-pack run: page shows `screenshot_only`; `intake_quality.missing_fields` mentions body parts.
- Existing Attention real run still passes audit.

## Limitations

- The runner still does not auto-extract PDF body. The operator must supply body text manually for `full_text` mode.
- The audit is structural only. It catches discipline violations, not content errors.
- The fill-pack writer is locale-aware (`zh-CN` / `en`) but per-step text is largely identical across `--agent-profile` values in v0.2.1-alpha. Future versions may branch on profile.

## Diff vs v0.2.0-alpha

- New: `audit_paper_reading.py`, `fill_pack_writer.py`, `AGENT_FILL_PACK.md`, `AUDIT.md`.
- Modified: `run_paper_reading.py` (5 new flags + audit + fill-pack integration), `validate.sh` (9th step), `RUNNER.md` / `USAGE.md` / `OUTPUT_SCHEMA.md` / `README.md` / `README.zh-CN.md` / `CHANGELOG.md`.
- Tag: `v0.2.1-alpha` (annotated, fresh — not a move of `v0.2.0-alpha`).
