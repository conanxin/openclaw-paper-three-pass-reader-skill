# 03. Pass 2 — Main Ideas

## 目标

写出论文的主要 idea（最多 3-5 条），以及方法的核心机制。

## 允许使用的材料

- abstract（必须）。
- introduction / conclusion / figures（仅 `full_text`）。

## 不允许做什么

- 不要编造方法细节。如果 abstract 没描述，留 `[DRAFT]`。
- 不要把 author 在 future work 里写的设想当作 main idea。

## 要填的字段

```json
"pass2": {
  "main_ideas": ["<idea 1>", "<idea 2>", ...],
  "method_summary": "<1-3 句：方法核心机制>",
  ...
}
```

## Evidence label 规则

- `main_ideas[i]`：弱输入 → `[Author claim]`；full_text → `[Paper evidence]` + section 编号。
- `method_summary`：弱输入 → `[Author claim]`；full_text → `[Paper evidence]` + equation / section 编号。

## Stop condition

- 至少有 1 条 `main_ideas`。
- `method_summary` 长度 >= 30 字符。
