# 09. Finalize JSON

## Goal

Audit the whole JSON before render / publish.

## Allowed materials

- work/paper_reading.json
- audit_result.json (previous run).

## Forbidden

- Don't publish a draft that still has [DRAFT] in stages that should be filled.

## JSON fields to fill

- `All [DRAFT] placeholders (except legitimate weak-mode Pass 2/3 ones) replaced.`
- `paper_metadata.reading_mode matches reality.`
- `intake_quality.needs_confirmation = false unless there's a real ambiguity.`
- `claims_evidence_map every claim has evidence_label in whitelist.`
- `Weak mode has no [Paper evidence] / [Figure/Table evidence] labels.`
- `final_checklist: ≥ 5 questions; full_text ≥ 8.`
- `glossary: ≥ 3 terms (unless domain is unusual).`

## Evidence label rules

Standard checklist.

## Output format

Run audit, see status PASS.

## Stop condition

audit status = PASS.
