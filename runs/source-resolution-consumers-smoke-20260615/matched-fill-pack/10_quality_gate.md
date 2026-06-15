# 10. Quality Gate

## Goal

Final quality gate: audit + render + (optional) publish.

## Commands

```bash
# 1. Audit
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input work/paper_reading.json

# 2. Render
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input work/paper_reading.json \
  --output paper-reading-output

# 3. Publish (optional)
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish <slug>"
```

## Quality bar

- audit status = **PASS**.
- `index.html` shows Five Cs / Claims-Evidence / Pass 1/2/3 / Final Checklist.
- Reading mode badge matches the JSON.
- All evidence labels come from the whitelist.

## Stop condition

- audit PASS.
- index.html generated.
- If publish: remote URL HTTP 200.
