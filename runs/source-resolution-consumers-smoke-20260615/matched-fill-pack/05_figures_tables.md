# 05. Figures and Tables

## Goal

For each key figure / table, write an explanation entry.

## Allowed materials

- Weak mode: figure/table numbers and titles from abstract.
- Full-text mode: actual figures / tables.

## Forbidden

- Don't explain a figure you didn't see.
- Weak mode: [Figure/Table evidence] is NOT allowed — use [Author claim] / [Needs verification].

## JSON fields to fill

- `figures_tables[*].id`
- `figures_tables[*].kind`
- `figures_tables[*].label`
- `figures_tables[*].explanation`
- `figures_tables[*].evidence_label`

## Evidence label rules

Valid evidence labels per the whitelist. Weak mode: 0-6 entries, each with a label in {[Author claim], [Needs verification], [Uncertain]}.

## Output format

≤ 6 entries in weak mode; matches actual figure count in full_text.

## Stop condition

Each entry has a label in the whitelist.
