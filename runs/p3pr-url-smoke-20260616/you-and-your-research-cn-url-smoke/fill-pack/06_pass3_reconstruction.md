# 06. Pass 3 — Method Reconstruction

## 目标

用自己的话把方法重建一遍：input → algorithm → output。要让一个没读过论文的人能复述。

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
