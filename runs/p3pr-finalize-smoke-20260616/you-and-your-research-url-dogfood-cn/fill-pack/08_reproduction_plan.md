# 08. Reproduction Plan

## 目标

写一份最小可执行 reproduction plan：data + baseline + hardware + steps + sanity checks + success criteria。

## 允许使用的材料

- 实验部分（仅 full_text）。
- GitHub repo（如果存在）。
- 弱输入：仅 abstract 提到的 dataset / metric 名称。

## 要填的字段

```json
"reproduction_plan": {
  "dataset": "<name + 链接>",
  "baseline": "<baseline name>",
  "hardware": "<GPU/CPU/RAM>",
  "steps": ["<step 1>", ...],
  "sanity_checks": ["<check 1>", ...],
  "success_criteria": ["<criterion 1>", ...]
}
```

## Stop condition

- full_text：dataset + baseline + steps 全部非空。
- 弱输入：保留 `[DRAFT]` 或写"待补"。
