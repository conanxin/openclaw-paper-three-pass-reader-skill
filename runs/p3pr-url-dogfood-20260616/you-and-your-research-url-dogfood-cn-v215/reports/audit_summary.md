# Audit summary for you-and-your-research-url-dogfood-cn-v215

- status: **FAIL**
- reading_mode: `full_text`
- input_kind: `paper_url`
- audit_json: `work/audit_result.json`

## Counts

- claims_total: 1
- claims_with_valid_evidence: 1
- final_checklist_questions: 8
- draft_placeholders: 39

## Errors

- reading_mode = full_text but claims_evidence_map has only 1 entries. full_text mode requires at least 5 claims.

## Warnings

- reading_mode = full_text but pass1 still contains [DRAFT] placeholders. The reading should be complete.
- reading_mode = full_text but pass2 still contains [DRAFT] placeholders. The reading should be complete.
- reading_mode = full_text but pass3 still contains [DRAFT] placeholders. The reading should be complete.
- target_language/ui_language = zh-CN but fewer than 50% of main interpretive fields contain Chinese characters (0/4). Fields checked: ['summaries.one_sentence', 'pass2.main_ideas', 'pass3.method_reconstruction', 'pass3.critical_review', 'glossary']. Ensure explanatory content is in Chinese; evidence labels and paper names may remain in English.

## Recommendations

- Document contains 39 [DRAFT] placeholders. These are normal for a freshly-generated runner draft; they should be replaced before the page is treated as a real reading.
