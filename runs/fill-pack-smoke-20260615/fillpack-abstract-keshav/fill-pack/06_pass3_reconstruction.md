# 06. Pass 3 — Method Reconstruction

## 目标

用自己的话把方法重建一遍：input → algorithm → output。要让一个没读过论文的人能复述。

> **弱输入提醒**：`reading_mode = abstract_only`。Pass 3 method reconstruction **不能**填——保留 `[DRAFT]`，并在 audit 里承认是 `unavailable_due_to_reading_mode`。

## 允许使用的材料

- full_text：method / algorithm / equations / appendix。
- 弱输入：abstract 范围。

## 要填的字段

```json
"pass3": {
  "method_reconstruction": ["<step 1>", "<step 2>", ...],
  "hidden_assumptions": ["<assumption 1>", ...],
  ...
}
```

## Stop condition

- full_text：`method_reconstruction` 至少 3 步。
- 弱输入：保留 `[DRAFT]`，并在 `notes` / `intake_quality.missing_fields` 里写明。
