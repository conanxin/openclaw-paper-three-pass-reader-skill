# Quality Gate (zh-CN) — paper-three-pass-reader

- Status: **FAIL**
- target_language = 'zh-CN'
- ui_language = 'zh-CN'
- reading_mode = 'full_text'
- CJK coverage: 0/21 = 0.00
- counts: claims=1, glossary_terms=0, checklist_items=8

## Errors
- CJK coverage on interpretive fields is 0.00 (0/21); minimum is 0.50. Most explanatory content is still in English.
- glossary has 0 entries; minimum is 10.
- claims_evidence_map has 1 entries; minimum is 8.

## Warnings
- Found 7 interpretive field(s) with a long English blob (>=30 ASCII chars without CJK). Examples: ['claims_evidence_map[0].comment', 'final_checklist[0].question', 'final_checklist[1].question']. These may be carryover from the English draft that should be translated.
- Only 0/1 claims have Chinese in claim_text or comment.
- Only 0/8 final_checklist questions are in Chinese.
