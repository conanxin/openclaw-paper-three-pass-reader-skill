# 04. Claims → Evidence Map

## 目标

为论文中重要 claim 写一条 claim-evidence 条目。**每条 claim 必须有 evidence_label**。

## 允许使用的材料

- abstract / introduction / experiments / figures / tables（按 `reading_mode` 决定）。
- 弱输入下：abstract 提到的每个数字 / 性能 / 主张都算一条候选 claim。

## 不允许做什么

- 不要把 `[Agent inference]` 写成 `[Paper evidence]`。
- 弱输入下不要写超过 `8` 条 claim（runner 默认上限）。
- 不要给 claim 编号 `C-DRAFT-xxx`——runner 已经在 draft 里放了一个示例，**全部替换**。

## 要填的字段

```json
"claims_evidence_map": [
  {
    "claim_id": "C-001",
    "claim_text": "<claim 的精确措辞>",
    "evidence_label": "[Paper evidence] | [Figure/Table evidence] | [Author claim] | [Agent inference] | [Uncertain] | [Needs verification]",
    "evidence_location": "<section / figure / table / abstract>",
    "evidence_kind": "paper_text | paper_figure | paper_table | author_claim | external_knowledge | none",
    "confidence": "high | medium | low",
    "notes": "<为什么是这个 label>",
    "needs_verification": true | false
  },
  ...
]
```

## Evidence label 规则（核心）

| Label | 含义 | 弱输入下可用？ |
| --- | --- | --- |
| `[Paper evidence]` | 论文 body 明确写了 | 否 |
| `[Figure/Table evidence]` | 论文图表明确显示 | 否 |
| `[Author claim]` | 作者在 abstract/conclusion 自述 | 是 |
| `[Agent inference]` | agent / reader 推断 | 是（但要说明依据） |
| `[Uncertain]` | 不能确定 | 是 |
| `[Needs verification]` | 需要再查 | 是 |

> **关键纪律**：弱输入下，`[Paper evidence]` 和 `[Figure/Table evidence]` 通常**不可用**——因为你没读过 body / 没看图。所有这些 claim 都要降级为 `[Author claim]` / `[Uncertain]` / `[Needs verification]`。

## Stop condition

- claim 数量：full_text ≥ 5，弱输入 1-8。
- 每条 claim 都有 `evidence_label` 且 label 在白名单内。
