# Published Pages Regression Audit — 2026-06-16T01:33:42.634522Z

- **Status**: PASS
- **Site root**: https://conanxin.github.io/paper-reading-pages
- **Manifest URL**: https://conanxin.github.io/paper-reading-pages/published_pages.json
- **Pages total / checked**: 11 / 11
- **Pages PASS / WARN / FAIL**: 11 / 0 / 0
- **Issues**: error=0 warning=0 info=9

## Summary

PASS: all pages HTTP 200 and no error-level issues. WARN: all pages accessible but legacy-render warnings present. FAIL: at least one page has template leak / raw dict / old footer / HTTP non-200.

## Page Type Summary

| Page type | Count |
|---|---|
| site_index | 1 |
| paper_page | 10 |
| manifest | 0 |
| unknown | 0 |

## Pages

| # | URL | Status | HTTP | Page type | Title | Issues |
|---|---|---|---|---|---|---|
| 1 | https://conanxin.github.io/paper-reading-pages/ | PASS | 200 | site_index | Paper Reading Pages — index | — |
| 2 | https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/ | PASS | 200 | paper_page | Attention Is All You Need — Three-Pass Reading | no_visible_claim_id |
| 3 | https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ | PASS | 200 | paper_page | Attention Is All You Need — Three-Pass Reading | no_visible_claim_id |
| 4 | https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ | PASS | 200 | paper_page | How to Read a Paper — Three-Pass Reading | no_visible_claim_id |
| 5 | https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ | PASS | 200 | paper_page | How to Read a Paper — Three-Pass Reading | no_visible_claim_id |
| 6 | https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ | PASS | 200 | paper_page | BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding | no_visible_claim_id |
| 7 | https://conanxin.github.io/paper-reading-pages/runner-title-attention/ | PASS | 200 | paper_page | Attention Is All You Need — Three-Pass Reading | no_visible_claim_id |
| 8 | https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/ | PASS | 200 | paper_page | AI-native Memory 2.0: Second Me — Three-Pass Reading | no_visible_claim_id |
| 9 | https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/ | PASS | 200 | paper_page | Second Me: Human-Inspired Memory Mechanism for LLM Agents — 三遍阅读法 | no_visible_claim_id |
| 10 | https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/ | PASS | 200 | paper_page | You and Your Research — 三遍阅读法 | — |
| 11 | https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-smoke-cn/ | PASS | 200 | paper_page | You and Your Research — 三遍阅读法 | no_visible_claim_id |

## Detailed issues

### https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/runner-title-attention/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-smoke-cn/

- **Page type**: paper_page
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

## Recommendations

- Root index is treated as site_index and exempted from paper-page checks (missing_resolver_trail / missing_claims_section / missing_glossary skipped by design).
