# 05. Figures and Tables

## 目标

为论文中的每个关键 figure / table 写一条 explanation 条目。

## 允许使用的材料

- 弱输入下：abstract 提到的 figure / table 编号 + title。
- full_text 下：实际看 figure / table。

## 不允许做什么

- 不要解释你没看过的 figure。
- 弱输入下，`[Figure/Table evidence]` 不可用——所有条目都用 `[Author claim]` / `[Needs verification]`。

## 要填的字段

```json
"figures_tables": [
  {
    "id": "F-1",
    "kind": "figure | table",
    "label": "<Figure 1: ...>",
    "explanation": "<这张图说明了什么>",
    "evidence_label": "[Author claim] | [Needs verification] | ...",
    "notes": "<可选>"
  },
  ...
]
```

## Stop condition

- 弱输入下：0-6 条，每条 evidence_label ∈ {`[Author claim]`, `[Needs verification]`, `[Uncertain]`}。
- full_text 下：实际 figure 数。
