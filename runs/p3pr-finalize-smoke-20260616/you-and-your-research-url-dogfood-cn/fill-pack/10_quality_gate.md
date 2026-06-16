# 10. Quality Gate

## 目标

最终质量门：audit + render + （可选）publish。

## 命令

```bash
# 1. Audit
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input work/paper_reading.json

# 2. Render
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input work/paper_reading.json \
  --output paper-reading-output

# 3. Publish（可选）
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish <slug>"
```

## Quality bar

- audit status = **PASS**。
- `index.html` 打开后 Five Cs / Claims-Evidence / Pass 1/2/3 / Final Checklist 全部可见。
- reading mode badge 与 JSON 一致。
- 所有 evidence label 至少有一个 `[Author claim]` / `[Paper evidence]` / `[Figure/Table evidence]` / `[Agent inference]` / `[Uncertain]` / `[Needs verification]` 之一。

## Stop condition

- audit PASS。
- index.html 生成。
- 如 publish：远端 URL HTTP 200。
