# 09. Finalize JSON

## 目标

校对 `work/paper_reading.json` 整体质量，准备 audit + render。

## 检查清单

- [ ] 所有 `[DRAFT]` 已替换（保留在 Pass 2/3 在弱输入下的合法 `[DRAFT]` 除外）。
- [ ] `paper_metadata.reading_mode` 与实际阅读情况一致。
- [ ] `intake_quality.needs_confirmation = false`，除非确实还有歧义。
- [ ] `claims_evidence_map` 每条 claim 都有 `evidence_label`，且 label ∈ 白名单。
- [ ] 弱输入下没有 `[Paper evidence]` / `[Figure/Table evidence]`（这是 audit 会标 FAIL 的）。
- [ ] `final_checklist` 至少 5 条；full_text ≥ 8 条。
- [ ] `glossary` 至少 3 条（除非论文领域陌生术语极少）。

## 跑 audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input work/paper_reading.json \
  --json-output work/audit_result.json
```

audit status 必须是 `PASS` 才能继续到 render / publish。

## Stop condition

- audit status = PASS。
