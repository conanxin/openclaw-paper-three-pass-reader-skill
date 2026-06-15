# Published Pages Regression Audit — 2026-06-15T15:05:11.027322Z

- **Status**: FAIL
- **Site root**: https://conanxin.github.io/paper-reading-pages
- **Manifest URL**: https://conanxin.github.io/paper-reading-pages/published_pages.json
- **Pages total / checked**: 10 / 10
- **Pages PASS / WARN / FAIL**: 1 / 1 / 8
- **Issues**: error=16 warning=10 info=15

## Summary

PASS: all pages HTTP 200 and no error-level issues. WARN: all pages accessible but legacy-render warnings present. FAIL: at least one page has template leak / raw dict / old footer / HTTP non-200.

## Pages

| # | URL | Status | HTTP | Title | Issues |
|---|---|---|---|---|---|
| 1 | https://conanxin.github.io/paper-reading-pages/ | WARN | 200 | Paper Reading Pages — index | missing_claims_section, missing_glossary, missing_resolver_trail |
| 2 | https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/ | FAIL | 200 | Attention Is All You Need — Three-Pass Reading | glossary_no_explicit_definition, missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 3 | https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/ | FAIL | 200 | Attention Is All You Need — Three-Pass Reading | glossary_no_explicit_definition, missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 4 | https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/ | FAIL | 200 | How to Read a Paper — Three-Pass Reading | glossary_no_explicit_definition, missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 5 | https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/ | FAIL | 200 | How to Read a Paper — Three-Pass Reading | glossary_no_explicit_definition, missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 6 | https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/ | FAIL | 200 | BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding | glossary_no_explicit_definition, missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 7 | https://conanxin.github.io/paper-reading-pages/runner-title-attention/ | FAIL | 200 | Attention Is All You Need — Three-Pass Reading | missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 8 | https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/ | FAIL | 200 | AI-native Memory 2.0: Second Me — Three-Pass Reading | glossary_no_explicit_definition, missing_resolver_trail, no_visible_claim_id, old_footer, template_leak |
| 9 | https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/ | FAIL | 200 | Second Me: Human-Inspired Memory Mechanism for LLM Agents — 三遍阅读法 | glossary_no_explicit_definition, no_visible_claim_id, old_footer, template_leak |
| 10 | https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/ | PASS | 200 | You and Your Research — 三遍阅读法 | — |

## Detailed issues

### https://conanxin.github.io/paper-reading-pages/

- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[warning]** `missing_claims_section` — 页面缺少 Claims / Evidence 区段。
  - 修复建议: 确认 paper_reading.json 含 claims_evidence_map,重新渲染。
- **[warning]** `missing_glossary` — 页面缺少 Glossary / 关键术语 区段。
  - 修复建议: 如果页面是 screenshot_only,可忽略;否则补 paper_reading.json 的 glossary 字段并重新渲染。

### https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

### https://conanxin.github.io/paper-reading-pages/weakinput-title-attention-is-all-you-need/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

### https://conanxin.github.io/paper-reading-pages/weakinput-abstract-how-to-read-a-paper/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

### https://conanxin.github.io/paper-reading-pages/weakinput-screenshot-how-to-read-a-paper/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

### https://conanxin.github.io/paper-reading-pages/weakinput-repo-bert/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

### https://conanxin.github.io/paper-reading-pages/runner-title-attention/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。

### https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[warning]** `missing_resolver_trail` — 页面缺少 Resolver Trail / 解析状态 区段,可能是 v0.2.7 之前渲染的旧页面。
  - 修复建议: 重新用 v0.2.8+ renderer 渲染;source_resolution_utils 会输出 Resolver status / Confidence / Matched paper 等。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

### https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/

- **[error]** `template_leak` — 渲染页包含未闭合的 template tag 或占位符: %}, No key references recorded, {%, {% else %}
  - 修复建议: 重新用 v0.2.9+ 渲染器 (render_page.py) 渲染该页面,确认 mini-template 的 {% else %} 分支已处理。
- **[error]** `old_footer` — 页面仍显示旧版本 footer: 'v0.1.0-alpha'
  - 修复建议: 重新渲染该页面以使用 v0.2.9+ 的 generator_version footer。
- **[info]** `no_visible_claim_id` — 页面没有可见的 claim ID (例如 C01/C02)。
  - 修复建议: 如果页面是弱输入(screenshot_only/abstract_only),可忽略;否则检查 paper_reading.json 的 claim id 字段。
- **[info]** `glossary_no_explicit_definition` — Glossary 仍是 v0.2.8 之前的 chip 形态(无显式定义块)。
  - 修复建议: v0.2.9+ 渲染器会输出 chip-body 块,重新渲染即可。

## Recommendations

- 8 页面仍泄漏 template tag — 优先 batch re-render + republish。
- 8 页面 footer 仍写 v0.1.0-alpha — 重新渲染以使用 generator_version。
- 8 页面缺 Resolver Trail — v0.2.8 之前渲染,建议在 v0.2.11+ 分批重渲染。
- 1 页面缺 Glossary — 检查 paper_reading.json 的 glossary 字段。
