# Published Pages Regression Audit — 2026-06-15T22:43:49.172834Z

- **Status**: WARN
- **Site root**: https://conanxin.github.io/paper-reading-pages
- **Manifest URL**: https://conanxin.github.io/paper-reading-pages/published_pages.json
- **Pages total / checked**: 10 / 10
- **Pages PASS / WARN / FAIL**: 9 / 1 / 0
- **Issues**: error=0 warning=3 info=8

## Summary

PASS: all pages HTTP 200 and no error-level issues. WARN: all pages accessible but legacy-render warnings present. FAIL: at least one page has template leak / raw dict / old footer / HTTP non-200.

## Pages

| # | URL | Status | HTTP | Title | Issues |
|---|---|---|---|---|---|
| 1 | https://conanxin.github.io/paper-reading-pages/ | WARN | 200 | Paper Reading Pages — index | missing_claims_section, missing_glossary, missing_resolver_trail |
| 2 | https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/ | PASS | 200 | You and Your Research — 三遍阅读法 | — |
| 3 | https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/ | PASS | 200 | Attention Is All You Need — Three-Pass Reading | no_visible_claim_id |
| 4 | https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ | PASS | 200 | Attention Is All You Need — Three-Pass Reading | no_visible_claim_id |
| 5 | https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ | PASS | 200 | How to Read a Paper — Three-Pass Reading | no_visible_claim_id |
| 6 | https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ | PASS | 200 | How to Read a Paper — Three-Pass Reading | no_visible_claim_id |
| 7 | https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ | PASS | 200 | BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding | no_visible_claim_id |
| 8 | https://conanxin.github.io/paper-reading-pages/runner-title-attention/ | PASS | 200 | Attention Is All You Need — Three-Pass Reading | no_visible_claim_id |
| 9 | https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/ | PASS | 200 | AI-native Memory 2.0: Second Me — Three-Pass Reading | no_visible_claim_id |
| 10 | https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/ | PASS | 200 | Second Me: Human-Inspired Memory Mechanism for LLM Agents — 三遍阅读法 | no_visible_claim_id |

## Detailed issues

### https://conanxin.github.io/paper-reading-pages/

- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[warning]** `missing_claims_section` — 页面缺少 Claims / Evidence 区段。
  - 修复建议: 确认 paper_reading.json 含 claims_evidence_map,重新渲染。
- **[warning]** `missing_glossary` — 页面缺少 Glossary / 关键术语 区段。
  - 修复建议: 如果页面是 screenshot_only,可忽略;否则补 paper_reading.json 的 glossary 字段并重新渲染。

### https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/runner-title-attention/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/

- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

## Recommendations

- 1 页面缺 Resolver Trail — v0.2.8 之前渲染,建议在 v0.2.11+ 分批重渲染。
- 1 页面缺 Glossary — 检查 paper_reading.json 的 glossary 字段。
