#!/usr/bin/env bash
# validate.sh — paper-three-pass-reader (v0.1.0-alpha)
#
# Smoke check only. No long tests, no CI complexity.
#
# What it does:
#   1. Check that all required skill files exist.
#   2. Validate that every JSON file is parseable.
#   3. Run render_page.py on the sample JSON and check that index.html appears.
#   4. Grep the rendered index.html for the 7 mandatory page sections.
#   5. Exit 0 on PASS, non-zero on FAIL.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DIR="$ROOT/skills/paper-three-pass-reader"
SAMPLE="$SKILL_DIR/examples/sample_paper_reading.json"
TMP_OUT="$(mktemp -d -t p3pr-validate-XXXXXX)"
trap 'rm -rf "$TMP_OUT"' EXIT

fail=0
pass=0

step() { printf "\n[%s] %s\n" "$1" "$2"; }
ok()   { pass=$((pass+1)); printf "  ok   %s\n" "$1"; }
bad()  { fail=$((fail+1)); printf "  FAIL %s\n" "$1"; }

# 1. Required files
step 1 "Required files"
for f in \
  "$ROOT/README.md" \
  "$ROOT/README.zh-CN.md" \
  "$ROOT/LICENSE" \
  "$ROOT/CHANGELOG.md" \
  "$SKILL_DIR/SKILL.md" \
  "$SKILL_DIR/templates/index.html" \
  "$SKILL_DIR/templates/style.css" \
  "$SKILL_DIR/templates/app.js" \
  "$SKILL_DIR/templates/paper_reading.schema.json" \
  "$SKILL_DIR/scripts/render_page.py" \
  "$SKILL_DIR/scripts/create_output_skeleton.py" \
  "$SKILL_DIR/scripts/publish_output_to_github.sh" \
  "$SKILL_DIR/examples/sample_paper_reading.json" \
  "$SKILL_DIR/examples/sample_intake_quality.json" \
  "$SKILL_DIR/docs/USAGE.md" \
  "$SKILL_DIR/docs/OUTPUT_SCHEMA.md" \
  "$SKILL_DIR/docs/GITHUB_PAGES_PUBLISHING.md" \
  "$SKILL_DIR/docs/DESIGN_RATIONALE.md" \
  ; do
  if [[ -f "$f" ]]; then ok "exists: ${f#$ROOT/}"; else bad "missing: ${f#$ROOT/}"; fi
done

# 2. JSON parseability
step 2 "JSON parseability"
for j in \
  "$SAMPLE" \
  "$SKILL_DIR/examples/sample_intake_quality.json" \
  "$SKILL_DIR/templates/paper_reading.schema.json" \
  ; do
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$j" >/dev/null 2>&1; then
    ok "json valid: ${j#$ROOT/}"
  else
    bad "json invalid: ${j#$ROOT/}"
  fi
done

# 3. Sample render
step 3 "Sample render"
if python3 "$SKILL_DIR/scripts/render_page.py" --input "$SAMPLE" --output "$TMP_OUT/out" >/dev/null 2>&1; then
  ok "render_page.py exit 0"
else
  bad "render_page.py failed (exit non-zero)"
fi
for f in \
  "$TMP_OUT/out/index.html" \
  "$TMP_OUT/out/assets/style.css" \
  "$TMP_OUT/out/assets/app.js" \
  "$TMP_OUT/out/data/paper_reading.json" \
  "$TMP_OUT/out/data/paper_metadata.json" \
  "$TMP_OUT/out/data/intake_quality.json" \
  "$TMP_OUT/out/data/claims_evidence_map.json" \
  "$TMP_OUT/out/data/figures_tables.json" \
  "$TMP_OUT/out/data/paper_outline.json" \
  "$TMP_OUT/out/data/source_resolution.json" \
  "$TMP_OUT/out/data/candidate_papers.json" \
  "$TMP_OUT/out/reports/stage0_intake_report.md" \
  "$TMP_OUT/out/reports/pass1_first_pass.md" \
  "$TMP_OUT/out/reports/pass1_five_cs.md" \
  "$TMP_OUT/out/reports/pass1_reading_decision.md" \
  "$TMP_OUT/out/reports/pass2_main_ideas.md" \
  "$TMP_OUT/out/reports/pass2_figures_tables.md" \
  "$TMP_OUT/out/reports/pass2_claims_evidence_map.md" \
  "$TMP_OUT/out/reports/pass2_key_references.md" \
  "$TMP_OUT/out/reports/pass3_reconstruction.md" \
  "$TMP_OUT/out/reports/pass3_critical_review.md" \
  "$TMP_OUT/out/reports/pass3_reproduction_plan.md" \
  "$TMP_OUT/out/reports/final_reading_report.md" \
  ; do
  if [[ -f "$f" ]]; then ok "produced: ${f#$TMP_OUT/out/}"; else bad "missing: ${f#$TMP_OUT/out/}"; fi
done

# 4. Page contains mandatory sections
step 4 "Mandatory page sections"
INDEX="$TMP_OUT/out/index.html"
for sec in "Intake Status" "Five Cs" "Pass 1" "Pass 2" "Pass 3" "Claims" "Evidence" "Final" "Checklist"; do
  if grep -q "$sec" "$INDEX"; then
    ok "section found: $sec"
  else
    bad "section missing: $sec"
  fi
done

# 5. Required interactive bits
step 5 "Interactive bits"
for needle in 'class="tabs"' 'class="accordion"' 'id="filter-confidence"' 'id="filter-label"' 'class="ev-label' 'class="timeline"' 'class="chips"' 'data-reading-mode'; do
  if grep -q "$needle" "$INDEX"; then ok "found: $needle"; else bad "missing: $needle"; fi
done

# 6. SKILL.md word count (sanity — must be substantial)
step 6 "SKILL.md substance"
wc=$(wc -w < "$SKILL_DIR/SKILL.md")
if [[ "$wc" -ge 800 ]]; then ok "SKILL.md has $wc words (≥800)"; else bad "SKILL.md too thin: $wc words"; fi

# Summary
echo
echo "================================================="
echo " PASS: $pass    FAIL: $fail"
echo "================================================="

if [[ "$fail" -gt 0 ]]; then
  echo "STATUS: FAIL"
  exit 1
fi
echo "STATUS: PASS"
