# 03. Pass 2 — Main Ideas

## Goal

Write the paper's main ideas (3-5 max) and the core mechanism of the method.

## Allowed materials

- Abstract (required).
- Introduction / conclusion / figures (only if full_text).
- > **Weak-input note**: `reading_mode = abstract_only`. Pass 2 main ideas can only use the abstract range. Do NOT write 'we read Section 3.2 and found X'. If the abstract does not name the idea, leave `[DRAFT]` and explain in `notes`.

## Forbidden

- Don't fabricate method details. If the abstract doesn't say, leave `[DRAFT]`.
- Don't treat author future work as main ideas.

## JSON fields to fill

- `pass2.main_ideas`
- `pass2.method_summary`

## Evidence label rules

weak → [Author claim]; full_text → [Paper evidence] + section number.

## Output format

main_ideas length >= 1; method_summary length >= 30 chars.

## Stop condition

Both fields non-empty.
