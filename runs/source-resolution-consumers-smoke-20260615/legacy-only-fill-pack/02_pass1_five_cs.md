# 02. Pass 1 — Five Cs

## Goal

Write Five Cs: Category / Context / Correctness / Contributions / Clarity.

## Allowed materials

- Abstract (if present).
- Title + authors + venue + field.
- If `reading_mode == full_text`, introduction / conclusion are allowed.

## Forbidden

- Don't claim 'all experiments are correct' unless you actually checked the experimental section.
- Don't take an author's abstract claim as verified contribution.
- Don't write 'this is the first paper to propose X' without checking references.

## JSON fields to fill

- `five_cs.category`
- `five_cs.context`
- `five_cs.correctness`
- `five_cs.contributions`
- `five_cs.clarity`

## Evidence label rules

Weak mode defaults: category/context → [Author claim]; correctness/clarity → [Needs verification].
Full-text defaults: paper_text → [Paper evidence]; inferences → [Agent inference].

## Output format

All five fields non-empty; correctness and clarity carry an evidence label.

## Stop condition

All five fields filled with at least one sentence each.
