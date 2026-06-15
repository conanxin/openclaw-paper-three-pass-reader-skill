# 02. Pass 1 — Five Cs

## 目标

写完 Five Cs：Category / Context / Correctness / Contributions / Clarity。

## 允许使用的材料

- abstract（如果 input 含 abstract）。
- title + authors + venue + field。
- 如果 `reading_mode == full_text`，允许读 introduction / conclusion。

> **弱输入提醒**：`reading_mode = abstract_only`，没有 body。Five Cs 只能基于 abstract + metadata 写**骨架**。`correctness` / `clarity` 这两项要诚实标 `[Needs verification]`。

## 不允许做什么

- 不要在 `correctness` 字段里说"论文实验全部正确"——除非你真的核对了实验部分。
- 不要把 author 在 abstract 中**声称**的贡献直接当作已验证贡献。
- 不要在没有 references 的情况下，写出"本文是第一个提出 X 的论文"。

## 要填的字段

```json
"five_cs": {
  "category": "<1-2 句：论文类型>",
  "context": "<2-4 句：研究背景 + 与已有工作的关系>",
  "correctness": "<1-3 句：方法 / 实验 / 论证是否成立 + evidence label>",
  "contributions": ["<贡献 1>", "<贡献 2>", ...],
  "clarity": "<1-3 句：写作 / 结构 / 图表清晰度 + evidence label>"
}
```

## Evidence label 规则

| 字段 | 弱输入下默认 label | full_text 下默认 label |
| --- | --- | --- |
| `category` | `[Author claim]` | `[Paper evidence]` |
| `context` | `[Author claim]` | `[Paper evidence]` |
| `correctness` | `[Needs verification]` | `[Paper evidence]` 或 `[Agent inference]` |
| `contributions` | `[Author claim]` | `[Author claim]`（作者自述） |
| `clarity` | `[Needs verification]` | `[Paper evidence]` 或 `[Agent inference]` |

## Stop condition

- 五个字段全部非空。
- `correctness` 和 `clarity` 必须含 evidence label。
