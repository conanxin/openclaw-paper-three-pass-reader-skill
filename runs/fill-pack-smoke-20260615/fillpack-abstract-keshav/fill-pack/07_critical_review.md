# 07. Critical Review

## 目标

写 critical review + limitations + hidden assumptions + future work。

## 要填的字段

```json
"pass3": {
  "critical_review": ["<critique 1>", ...],
  "hidden_assumptions": ["<assumption 1>", ...],
  "limitations": ["<limitation 1>", ...],
  "future_work": ["<future direction 1>", ...],
  "application_notes": ["<how to apply 1>", ...]
}
```

## Evidence label 规则

- `critical_review` / `limitations` / `hidden_assumptions`：默认 `[Agent inference]` + 说明依据。
- `future_work`：默认 `[Author claim]`（作者自述）或 `[Agent inference]`。
- `application_notes`：默认 `[Agent inference]`。

## Stop condition

- 至少 1 条 `critical_review`，至少 1 条 `limitations`。
