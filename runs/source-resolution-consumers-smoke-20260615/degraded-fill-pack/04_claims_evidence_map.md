# 04. Claims → Evidence Map

## Goal

Write one claim-evidence entry for each important claim. Every claim must have an evidence_label.

## Allowed materials

- Abstract / introduction / experiments / figures / tables (per reading_mode).
- In weak mode: every number / metric / claim in the abstract is a candidate claim.

## Forbidden

- Don't relabel [Agent inference] as [Paper evidence].
- Don't write more than 8 claims in weak mode.
- Don't keep `C-DRAFT-xxx` IDs — replace them all.

## JSON fields to fill

- `claims_evidence_map[*].claim_id`
- `claims_evidence_map[*].claim_text`
- `claims_evidence_map[*].evidence_label`
- `claims_evidence_map[*].evidence_location`
- `claims_evidence_map[*].confidence`

## Evidence label rules

Valid labels: [Paper evidence], [Figure/Table evidence], [Author claim], [Agent inference], [Uncertain], [Needs verification].
Weak mode: [Paper evidence] and [Figure/Table evidence] are NOT available.

## Output format

full_text ≥ 5 claims; weak mode 1-8. All labels in whitelist.

## Stop condition

Every claim has a label and the audit confirms the whitelist.
