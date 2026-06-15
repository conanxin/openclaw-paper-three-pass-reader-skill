# 08. Reproduction Plan

## Goal

Write a minimal executable reproduction plan: data + baseline + hardware + steps + sanity checks + success criteria.

## Allowed materials

- Experimental section (full_text only).
- GitHub repo if any.
- Weak mode: dataset / metric names from abstract only.

## Forbidden

- Don't fabricate hyperparameters. If unknown, write 'unknown — verify from paper'.

## JSON fields to fill

- `reproduction_plan.dataset`
- `reproduction_plan.baseline`
- `reproduction_plan.steps`
- `reproduction_plan.sanity_checks`
- `reproduction_plan.success_criteria`

## Evidence label rules

Default label: [Author claim] for dataset/baseline; [Needs verification] for steps you haven't executed.

## Output format

full_text: dataset + baseline + steps all non-empty. weak: leave [DRAFT].

## Stop condition

All required fields present.
