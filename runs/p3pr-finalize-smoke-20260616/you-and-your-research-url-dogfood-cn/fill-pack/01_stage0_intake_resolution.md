# 01. Stage 0 — Intake and Resolution

## 目标

校对 Stage 0 解析是否正确：这份输入到底是不是那篇论文？是不是合法 arXiv ID / DOI？是否需要人工确认 canonical paper？

## 允许使用的材料

- 本目录 `input/input.md` 里捕获的原始输入。
- 联网搜索 arXiv / DOI / OpenReview / 出版方页面（仅用于**确认 canonical**，不下载 body）。
- runner hint（如果存在）。

## 不允许做什么

- 不要直接下载 PDF / 提取全文。runner 不做自动 deep-read。
- 不要把含糊 clue 自动当成 canonical paper。如果 `needs_confirmation = true`，必须显式标注。

## 要填的字段

- `paper_metadata.title` — 校对为 canonical title（arXiv 上显示的那个）。
- `paper_metadata.authors` — 与 arXiv 一致。
- `paper_metadata.year` — 首次公开年。
- `paper_metadata.identifiers.arxiv_id` — `None` 或形如 `"1706.03762"`。
- `paper_metadata.identifiers.doi` — `None` 或形如 `"10.xxxx/xxxx"`。
- `intake_quality.ambiguities` — 写下任何 disambiguation 问题。
- `intake_quality.source_resolution` — 每一步解析写成单独一行。

## Evidence label 规则

Stage 0 阶段的来源标注用纯文本即可，不需要 `[Paper evidence]`。但 `intake_quality` 里写"我们如何确认这篇就是 canonical"时，可以标注 `[Author claim]`（来源是 arXiv 页）或 `[Needs verification]`（来源是社交媒体线索）。

## 输出格式

直接在 `work/paper_reading.json` 里修改对应字段。**不要**把 `[DRAFT]` 占位符留在这里。

## Stop condition

- `intake_quality.needs_confirmation = false`，并且
- `paper_metadata.title` 与 arXiv 页完全一致。
