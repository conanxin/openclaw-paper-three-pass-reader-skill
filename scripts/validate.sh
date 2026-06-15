#!/usr/bin/env bash
# validate.sh — paper-three-pass-reader (v0.2.1-alpha)
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

# 7. v0.1.1 hardening: render_page.py + publish_output_to_github.sh behaviour
step 7 "v0.1.1 hardening"

# 7a. render_page.py tolerates figures_tables string entries + bad evidence labels.
SKILL_DIR_FOR_TEST="$SKILL_DIR"
export SKILL_DIR_FOR_TEST
python3 - <<PYEOF >/dev/null 2>&1 && ok "render_page.py handles figures_tables string entry" || bad "render_page.py crashed on figures_tables string entry"
import json, subprocess, tempfile, pathlib, os
payload = {
    "schema_version": "0.1.0",
    "paper_metadata": {"title":"t","authors":["a"],"year":2024,"venue":"v","identifiers":{"arxiv_id":None,"doi":None,"openreview_id":None,"url":None},"source_kind":"complete_paper","reading_mode":"full_text"},
    "intake_quality": {"input_kind":"complete_paper","reading_mode":"full_text","confidence":"high","needs_confirmation":False,"missing_fields":[],"warnings":[]},
    "summaries": {"one_sentence":"x","three_sentence":["a","b","c"],"ten_sentence":["1","2","3","4","5","6","7","8","9","10"]},
    "five_cs": {"category":"x","context":"x","correctness":"x","contributions":["c1"],"clarity":"x"},
    "pass1": {"bird_eye_notes":"n","decision":"CONTINUE_FULL","decision_rationale":"r"},
    "pass2": {"main_ideas":["m1"],"key_references":[]},
    "pass3": {"method_reconstruction":["s1"],"critical_review":["cr1"]},
    "claims_evidence_map": [
        "plain string claim",
        {"claim_id":"C-002","claim_text":"dict","evidence_label":"[NotALegalLabel]","confidence":"ultra-high","evidence_location":"s1","evidence_kind":"paper_text","notes":"","needs_verification":False},
    ],
    "figures_tables": ["Figure 1 plain string note"],
    "glossary": ["Transformer (string)"],
    "limitations": ["L1"],
    "reproduction_plan": {"dataset":"","baseline":"","hardware":"","steps":["s1"],"sanity_checks":[],"success_criteria":[]},
    "open_questions": ["q1"],
    "final_checklist": ["plain string question"],
}
src = pathlib.Path(os.environ["SKILL_DIR_FOR_TEST"]) / "scripts" / "render_page.py"
with tempfile.TemporaryDirectory() as td:
    inp = pathlib.Path(td)/"in.json"; out = pathlib.Path(td)/"out"
    inp.write_text(json.dumps(payload), encoding="utf-8")
    r = subprocess.run(["python3", str(src), "--input", str(inp), "--output", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, f"render failed rc={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
    assert (out/"index.html").exists(), "no index.html produced"
    text = (out/"index.html").read_text(encoding="utf-8")
    assert "[Uncertain]" in text, "no fallback [Uncertain] label in rendered page"
PYEOF

# 7b. publish script help text mentions --site-path and --page-title.
HELP="$(bash "$SKILL_DIR/scripts/publish_output_to_github.sh" --help 2>&1 || true)"
if echo "$HELP" | grep -q -- "--site-path"; then ok "publish script advertises --site-path"; else bad "publish script help missing --site-path"; fi
if echo "$HELP" | grep -q -- "--page-title"; then ok "publish script advertises --page-title"; else bad "publish script help missing --page-title"; fi

# 7c. publish script --check mode passes.
if bash "$SKILL_DIR/scripts/publish_output_to_github.sh" --check >/dev/null 2>&1; then ok "publish script --check exits 0"; else bad "publish script --check failed"; fi

# 7d. Attention run re-renders without crashing.
rm -rf /tmp/p3pr-attn-validate
if python3 "$SKILL_DIR/scripts/render_page.py" \
     --input "$ROOT/runs/attention-is-all-you-need-20260615/work/paper_reading.json" \
     --output /tmp/p3pr-attn-validate >/dev/null 2>&1; then
  if [[ -f /tmp/p3pr-attn-validate/index.html ]]; then
    ok "Attention run re-renders OK"
  else
    bad "Attention re-render produced no index.html"
  fi
else
  bad "Attention run re-render failed"
fi

# 8. v0.2 runner checks
step 8 "v0.2 runner"

# 8a. runner script exists.
if [[ -x "$SKILL_DIR/scripts/run_paper_reading.py" ]]; then
  ok "runner script exists and is executable"
else
  bad "runner script missing or not executable: $SKILL_DIR/scripts/run_paper_reading.py"
fi

# 8b. runner help works.
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" --help >/dev/null 2>&1; then
  ok "runner --help exits 0"
else
  bad "runner --help failed"
fi

# 8c. title-only smoke run can generate work/paper_reading.json.
rm -rf /tmp/p3pr-runner-title-only
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "Attention Is All You Need" \
     --input-kind paper_title \
     --slug runner-title-only \
     --output-root /tmp/p3pr-runner-title-only >/dev/null 2>&1; then
  if [[ -f /tmp/p3pr-runner-title-only/runner-title-only/work/paper_reading.json ]]; then
    ok "title-only smoke run produced work/paper_reading.json"
  else
    bad "title-only smoke run did not produce work/paper_reading.json"
  fi
else
  bad "title-only smoke run failed"
fi

# 8d. abstract-only smoke run page contains abstract_only.
rm -rf /tmp/p3pr-runner-abstract
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "abstract excerpt of How to Read a Paper" \
     --input-kind paper_excerpt \
     --slug runner-abstract \
     --output-root /tmp/p3pr-runner-abstract \
     --render >/dev/null 2>&1; then
  if grep -q "abstract_only" /tmp/p3pr-runner-abstract/runner-abstract/paper-reading-output/index.html; then
    ok "abstract_only smoke page contains abstract_only"
  else
    bad "abstract_only smoke page missing abstract_only"
  fi
else
  bad "abstract_only smoke run failed"
fi

# 8e. screenshot-only smoke run page contains screenshot_only.
rm -rf /tmp/p3pr-runner-screenshot
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "OCR transcript of How to Read a Paper screenshot" \
     --input-kind paper_screenshot \
     --slug runner-screenshot \
     --output-root /tmp/p3pr-runner-screenshot \
     --render >/dev/null 2>&1; then
  if grep -q "screenshot_only" /tmp/p3pr-runner-screenshot/runner-screenshot/paper-reading-output/index.html; then
    ok "screenshot_only smoke page contains screenshot_only"
  else
    bad "screenshot_only smoke page missing screenshot_only"
  fi
else
  bad "screenshot_only smoke run failed"
fi

# 8f. Sample render still passes.
rm -rf /tmp/p3pr-validate-sample
if python3 "$SKILL_DIR/scripts/render_page.py" \
     --input "$SKILL_DIR/examples/sample_paper_reading.json" \
     --output /tmp/p3pr-validate-sample >/dev/null 2>&1; then
  if [[ -f /tmp/p3pr-validate-sample/index.html ]]; then
    ok "sample render still passes"
  else
    bad "sample render produced no index.html"
  fi
else
  bad "sample render failed"
fi

# 9. v0.2.1 agent fill pack + audit
step 9 "v0.2.1 agent fill pack + audit"

# 9a. runner help mentions all v0.2.1 flags.
RUNNER_HELP="$(python3 "$SKILL_DIR/scripts/run_paper_reading.py" --help 2>&1 || true)"
for flag in --fill-pack --audit --audit-warn-only --agent-profile --language --max-claims --max-figures; do
  if echo "$RUNNER_HELP" | grep -q -- "$flag"; then ok "runner advertises $flag"; else bad "runner help missing $flag"; fi
done

# 9b. audit script exists and --help runs.
if [[ -x "$SKILL_DIR/scripts/audit_paper_reading.py" ]]; then
  ok "audit script exists and is executable"
else
  bad "audit script missing or not executable: $SKILL_DIR/scripts/audit_paper_reading.py"
fi
if python3 "$SKILL_DIR/scripts/audit_paper_reading.py" --help >/dev/null 2>&1; then
  ok "audit script --help exits 0"
else
  bad "audit script --help failed"
fi

# 9c. fill_pack_writer exists.
if [[ -x "$SKILL_DIR/scripts/fill_pack_writer.py" ]]; then
  ok "fill_pack_writer exists and is executable"
else
  bad "fill_pack_writer missing or not executable: $SKILL_DIR/scripts/fill_pack_writer.py"
fi

# 9d. title-only smoke run with --fill-pack + --audit.
rm -rf /tmp/p3pr-fillpack-title
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "Attention Is All You Need" \
     --input-kind paper_title \
     --slug fillpack-title \
     --output-root /tmp/p3pr-fillpack-title \
     --reading-mode partial_text \
     --fill-pack --audit --audit-warn-only \
     --render >/dev/null 2>&1; then
  for f in \
      /tmp/p3pr-fillpack-title/fillpack-title/work/paper_reading.json \
      /tmp/p3pr-fillpack-title/fillpack-title/work/audit_result.json \
      /tmp/p3pr-fillpack-title/fillpack-title/reports/audit_summary.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/00_README.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/01_stage0_intake_resolution.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/02_pass1_five_cs.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/03_pass2_main_ideas.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/04_claims_evidence_map.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/05_figures_tables.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/06_pass3_reconstruction.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/07_critical_review.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/08_reproduction_plan.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/09_finalize_json.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/10_quality_gate.md \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/prompts.json \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/field_checklist.json \
      /tmp/p3pr-fillpack-title/fillpack-title/fill-pack/draft_status.json \
      /tmp/p3pr-fillpack-title/fillpack-title/paper-reading-output/index.html \
      ; do
    if [[ -f "$f" ]]; then ok "fillpack smoke produced: ${f#/tmp/p3pr-fillpack-title/fillpack-title/}"; else bad "fillpack smoke missing: ${f#/tmp/p3pr-fillpack-title/fillpack-title/}"; fi
  done
  # Audit result must be PASS or WARN (we used --audit-warn-only).
  if grep -q '"status": "PASS"' /tmp/p3pr-fillpack-title/fillpack-title/work/audit_result.json \
     || grep -q '"status": "WARN"' /tmp/p3pr-fillpack-title/fillpack-title/work/audit_result.json; then
    ok "fillpack title smoke audit PASS/WARN"
  else
    bad "fillpack title smoke audit not PASS/WARN"
  fi
else
  bad "title-only fillpack smoke run failed"
fi

# 9e. abstract-only fillpack run page contains abstract_only.
rm -rf /tmp/p3pr-fillpack-abstract
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "abstract excerpt of How to Read a Paper" \
     --input-kind paper_excerpt \
     --slug fillpack-abstract \
     --output-root /tmp/p3pr-fillpack-abstract \
     --reading-mode abstract_only \
     --fill-pack --audit --audit-warn-only \
     --render >/dev/null 2>&1; then
  if grep -q "abstract_only" /tmp/p3pr-fillpack-abstract/fillpack-abstract/paper-reading-output/index.html; then
    ok "abstract_only fillpack smoke page contains abstract_only"
  else
    bad "abstract_only fillpack smoke page missing abstract_only"
  fi
  # audit must NOT mark abstract_only as full_text-missing failure.
  if grep -q '"status": "FAIL"' /tmp/p3pr-fillpack-abstract/fillpack-abstract/work/audit_result.json; then
    bad "abstract_only audit wrongly marked FAIL"
  else
    ok "abstract_only audit did not falsely mark FAIL"
  fi
else
  bad "abstract-only fillpack smoke run failed"
fi

# 9f. screenshot-only fillpack run.
rm -rf /tmp/p3pr-fillpack-screenshot
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "OCR transcript of How to Read a Paper screenshot" \
     --input-kind paper_screenshot \
     --slug fillpack-screenshot \
     --output-root /tmp/p3pr-fillpack-screenshot \
     --reading-mode screenshot_only \
     --fill-pack --audit --audit-warn-only \
     --render >/dev/null 2>&1; then
  if grep -q "screenshot_only" /tmp/p3pr-fillpack-screenshot/fillpack-screenshot/paper-reading-output/index.html; then
    ok "screenshot_only fillpack smoke page contains screenshot_only"
  else
    bad "screenshot_only fillpack smoke page missing screenshot_only"
  fi
  # audit must mark missing_parts with body hints.
  if grep -q "full body" /tmp/p3pr-fillpack-screenshot/fillpack-screenshot/work/paper_reading.json \
     || grep -qi "full_body" /tmp/p3pr-fillpack-screenshot/fillpack-screenshot/work/paper_reading.json; then
    ok "screenshot_only draft has body-related missing_parts"
  else
    bad "screenshot_only draft missing body-related missing_parts"
  fi
else
  bad "screenshot-only fillpack smoke run failed"
fi

# 9g. Attention real run audit still passes.
if python3 "$SKILL_DIR/scripts/audit_paper_reading.py" \
     --input "$ROOT/runs/attention-is-all-you-need-20260615/work/paper_reading.json" >/dev/null 2>&1; then
  ok "Attention real run audit passes"
else
  bad "Attention real run audit failed (rc=$?)"
fi

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
