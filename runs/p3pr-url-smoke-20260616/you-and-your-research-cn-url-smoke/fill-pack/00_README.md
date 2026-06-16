# Agent Fill Pack — paper-three-pass-reader

> 这个目录 (`fill-pack/`) 是由 `run_paper_reading.py --fill-pack` 自动生成的**任务包**，不是阅读结果。
> 它的目标是把 `work/paper_reading.json` 中的 `[DRAFT]` 占位符逐字段填满，变成一份可发布的论文阅读页面。

## 当前 run 状态

| 项 | 值 |
| --- | --- |
| slug | `you-and-your-research-cn-url-smoke` |
| `paper_reading.json` 路径 | `/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/work/paper_reading.json` |
| `input_kind` | `paper_url` |
| `reading_mode` | `full_text` |
| `confidence` | `low` |
| `needs_confirmation` | `True` |
| agent profile | `default` |
| max_claims | `8` |
| max_figures | `6` |

## 哪些部分已经可做

- Stage 0 intake/resolution：runner 已经写了 `paper_metadata` + `intake_quality` + `source_resolution`。
- One / three / ten sentence summary：可以基于 abstract（如果存在）写**草稿**，但必须保留 `[Author claim]` / `[Needs verification]`。
- Pass 1 (Five Cs)：基于 metadata + abstract 通常已经可以写**骨架**。

## 哪些部分不可做

- Pass 2 main ideas / method summary / Pass 3 reconstruction：**只有在 `reading_mode == full_text` 时才能完整写**。
- Claims-Evidence Map：弱输入下每条 claim 必须带 `[Author claim]` / `[Uncertain]` / `[Needs verification]`。
- Reproduction plan：弱输入下只能写"待补"，不能编造。

## Source Resolution 摘要 (v0.2.8)

本节展示 runner 已经确定的 paper identity trail。agent 在 Stage 0 应当
**优先读取** `source_resolution` (top-level structured block) 而非
`intake_quality.source_resolution` (legacy list)。

- **输入线索**:`https://www.cs.virginia.edu/~robins/YouAndYourResearch.html`
- **解析状态**:`not_found`
- **匹配类型**:`none`
- **置信度**:`low`
- **匹配论文**:`(none)`
- **匹配 arXiv ID**:`(none)`
- **匹配仓库**:`(none)`
- **解析来源**:`skills/paper-three-pass-reader/data/resolver_hints.json`
- **解析步骤**:`cli overlay via p3pr paper_url subcommand; input='https://www.cs.virginia.edu/~robins/YouAndYourResearch.html'`
- **候选数量**:`0`
- **Structured trail**:`True`
- **Legacy fallback**:`False`

Top 候选:
  - (none)
## 交叉链接

- `docs/SOURCE_RESOLUTION.md` — canonical schema 与字段说明
- `docs/RESOLVER_HINTS.md` — 解析器如何产生该对象
- `docs/AUDIT.md` — audit 如何校验该对象
- `docs/AGENT_FILL_PACK.md` — 如何填写 source-resolution checklist


## Source Resolution Checklist (v0.2.8)

在 Stage 0 完成前，agent 必须逐条确认：

- [ ] 已读取 `source_resolution`（**top-level structured block 是 canonical**，不是 `intake_quality.source_resolution`）。
- [ ] 保留 `intake_quality.source_resolution` legacy list 的兼容说明（v0.2.5 历史 sample）。
- [ ] 写明 `confidence`（high / medium / low 或 0.0–1.0 数字）。
- [ ] 写明 `matched_paper_id` 与 `matched_arxiv_id`（若 `resolver_status=matched`）。
- [ ] 若 `resolver_status` 是 `ambiguous_clue` 或 `error` / `degraded = ambiguous_clue`，在 `intake_quality.ambiguities` 中说明，并要求用户确认论文身份。
- [ ] 若 `resolver_status = error`，确认 `source_resolution.degraded` 已被记录，且 `intake_quality.warnings` 至少有 1 条。

调试方式：`python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "<hint>"`。


## 如何一步步填 `work/paper_reading.json`

按编号顺序打开本目录下的 markdown，每读完一个 step，修改 `work/paper_reading.json` 对应字段。

1. `01_stage0_intake_resolution.md` — 校对 input 解析是否正确。
2. `02_pass1_five_cs.md` — 写 Five Cs。
3. `03_pass2_main_ideas.md` — 写 Pass 2 main ideas（弱输入下保留 `[DRAFT]`）。
4. `04_claims_evidence_map.md` — 写 claims + evidence。
5. `05_figures_tables.md` — 写 figure/table 解释。
6. `06_pass3_reconstruction.md` — 写 method reconstruction。
7. `07_critical_review.md` — 写 critical review + limitations。
8. `08_reproduction_plan.md` — 写 reproduction plan。
9. `09_finalize_json.md` — 校对整份 JSON。
10. `10_quality_gate.md` — 重新跑 audit + render。
11. `11_zh_cn_quality_gate.md` — **v0.2.4+** 中文质量门：检查中文覆盖率、字段深度、术语解释质量。

## 重新 render

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/work/paper_reading.json \
  --output /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/paper-reading-output
```

## 重新 audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/work/paper_reading.json --json-output /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/work/audit_result.json
```

## 发布到 GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish you-and-your-research-cn-url-smoke"
```

> 不要在没有真实阅读过论文之前发布。弱输入可以发布，但页面顶部 reading mode badge 必须如实显示 `full_text`。

## 不允许做的事

- 不要把 `[Author claim]` / `[Uncertain]` 改成 `[Paper evidence]` —— 这就是 audit 会发现的不诚实。
- 不要在没有 body 的情况下写出 "Pass 3 reconstruction was performed" 这种句子。
- 不要扩大成 SaaS / 自动论文总结 / 接入外部 LLM API。
