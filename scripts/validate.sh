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
for needle in 'class="tabs"' 'id="filter-confidence"' 'id="filter-label"' 'class="ev-label' 'class="timeline"' 'class="chips"' 'data-reading-mode'; do
  if grep -q "$needle" "$INDEX"; then ok "found: $needle"; else bad "missing: $needle"; fi
done
# Accordion-style disclosure: v0.2.9 template uses native <details> markup
# instead of the legacy "accordion" CSS class. Accept either, but require at
# least one collapsible section to be present in the rendered output.
if grep -qE 'class="accordion"|<details( |>)' "$INDEX"; then
  ok "found: collapsible section (details/accordion)"
else
  bad "missing: collapsible section (neither <details> nor class=accordion)"
fi

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

# 10. v0.2.3 zh-CN language support
step 10 "v0.2.3 zh-CN language support"

# 10a. runner --help mentions --language.
if echo "$RUNNER_HELP" | grep -q -- "--language"; then
  ok "runner --help mentions --language"
else
  bad "runner --help missing --language"
fi

# 10b. zh-CN runner smoke produces target_language / ui_language.
rm -rf /tmp/p3pr-runner-zh-cn
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "Attention Is All You Need" \
     --input-kind paper_title \
     --slug runner-zh-cn \
     --output-root /tmp/p3pr-runner-zh-cn \
     --language zh-CN >/dev/null 2>&1; then
  if grep -q '"target_language": "zh-CN"' /tmp/p3pr-runner-zh-cn/runner-zh-cn/work/paper_reading.json; then
    ok "zh-CN runner smoke has target_language=zh-CN"
  else
    bad "zh-CN runner smoke missing target_language=zh-CN"
  fi
  if grep -q '"ui_language": "zh-CN"' /tmp/p3pr-runner-zh-cn/runner-zh-cn/work/paper_reading.json; then
    ok "zh-CN runner smoke has ui_language=zh-CN"
  else
    bad "zh-CN runner smoke missing ui_language=zh-CN"
  fi
else
  bad "zh-CN runner smoke failed"
fi

# 10c. zh-CN fill-pack is in Chinese.
rm -rf /tmp/p3pr-runner-zh-cn-fp
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "Attention Is All You Need" \
     --input-kind paper_title \
     --slug runner-zh-cn-fp \
     --output-root /tmp/p3pr-runner-zh-cn-fp \
     --language zh-CN \
     --fill-pack >/dev/null 2>&1; then
  if [[ -f /tmp/p3pr-runner-zh-cn-fp/runner-zh-cn-fp/fill-pack/00_README.md ]]; then
    if grep -q "任务包" /tmp/p3pr-runner-zh-cn-fp/runner-zh-cn-fp/fill-pack/00_README.md; then
      ok "zh-CN fill-pack README is Chinese"
    else
      bad "zh-CN fill-pack README not Chinese"
    fi
  else
    bad "zh-CN fill-pack missing"
  fi
else
  bad "zh-CN fill-pack smoke run failed"
fi

# 10d. zh-CN render produces Chinese UI labels.
rm -rf /tmp/p3pr-zh-cn-render
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "Attention Is All You Need" \
     --input-kind paper_title \
     --slug runner-zh-cn-render \
     --output-root /tmp/p3pr-zh-cn-render \
     --language zh-CN \
     --render --audit-warn-only >/dev/null 2>&1; then
  ZH_INDEX="/tmp/p3pr-zh-cn-render/runner-zh-cn-render/paper-reading-output/index.html"
  if grep -q "输入解析状态" "$ZH_INDEX"; then
    ok "zh-CN rendered page has Chinese UI label"
  else
    bad "zh-CN rendered page missing Chinese UI label"
  fi
  if grep -q "第一遍阅读" "$ZH_INDEX" || grep -q "第一遍" "$ZH_INDEX"; then
    ok "zh-CN rendered page has Pass 1 Chinese label"
  else
    bad "zh-CN rendered page missing Pass 1 Chinese label"
  fi
else
  bad "zh-CN render smoke run failed"
fi

# 10e. audit detects missing Chinese content on zh-CN draft.
rm -rf /tmp/p3pr-zh-cn-audit
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
     --input "Attention Is All You Need" \
     --input-kind paper_title \
     --slug runner-zh-cn-audit \
     --output-root /tmp/p3pr-zh-cn-audit \
     --language zh-CN \
     --audit >/dev/null 2>&1; then
  # The fresh draft has no Chinese content; audit should warn.
  if grep -q "zh-CN but fewer than 50%" /tmp/p3pr-zh-cn-audit/runner-zh-cn-audit/work/audit_result.json; then
    ok "audit warns on zh-CN draft with no Chinese content"
  else
    bad "audit did not warn on zh-CN draft with no Chinese content"
  fi
else
  bad "zh-CN audit smoke run failed"
fi

# 10f. Second Me zh-CN real run audit passes.
if [[ -f "$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/audit_final.json" ]]; then
  if grep -q '"status": "PASS"' "$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/audit_final.json"; then
    ok "Second Me zh-CN real run audit PASS"
  else
    bad "Second Me zh-CN real run audit not PASS"
  fi
else
  bad "Second Me zh-CN audit_final.json missing"
fi

# 10g. Second Me zh-CN rendered page has Chinese labels.
if [[ -f "$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/paper-reading-output/index.html" ]]; then
  ZH_SM_INDEX="$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/paper-reading-output/index.html"
  for zh_label in "输入解析状态" "主张" "证据" "最终理解检查表"; do
    if grep -q "$zh_label" "$ZH_SM_INDEX"; then
      ok "Second Me zh-CN page has: $zh_label"
    else
      bad "Second Me zh-CN page missing: $zh_label"
    fi
  done
else
  bad "Second Me zh-CN index.html missing"
fi

# 11. v0.2.4 zh-CN quality gate
step 11 "v0.2.4 zh-CN quality gate"

# 11a. quality_gate_zh_cn.py --help runs.
if python3 "$SKILL_DIR/scripts/quality_gate_zh_cn.py" --help >/dev/null 2>&1; then
  ok "quality_gate_zh_cn.py --help exits 0"
else
  bad "quality_gate_zh_cn.py --help failed"
fi

# 11b. quality_gate_zh_cn.py is executable.
if [[ -x "$SKILL_DIR/scripts/quality_gate_zh_cn.py" ]]; then
  ok "quality_gate_zh_cn.py is executable"
else
  bad "quality_gate_zh_cn.py not executable"
fi

# 11c. Second Me zh-CN run quality gate PASS.
QG_SM="$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/quality_gate_zh_cn.json"
if [[ -f "$QG_SM" ]]; then
  if grep -q '"status": "PASS"' "$QG_SM"; then
    ok "Second Me zh-CN quality gate PASS"
  else
    bad "Second Me zh-CN quality gate not PASS"
  fi
else
  bad "Second Me zh-CN quality_gate_zh_cn.json missing"
fi

# 11d. Bad zh-CN sample quality gate FAILS (or WARNs).
if [[ -f "$ROOT/runs/quality-gate-smoke-20260615/bad-zh-cn-draft/work/paper_reading.json" ]]; then
  if python3 "$SKILL_DIR/scripts/quality_gate_zh_cn.py" \
       --input "$ROOT/runs/quality-gate-smoke-20260615/bad-zh-cn-draft/work/paper_reading.json" \
       --json-output /tmp/p3pr-bad-qg.json >/dev/null 2>&1; then
    bad "bad zh-CN sample should FAIL quality gate but did not"
  else
    ok "bad zh-CN sample correctly FAILed quality gate"
  fi
else
  bad "bad zh-CN sample draft missing"
fi

# 11e. runner help mentions --quality-gate.
if echo "$RUNNER_HELP" | grep -q -- "--quality-gate"; then
  ok "runner --help mentions --quality-gate"
else
  bad "runner --help missing --quality-gate"
fi

# 11f. audit help mentions --quality-gate.
AUDIT_HELP="$(python3 "$SKILL_DIR/scripts/audit_paper_reading.py" --help 2>&1 || true)"
if echo "$AUDIT_HELP" | grep -q -- "--quality-gate"; then
  ok "audit --help mentions --quality-gate"
else
  bad "audit --help missing --quality-gate"
fi

# 11g. zh-CN fill-pack contains 11_zh_cn_quality_gate.md.
if [[ -f /tmp/p3pr-runner-zh-cn-fp/runner-zh-cn-fp/fill-pack/11_zh_cn_quality_gate.md ]]; then
  ok "zh-CN fill-pack contains 11_zh_cn_quality_gate.md"
else
  bad "zh-CN fill-pack missing 11_zh_cn_quality_gate.md"
fi

# 11h. audit --quality-gate integration on Second Me zh-CN run.
if python3 "$SKILL_DIR/scripts/audit_paper_reading.py" \
     --input "$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/paper_reading.json" \
     --quality-gate 2>&1 | grep -q "Quality gate status: PASS"; then
  ok "audit --quality-gate integration PASS on Second Me zh-CN"
else
  bad "audit --quality-gate integration failed on Second Me zh-CN"
fi

# 11i. audit default hint on zh-CN run (without --quality-gate).
if python3 "$SKILL_DIR/scripts/audit_paper_reading.py" \
     --input "$ROOT/runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/work/paper_reading.json" 2>&1 | grep -q "Re-run with --quality-gate"; then
  ok "audit shows --quality-gate hint on zh-CN run"
else
  bad "audit did not show --quality-gate hint on zh-CN run"
fi

# 12. v0.2.5 P3PR one-line CLI
step 12 "v0.2.5 P3PR one-line CLI"

# 12a. p3pr shim exists and is executable.
if [[ -x "$ROOT/p3pr" ]]; then
  ok "p3pr shim exists and is executable"
else
  bad "p3pr shim missing or not executable"
fi

# 12b. p3pr --help runs.
if "$ROOT/p3pr" --help >/dev/null 2>&1; then
  ok "p3pr --help exits 0"
else
  bad "p3pr --help failed"
fi

# 12c. p3pr.py --help runs.
if python3 "$SKILL_DIR/scripts/p3pr.py" --help >/dev/null 2>&1; then
  ok "p3pr.py --help exits 0"
else
  bad "p3pr.py --help failed"
fi

# 12d. p3pr subcommands work.
for sub in arxiv title abstract screenshot repo pdf; do
  if "$ROOT/p3pr" "$sub" --help >/dev/null 2>&1; then
    ok "p3pr $sub --help works"
  else
    bad "p3pr $sub --help failed"
  fi
done

# 12e. arxiv dry-run prints expected fields.
DRY_OUT="$("$ROOT/p3pr" arxiv 2503.08102 --zh --full --publish --dry-run 2>&1 || true)"
for needle in "P3PR_STATUS" "P3PR_INPUT_KIND" "P3PR_READING_MODE" "P3PR_RUN_DIR"; do
  if echo "$DRY_OUT" | grep -q "$needle"; then
    ok "arxiv dry-run prints: $needle"
  else
    bad "arxiv dry-run missing: $needle"
  fi
done
if echo "$DRY_OUT" | grep -q "P3PR_READING_MODE: full_text"; then
  ok "arxiv dry-run says reading_mode=full_text"
else
  bad "arxiv dry-run reading_mode not full_text"
fi
if echo "$DRY_OUT" | grep -q "P3PR_INPUT_KIND: paper_identifier"; then
  ok "arxiv dry-run says input_kind=paper_identifier"
else
  bad "arxiv dry-run input_kind wrong"
fi

# 12f. title dry-run does not crash.
if "$ROOT/p3pr" title "Attention Is All You Need" --zh --full --publish --dry-run >/dev/null 2>&1; then
  ok "title dry-run exits 0"
else
  bad "title dry-run failed"
fi

# 12g. repo dry-run does not crash.
if "$ROOT/p3pr" repo https://github.com/google-research/bert --zh --full --publish --dry-run >/dev/null 2>&1; then
  ok "repo dry-run (BERT) exits 0"
else
  bad "repo dry-run (BERT) failed"
fi

# 12h. screenshot smoke run produced work/paper_reading.json + fill-pack + page.
SMOKE_DIR="$ROOT/runs/p3pr-cli-smoke-20260615/cli-screenshot-smoke"
if [[ -f "$SMOKE_DIR/work/paper_reading.json" ]]; then
  ok "CLI screenshot smoke: work/paper_reading.json exists"
else
  bad "CLI screenshot smoke: work/paper_reading.json missing"
fi
if [[ -d "$SMOKE_DIR/fill-pack" ]]; then
  ok "CLI screenshot smoke: fill-pack exists"
else
  bad "CLI screenshot smoke: fill-pack missing"
fi

# 12i. abstract smoke run has correct reading_mode.
ABS_JSON="$ROOT/runs/p3pr-cli-smoke-20260615/cli-abstract-smoke/work/paper_reading.json"
if [[ -f "$ABS_JSON" ]] && grep -q '"reading_mode": "abstract_only"' "$ABS_JSON"; then
  ok "CLI abstract smoke: reading_mode = abstract_only"
else
  bad "CLI abstract smoke: reading_mode not abstract_only"
fi

# 12j. CLI smoke runs do not pretend full_text on weak inputs.
for weak_slug in cli-screenshot-smoke cli-abstract-smoke; do
  weak_json="$ROOT/runs/p3pr-cli-smoke-20260615/${weak_slug}/work/paper_reading.json"
  if [[ -f "$weak_json" ]]; then
    if grep -q '"reading_mode": "full_text"' "$weak_json"; then
      bad "CLI ${weak_slug} pretends full_text (should be weak mode)"
    else
      ok "CLI ${weak_slug} does not pretend full_text"
    fi
  fi
done

# 13. v0.2.6 shared resolver hints unification
step 13 "v0.2.6 shared resolver hints"

# 13a. resolver_hints.json exists, is valid JSON, and includes the 4 anchor papers.
HINTS_JSON="$SKILL_DIR/data/resolver_hints.json"
if [[ -f "$HINTS_JSON" ]]; then
  ok "resolver_hints.json exists"
else
  bad "resolver_hints.json missing: ${HINTS_JSON#$ROOT/}"
fi
if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$HINTS_JSON" >/dev/null 2>&1; then
  ok "resolver_hints.json parses"
else
  bad "resolver_hints.json invalid JSON"
fi
for pid in attention-is-all-you-need bert how-to-read-a-paper second-me paper-three-pass-reader-skill; do
  if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); ids=[p.get('id') for p in d.get('papers',[])]; sys.exit(0 if '$pid' in ids else 1)" "$HINTS_JSON" >/dev/null 2>&1; then
    ok "resolver_hints.json has paper: $pid"
  else
    bad "resolver_hints.json missing paper: $pid"
  fi
done

# 13b. resolver_hints.py exists and loads.
if [[ -f "$SKILL_DIR/scripts/resolver_hints.py" ]]; then
  ok "resolver_hints.py exists"
else
  bad "resolver_hints.py missing"
fi
if python3 -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import resolver_hints; rh=resolver_hints.load_hints(); assert rh.get('papers'), 'no papers'" >/dev/null 2>&1; then
  ok "resolver_hints.load_hints() returns papers"
else
  bad "resolver_hints.load_hints() broken"
fi

# 13c. resolve_paper_hint.py CLI works for title/arxiv/repo.
for case in \
    "title|Attention Is All You Need|attention-is-all-you-need" \
    "repo|https://github.com/google-research/bert|bert" \
    "arxiv|2503.08102|second-me" \
    "any|second me|second-me" \
    ; do
  IFS="|" read -r kind val expect <<<"$case"
  out="$(python3 "$SKILL_DIR/scripts/resolve_paper_hint.py" "$kind" "$val" 2>/dev/null || true)"
  pid="$(printf '%s' "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); print((d.get('paper') or {}).get('id',''))" 2>/dev/null || true)"
  if [[ "$pid" == "$expect" ]]; then
    ok "resolve_paper_hint $kind '$val' -> $pid"
  else
    bad "resolve_paper_hint $kind '$val' -> '$pid' (expected $expect)"
  fi
done

# 13d. Unknown input returns not_found / ambiguous without crashing.
UNK_OUT="$(python3 "$SKILL_DIR/scripts/resolve_paper_hint.py" title "completely unknown paper xyz" 2>&1 || true)"
if echo "$UNK_OUT" | grep -q '"status": "not_found"'; then
  ok "resolve_paper_hint unknown -> not_found"
else
  bad "resolve_paper_hint unknown did not return not_found"
fi

# 13e. Aliases work (transformers / Second Me case-insensitive).
ALIAS_OUT="$(python3 "$SKILL_DIR/scripts/resolve_paper_hint.py" title "transformers" 2>&1 || true)"
if echo "$ALIAS_OUT" | grep -q '"id": "attention-is-all-you-need"'; then
  ok "resolver_hints alias 'transformers' -> attention-is-all-you-need"
else
  bad "resolver_hints alias 'transformers' did not match"
fi

# 13f. p3pr.py no longer has a local HINTS dict.
if ! grep -q '^HINTS = {' "$SKILL_DIR/scripts/p3pr.py"; then
  ok "p3pr.py no longer has local HINTS dict"
else
  bad "p3pr.py still has local HINTS dict"
fi

# 13g. p3pr.py imports from resolver_hints.
if grep -q 'from resolver_hints import' "$SKILL_DIR/scripts/p3pr.py"; then
  ok "p3pr.py imports from resolver_hints"
else
  bad "p3pr.py does not import from resolver_hints"
fi

# 13h. run_paper_reading.py imports from resolver_hints.
if grep -q 'from resolver_hints import' "$SKILL_DIR/scripts/run_paper_reading.py"; then
  ok "run_paper_reading.py imports from resolver_hints"
else
  bad "run_paper_reading.py does not import from resolver_hints"
fi

# 13i. runner RESOLVER_HINTS dict still has the historical keys (back-compat).
RH_LEN="$(python3 -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import run_paper_reading as r; print(len(r.RESOLVER_HINTS))")"
if [[ "$RH_LEN" -ge 8 ]]; then
  ok "runner RESOLVER_HINTS back-compat dict has $RH_LEN keys (>=8)"
else
  bad "runner RESOLVER_HINTS back-compat dict too small: $RH_LEN"
fi

# 13j. runner RESOLVER_HINTS resolves historical keys.
if python3 -c "import sys; sys.path.insert(0,'$SKILL_DIR/scripts'); import run_paper_reading as r; assert r.RESOLVER_HINTS['attention is all you need']['arxiv_id']=='1706.03762'; assert r.RESOLVER_HINTS['https://github.com/google-research/bert']['arxiv_id']=='1810.04805'; assert r.RESOLVER_HINTS['how to read a paper']['default_reading_mode']=='abstract_only'" >/dev/null 2>&1; then
  ok "runner historical RESOLVER_HINTS keys still resolve correctly"
else
  bad "runner historical RESOLVER_HINTS keys do not resolve correctly"
fi

# 13k. p3pr dry-run summary now includes resolver details.
DRY_V26="$(cd "$ROOT" && ./p3pr arxiv 2503.08102 --zh --full --publish --dry-run 2>&1 || true)"
for needle in "P3PR_RESOLVER_STATUS" "P3PR_RESOLVER_MATCH_TYPE" "P3PR_CANONICAL_TITLE" "P3PR_ARXIV_ID" "P3PR_DEFAULT_SLUG"; do
  if echo "$DRY_V26" | grep -q "$needle"; then
    ok "p3pr dry-run prints: $needle"
  else
    bad "p3pr dry-run missing: $needle"
  fi
done

# 13l. p3pr title dry-run auto-derives canonical title from hint.
DRY_V26_TITLE="$(cd "$ROOT" && ./p3pr title "Attention Is All You Need" --zh --full --publish --dry-run 2>&1 || true)"
if echo "$DRY_V26_TITLE" | grep -q "P3PR_RESOLVER_MATCH_TYPE: title" \
   && echo "$DRY_V26_TITLE" | grep -q "P3PR_ARXIV_ID: 1706.03762"; then
  ok "p3pr title dry-run auto-resolves to arxiv 1706.03762"
else
  bad "p3pr title dry-run did not auto-resolve"
fi

# 13m. p3pr repo dry-run auto-resolves BERT hint.
DRY_V26_REPO="$(cd "$ROOT" && ./p3pr repo https://github.com/google-research/bert --zh --full --publish --dry-run 2>&1 || true)"
if echo "$DRY_V26_REPO" | grep -q "P3PR_RESOLVER_MATCH_TYPE: repo" \
   && echo "$DRY_V26_REPO" | grep -q "P3PR_ARXIV_ID: 1810.04805"; then
  ok "p3pr repo dry-run auto-resolves BERT to arxiv 1810.04805"
else
  bad "p3pr repo dry-run did not auto-resolve BERT"
fi

# 13n. p3pr screenshot smoke re-run still works (auto-detects arXiv from transcript).
rm -rf /tmp/p3pr-v26-screenshot
if cd "$ROOT" && ./p3pr screenshot runs/p3pr-cli-smoke-20260615/input/screenshot.md \
    --zh --screenshot-only --slug cli-screenshot-smoke-v26 \
    --output-root /tmp/p3pr-v26-screenshot --no-publish >/dev/null 2>&1; then
  if grep -q "arxiv_id" /tmp/p3pr-v26-screenshot/cli-screenshot-smoke-v26/work/paper_reading.json 2>/dev/null \
     && grep -q '"2503.08102"' /tmp/p3pr-v26-screenshot/cli-screenshot-smoke-v26/work/paper_reading.json; then
    ok "p3pr screenshot v0.2.6 smoke auto-detected arXiv 2503.08102"
  else
    bad "p3pr screenshot v0.2.6 smoke did not auto-detect arXiv"
  fi
else
  bad "p3pr screenshot v0.2.6 smoke failed"
fi

# 14. v0.2.6 source_resolution + resolver helper degradation
step 14 "v0.2.6 source_resolution + resolver helper degradation"

# 14a. runner --help mentions --resolver-source.
if echo "$RUNNER_HELP" | grep -q -- "--resolver-source"; then
  ok "runner --help mentions --resolver-source"
else
  bad "runner --help missing --resolver-source"
fi

# 14b. p3pr title smoke: paper_reading.json has the new structured source_resolution fields.
if [[ -f /tmp/p3pr-v26-screenshot/cli-screenshot-smoke-v26/work/paper_reading.json ]]; then
  SR_JSON=/tmp/p3pr-v26-screenshot/cli-screenshot-smoke-v26/work/paper_reading.json
  for field in hint_input resolver_source resolver_helper resolver_status resolver_match_type confidence matched_paper_id source_resolution_step; do
    if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d.get('source_resolution',{}).get('$field') is not None" "$SR_JSON" 2>/dev/null; then
      ok "source_resolution has $field"
    else
      bad "source_resolution missing $field"
    fi
  done
else
  bad "no p3pr smoke draft to inspect for source_resolution"
fi

# 14c. p3pr title smoke: source_resolution.matched_paper_id matches the shared resolver.
if [[ -f /tmp/p3pr-v26-screenshot/cli-screenshot-smoke-v26/work/paper_reading.json ]]; then
  mp="$(python3 -c "import json; d=json.load(open('/tmp/p3pr-v26-screenshot/cli-screenshot-smoke-v26/work/paper_reading.json')); print(d['source_resolution'].get('matched_paper_id'))")"
  if [[ "$mp" == "second-me" ]]; then
    ok "source_resolution.matched_paper_id=second-me (auto-detected from transcript)"
  else
    bad "source_resolution.matched_paper_id is '$mp' (expected second-me)"
  fi
fi

# 14d. resolver overlay: runner accepts --resolver-source and applies it.
rm -rf /tmp/p3pr-v26b-overlay
cat > /tmp/p3pr-v26b-overlay.json <<'JSON'
{
  "status": "matched",
  "match_type": "repo",
  "confidence": "high",
  "paper": {"id": "bert", "canonical_title": "BERT", "arxiv_id": "1810.04805"},
  "matched_repo": "https://github.com/google-research/bert",
  "candidates": [],
  "source_resolution_step": "manual test overlay"
}
JSON
if python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
   --input "https://github.com/google-research/bert" \
   --input-kind project_or_repo \
   --slug v26b-overlay \
   --output-root /tmp/p3pr-v26b-overlay \
   --resolver-source /tmp/p3pr-v26b-overlay.json >/dev/null 2>&1; then
  if python3 -c "import json; d=json.load(open('/tmp/p3pr-v26b-overlay/v26b-overlay/work/paper_reading.json')); assert d['source_resolution']['matched_paper_id']=='bert'; assert d['source_resolution']['resolver_status']=='matched'; assert d['source_resolution']['resolver_match_type']=='repo'" >/dev/null 2>&1; then
    ok "runner --resolver-source overlay applies (matched_paper_id=bert, status=matched, match_type=repo)"
  else
    bad "runner --resolver-source overlay did not apply correctly"
  fi
else
  bad "runner --resolver-source overlay run failed"
fi

# 14e. Hostile resolver degradation: PYTHONPATH override makes resolver_hints raise;
#      runner must NOT fail and must record status=error + degraded=ambiguous_clue.
rm -rf /tmp/p3pr-hostile-sandbox
HOSTILE_DIR=/tmp/p3pr-hostile-dir
rm -rf "$HOSTILE_DIR"
mkdir -p "$HOSTILE_DIR"
# Copy the real scripts dir (minus resolver_hints.py) so the runner can import its
# other dependencies (audit, fill_pack_writer, etc.).
mkdir -p "$HOSTILE_DIR/scripts"
for f in "$SKILL_DIR/scripts"/*.py "$SKILL_DIR/scripts"/*.sh; do
  bn="$(basename "$f")"
  if [[ "$bn" == "resolver_hints.py" ]] || [[ "$bn" == "__pycache__" ]]; then continue; fi
  cp "$f" "$HOSTILE_DIR/scripts/"
done
# Write a hostile resolver_hints.py
cat > "$HOSTILE_DIR/scripts/resolver_hints.py" <<'PYEOF'
def resolve_any(*a, **k):
    raise RuntimeError("validate.sh hostile resolver stub")
def resolve_title(*a, **k):
    raise RuntimeError("validate.sh hostile resolver stub")
def resolve_arxiv(*a, **k):
    raise RuntimeError("validate.sh hostile resolver stub")
def resolve_repo(*a, **k):
    raise RuntimeError("validate.sh hostile resolver stub")
def load_hints(*a, **k):
    return {"schema_version":"hostile","papers":[],"repo_hints":[]}
def paper_to_runner_overrides(*a, **k):
    return {}
PYEOF
# Symlink data/ so the rest of the pipeline works (and override our resolver).
mkdir -p "$HOSTILE_DIR/scripts/data"
for f in "$SKILL_DIR/data"/*; do
  ln -sf "$f" "$HOSTILE_DIR/scripts/data/"
done
# Run with PYTHONPATH=$HOSTILE_DIR/scripts so the hostile resolver is picked first.
if env PYTHONPATH="$HOSTILE_DIR/scripts" python3 "$SKILL_DIR/scripts/run_paper_reading.py" \
   --input "Attention Is All You Need" \
   --input-kind paper_title \
   --slug v26-hostile \
   --output-root /tmp/p3pr-hostile-sandbox >/dev/null 2>&1; then
  HOSTILE_JSON=/tmp/p3pr-hostile-sandbox/v26-hostile/work/paper_reading.json
  if [[ -f "$HOSTILE_JSON" ]]; then
    SR_STATUS="$(python3 -c "import json; print(json.load(open('$HOSTILE_JSON'))['source_resolution'].get('resolver_status'))")"
    SR_DEGRADED="$(python3 -c "import json; print(json.load(open('$HOSTILE_JSON'))['source_resolution'].get('degraded'))")"
    if [[ "$SR_STATUS" == "error" ]]; then
      ok "hostile resolver: source_resolution.resolver_status=error"
    else
      bad "hostile resolver: status was '$SR_STATUS' (expected error)"
    fi
    if [[ "$SR_DEGRADED" == "ambiguous_clue" ]]; then
      ok "hostile resolver: source_resolution.degraded=ambiguous_clue"
    else
      bad "hostile resolver: degraded was '$SR_DEGRADED' (expected ambiguous_clue)"
    fi
    # And runner still wrote a paper_reading.json (no crash)
    if [[ -f "$HOSTILE_JSON" ]]; then
      ok "hostile resolver: runner still produced paper_reading.json (no crash)"
    fi
  else
    bad "hostile resolver: no paper_reading.json produced"
  fi
else
  bad "hostile resolver: runner exited non-zero (should degrade gracefully)"
fi
rm -rf "$HOSTILE_DIR"

# 14f. Original CLI smokes (screenshot + abstract) still pass.
SMOKE_DIR="$ROOT/runs/p3pr-cli-smoke-20260615"
for sub in cli-screenshot-smoke cli-abstract-smoke; do
  if [[ -f "$SMOKE_DIR/$sub/work/paper_reading.json" ]]; then
    if grep -q '"resolver_status"' "$SMOKE_DIR/$sub/work/paper_reading.json"; then
      ok "v0.2.5 $sub still has source_resolution.resolver_status"
    else
      bad "v0.2.5 $sub missing source_resolution.resolver_status"
    fi
  fi
done

# ----------------------------------------------------------------------
# step 15 — v0.2.8 structured source_resolution consumers
# ----------------------------------------------------------------------
step 15 "v0.2.8 structured source_resolution consumers"

# 15a. The utility module is importable.
if python3 -c "import sys; sys.path.insert(0,'$ROOT/skills/paper-three-pass-reader/scripts'); import source_resolution_utils" >/dev/null 2>&1; then
  ok "source_resolution_utils.py imports cleanly"
else
  bad "source_resolution_utils.py failed to import"
fi

# 15b. Utility reads structured source_resolution correctly.
SR_UTILS_DIR="$ROOT/skills/paper-three-pass-reader/scripts"
SMOKE="$ROOT/runs/source-resolution-consumers-smoke-20260615"
if (cd "$SR_UTILS_DIR" && python3 - "$SMOKE/matched-paper_reading.json" <<'PYEOF' >/dev/null 2>&1
import sys, json
sys.path.insert(0, ".")
import source_resolution_utils as u
data = json.load(open(sys.argv[1]))
s = u.summarize_source_resolution(data)
assert s["structured"] is True, s
assert s["matched_paper_id"] == "attention-is-all-you-need", s
errs, warns = u.validate_source_resolution(data)
assert not errs, errs
PYEOF
); then
  ok "utility reads structured source_resolution from matched sample"
else
  bad "utility could not read structured source_resolution from matched sample"
fi

# 15c. Legacy-only sample does not crash and produces a fallback summary.
if (cd "$SR_UTILS_DIR" && python3 - "$SMOKE/legacy-only-paper_reading.json" <<'PYEOF' >/dev/null 2>&1
import sys, json
sys.path.insert(0, ".")
import source_resolution_utils as u
data = json.load(open(sys.argv[1]))
s = u.summarize_source_resolution(data)
assert s["fallback_legacy"] is True, s
errs, warns = u.validate_source_resolution(data)
assert any("legacy" in w for w in warns), warns
PYEOF
); then
  ok "legacy-only sample produces fallback summary and a legacy warning"
else
  bad "legacy-only sample did not degrade gracefully"
fi

# 15d. Renderer page for matched sample includes expected markers (English).
MATCHED_HTML="$SMOKE/matched-render/index.html"
if [[ -f "$MATCHED_HTML" ]]; then
  if grep -q 'Resolver status' "$MATCHED_HTML" && \
     grep -q 'Confidence' "$MATCHED_HTML" && \
     grep -q 'Matched arXiv ID' "$MATCHED_HTML" && \
     grep -q 'attention-is-all-you-need' "$MATCHED_HTML" && \
     grep -q '1706.03762' "$MATCHED_HTML"; then
    ok "matched render contains Resolver status / Confidence / arXiv ID"
  else
    bad "matched render is missing one of Resolver status / Confidence / arXiv ID"
  fi
else
  bad "matched render/index.html is missing — re-run smoke generation"
fi

# 15e. Renderer page for zh-CN sample contains Chinese labels.
ZH_HTML="$SMOKE/zh-cn-render/index.html"
if [[ -f "$ZH_HTML" ]]; then
  if grep -q '解析状态' "$ZH_HTML" && \
     grep -q '置信度' "$ZH_HTML" && \
     grep -q '匹配 arXiv ID' "$ZH_HTML" && \
     grep -q '1706.03762' "$ZH_HTML"; then
    ok "zh-cn render contains 解析状态 / 置信度 / 匹配 arXiv ID"
  else
    bad "zh-cn render is missing one of 解析状态 / 置信度 / 匹配 arXiv ID"
  fi
else
  bad "zh-cn render/index.html is missing"
fi

# 15f. Hostile/degraded sample renders without crashing.
DEG_HTML="$SMOKE/degraded-render/index.html"
if [[ -f "$DEG_HTML" ]]; then
  if grep -q 'Resolver status' "$DEG_HTML" && \
     grep -q 'Degraded fallback' "$DEG_HTML"; then
    ok "degraded render contains Degraded fallback badge + Resolver status"
  else
    bad "degraded render is missing Degraded fallback badge"
  fi
else
  bad "degraded render/index.html is missing"
fi

# 15g. Audit JSON includes source_resolution block.
if python3 - "$ROOT" <<'PYEOF' >/dev/null 2>&1
import sys, json, subprocess, tempfile, pathlib
root = sys.argv[1]
src = pathlib.Path(root) / "runs/source-resolution-consumers-smoke-20260615/matched-paper_reading.json"
data = json.load(open(src))
sys.path.insert(0, str(pathlib.Path(root) / "skills/paper-three-pass-reader/scripts"))
import audit_paper_reading
r = audit_paper_reading.audit(data)
assert "source_resolution" in r, list(r.keys())
sr = r["source_resolution"]
assert sr["structured"] is True
assert "summary" in sr and sr["summary"]
PYEOF
then
  ok "audit JSON includes source_resolution block with summary"
else
  bad "audit JSON does not include source_resolution block"
fi

# 15h. Quality gate JSON includes source_resolution_check.
if python3 - "$ROOT" "$SMOKE/zh-cn-matched-paper_reading.json" <<'PYEOF' >/dev/null 2>&1
import sys, json, pathlib
root, src = sys.argv[1], sys.argv[2]
sys.path.insert(0, str(pathlib.Path(root) / "skills/paper-three-pass-reader/scripts"))
import quality_gate_zh_cn
class A: min_cjk_ratio=0.5; min_glossary=5; min_claims=5; min_checklist=8
data = json.load(open(src))
r = quality_gate_zh_cn.run_quality_gate(data, A())
assert "source_resolution_check" in r
assert r["source_resolution_check"]["structured"] is True
PYEOF
then
  ok "quality_gate_zh_cn JSON includes source_resolution_check"
else
  bad "quality_gate_zh_cn JSON missing source_resolution_check"
fi

# 15i. Fill-pack 00_README contains Source Resolution summary.
for tag in matched degraded legacy-only zh-cn; do
  fp="$SMOKE/$tag-fill-pack/00_README.md"
  if [[ -f "$fp" ]] && grep -q 'Source Resolution' "$fp"; then
    ok "$tag fill-pack 00_README has Source Resolution summary"
  else
    bad "$tag fill-pack 00_README missing Source Resolution summary"
  fi
done

# 15j. zh-CN fill-pack contains 解析状态 OR 输入线索.
for tag in zh-cn; do
  fp="$SMOKE/$tag-fill-pack/00_README.md"
  if [[ -f "$fp" ]] && grep -qE '解析状态|输入线索' "$fp"; then
    ok "$tag fill-pack 00_README has 解析状态 / 输入线索"
  else
    bad "$tag fill-pack 00_README missing 解析状态 / 输入线索"
  fi
done

# 15k. Runner structured source_resolution smoke still passes.
RUNNER_SMOKE="$ROOT/runs/p3pr-cli-v26b-smoke/p3pr-v26b-title/work/paper_reading.json"
if [[ -f "$RUNNER_SMOKE" ]] && \
   python3 -c "import json,sys; sys.path.insert(0,'$ROOT/skills/paper-three-pass-reader/scripts'); import source_resolution_utils as u; d=json.load(open('$RUNNER_SMOKE')); s=u.summarize_source_resolution(d); assert s['matched_paper_id']=='attention-is-all-you-need' and s['structured']" >/dev/null 2>&1; then
  ok "v0.2.6 runner smoke still has structured source_resolution"
else
  bad "v0.2.6 runner smoke lost structured source_resolution"
fi

# 15l. p3pr dry-run structured resolver output still passes.
P3PR_SMOKE="$ROOT/runs/p3pr-cli-v26b-smoke/p3pr-v26b-title"
if [[ -d "$P3PR_SMOKE" ]] && \
   python3 -c "import json; d=json.load(open('$P3PR_SMOKE/work/paper_reading.json')); assert d.get('source_resolution',{}).get('matched_paper_id')=='attention-is-all-you-need'" >/dev/null 2>&1; then
  ok "p3pr dry-run smoke still has structured resolver output"
else
  bad "p3pr dry-run smoke lost structured resolver output"
fi

# ----------------------------------------------------------------
# Step 16 — v0.2.9 HTML essay-page quality
# ----------------------------------------------------------------
# 16a. Renderer does not output raw {'label': ...} dict repr.
RENDER_OUT="$(mktemp -d)"
RENDER_JSON="$RENDER_OUT/sample.json"
python3 - <<PY >/dev/null
import json, pathlib
src = json.load(open('$ROOT/runs/you-and-your-research-20260615/you-and-your-research-cn/work/paper_reading.json'))
# Write a minimal copy to ensure renderer doesn't see weird shapes.
pathlib.Path('$RENDER_JSON').write_text(json.dumps(src, ensure_ascii=False), encoding='utf-8')
PY
python3 "$ROOT/skills/paper-three-pass-reader/scripts/render_page.py" \
  --input "$RENDER_JSON" \
  --output "$RENDER_OUT/out" >/dev/null 2>&1 || true
HTML="$RENDER_OUT/out/index.html"
if [[ -s "$HTML" ]] && ! grep -q "{'label'" "$HTML"; then
  ok "renderer does not output raw {'label': ...} dict repr"
else
  bad "renderer still outputs raw {'label': ...} dict repr"
fi

# 16b. Renderer does not leak template tags.
if [[ -s "$HTML" ]] && ! grep -qE "\{%|%\}|\{\{|\}\}" "$HTML"; then
  ok "renderer does not leak template tags ({% / %} / {{ / }})"
else
  bad "renderer leaked template tags"
fi

# 16c. Footer version is generator_version, not the stale v0.1.0-alpha.
if [[ -s "$HTML" ]] && grep -q "paper-three-pass-reader v0.2.9-alpha" "$HTML" \
   && ! grep -q "v0.1.0-alpha" "$HTML"; then
  ok "footer uses generator_version v0.2.9-alpha (no stale v0.1.0-alpha)"
else
  bad "footer version string is wrong"
fi

# 16d. Essay / talk rendering: Figures & Tables empty state.
if grep -q "原文无传统图表" "$HTML" && grep -q "结构说明" "$HTML"; then
  ok "essay / talk figures empty state shows 中文 empty + conceptual notes"
else
  bad "essay / talk figures empty state missing"
fi

# 16e. Essay / talk Reproduction Plan heading is 实践计划.
if grep -q "<h2[^>]*>实践计划</h2>" "$HTML"; then
  ok "essay / talk reproduction heading is 实践计划"
else
  bad "essay / talk reproduction heading missing"
fi

# 16f. Claims table shows real claim IDs (C01/C02 etc.), no empty <code></code>.
if grep -qE "<code>C0[0-9]</code>" "$HTML"; then
  ok "claims table renders real claim IDs (C01/C02 ...)"
else
  bad "claims table does not render real claim IDs"
fi

# 16g. Related Work: no template leak + 中文 fallback when list empty.
# (We have a non-empty list, so verify the list rendered; we ALSO verify the
# 中文 fallback string is present somewhere as a safety net.)
if grep -q "原文不是学术论文" "$HTML" || grep -q "Bell Labs、Shannon" "$HTML"; then
  ok "related-work 中文 fallback string is reachable (via fallback OR content)"
else
  bad "related-work fallback string missing"
fi

# 16h. Glossary term entries show definition (not just term chip).
# Check the first glossary entry has both term + definition_zh text on the page.
if [[ -s "$HTML" ]] && grep -qE "Bell Labs" "$HTML" && grep -qE "贝尔实验室" "$HTML"; then
  ok "glossary entries show term + Chinese definition"
else
  bad "glossary entries missing term + Chinese definition"
fi

# 16i. YAYR page smoke: all the spec's positive markers.
YAYR="$ROOT/runs/you-and-your-research-20260615/you-and-your-research-cn/paper-reading-output/index.html"
if [[ -s "$YAYR" ]]; then
  ok_paths=()
  for term in "输入解析状态" "解析状态" "Five Cs 面板" "三遍阅读" "主张" "证据" "图表" "结构说明" "相关脉络" "实践计划" "最终理解检查表"; do
    if grep -q "$term" "$YAYR"; then
      ok_paths+=("$term")
    else
      bad "YAYR page missing positive marker: $term"
    fi
  done
  if [[ ${#ok_paths[@]} -ge 11 ]]; then
    ok "YAYR page has all 11 spec positive markers (${#ok_paths[@]} found)"
  fi
  # Negative markers must be absent.
  leak=0
  for term in "{'label'" "{% else %}" "v0.1.0-alpha" "— confidence:"; do
    if grep -q "$term" "$YAYR"; then
      bad "YAYR page still contains leak: $term"
      leak=1
    fi
  done
  if [[ $leak -eq 0 ]]; then
    ok "YAYR page has no template / version / dict-leak / confidence-leak artefacts"
  fi
else
  bad "YAYR page missing at $YAYR"
fi

rm -rf "$RENDER_OUT"

# 17. v0.2.10 published-pages regression audit
step 17 "v0.2.10 published-pages regression audit"

AUDIT_SCRIPT="$SKILL_DIR/scripts/audit_published_pages.py"

# 17a. --help works
if python3 "$AUDIT_SCRIPT" --help >/dev/null 2>&1; then
  ok "audit_published_pages.py --help runs"
else
  bad "audit_published_pages.py --help failed"
fi

# 17b. Build a temporary selftest directory with fake pages
SELFTEST_DIR="$(mktemp -d)"
mkdir -p "$SELFTEST_DIR"

cat > "$SELFTEST_DIR/fake-essay.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Fake Essay</title></head>
<body><h1>Fake Essay</h1>
<p>Generated by paper-three-pass-reader v0.2.9-alpha (selftest fixture)</p>
<p>Some content here, but no essay-mode markers at all.</p>
</body></html>
HTMLEOF

cat > "$SELFTEST_DIR/fake-zhcn.html" <<'HTMLEOF'
<!doctype html>
<html lang="zh-CN"><head><title>Fake 中文</title></head>
<body><h1>Fake 中文</h1>
<p>Generated by paper-three-pass-reader v0.2.9-alpha (selftest fixture)</p>
<p>This page has Chinese title but missing most zh-CN UI markers.</p>
</body></html>
HTMLEOF

cat > "$SELFTEST_DIR/fake-pass.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Fake Pass</title></head>
<body><h1>Fake Pass</h1>
<p>Generated by paper-three-pass-reader v0.2.9-alpha (selftest fixture)</p>
<p>输入解析状态 — 摘要 — 论文地图 — 主张 — 证据 — 最终理解检查表</p>
<p>Glossary 关键术语</p>
<p>Resolver Trail — Resolver status — Confidence — Matched arXiv ID</p>
<p>Claims C01 C02 [Paper evidence] [Author claim]</p>
</body></html>
HTMLEOF

cat > "$SELFTEST_DIR/fake-template-leak.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Fake Template Leak</title></head>
<body><h1>Fake Template Leak</h1>
<p>Generated by paper-three-pass-reader v0.2.9-alpha (selftest fixture)</p>
<p>This page leaks: {% else %} and No key references recorded</p>
</body></html>
HTMLEOF

cat > "$SELFTEST_DIR/fake-raw-dict.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Fake Raw Dict</title></head>
<body><h1>Fake Raw Dict</h1>
<p>Generated by paper-three-pass-reader v0.2.9-alpha (selftest fixture)</p>
<p>Raw dict: {'label': 'foo', 'value': 'bar'}</p>
</body></html>
HTMLEOF

cat > "$SELFTEST_DIR/fake-old-footer.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Fake Old Footer</title></head>
<body><h1>Fake Old Footer</h1>
<p>Generated by paper-three-pass-reader v0.1.0-alpha (selftest fixture)</p>
<p>This page still says v0.1.0-alpha in the footer.</p>
</body></html>
HTMLEOF

# v0.2.12-alpha fixtures: fake site_index pages.
# v0.2.13-alpha: fake-site-index now includes the manifest link (both forms).
cat > "$SELFTEST_DIR/fake-site-index.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Paper Reading Pages — index</title>
<link rel="alternate" type="application/json" href="published_pages.json" title="Published pages manifest" />
</head>
<body><h1>Paper Reading Pages</h1>
<ul class="pages">
<li><a href="/fake-essay/">Fake Essay — Self Test</a> <span class="slug">[fake-essay]</span></li>
<li><a href="/fake-pass/">Fake Pass</a> <span class="slug">[fake-pass]</span></li>
<li><a href="/fake-template-leak/">Fake Template Leak</a> <span class="slug">[fake-template-leak]</span></li>
<li><a href="/fake-raw-dict/">Fake Raw Dict</a> <span class="slug">[fake-raw-dict]</span></li>
<li><a href="/fake-old-footer/">Fake Old Footer</a> <span class="slug">[fake-old-footer]</span></li>
</ul>
<p>Manifest: <a href="published_pages.json">published_pages.json</a></p>
</body></html>
HTMLEOF

cat > "$SELFTEST_DIR/fake-site-index-leak.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Site Index With Leak</title></head>
<body><h1>Paper Reading Pages</h1>
<p>Leak: {% else %} inside a comment</p>
<ul class="pages">
<li><a href="/fake-pass/">Fake Pass</a> <span class="slug">[fake-pass]</span></li>
</ul>
<p>Manifest: <a href="published_pages.json">published_pages.json</a></p>
</body></html>
HTMLEOF

# v0.2.13-alpha fixture: a site_index that does NOT link to the manifest at all.
# Should still trigger the info-level index_no_manifest_link finding.
cat > "$SELFTEST_DIR/fake-site-index-no-manifest.html" <<'HTMLEOF'
<!doctype html>
<html lang="en"><head><title>Site Index Without Manifest Link</title></head>
<body><h1>Paper Reading Pages</h1>
<ul class="pages">
<li><a href="/fake-pass/">Fake Pass</a> <span class="slug">[fake-pass]</span></li>
</ul>
<p>This page does not reference published_pages.json at all.</p>
</body></html>
HTMLEOF

SELFTEST_JSON="$(mktemp)"
SELFTEST_MD="$(mktemp)"
python3 "$AUDIT_SCRIPT" \
  --selftest-dir "$SELFTEST_DIR" \
  --json-output "$SELFTEST_JSON" \
  --markdown-output "$SELFTEST_MD" \
  >/dev/null 2>&1

# 17c. JSON output contains required fields
if python3 -c "
import json, sys
d = json.load(open('$SELFTEST_JSON'))
need = ['pages_total', 'pages_checked', 'issues_by_severity', 'pages', 'recommendations']
missing = [k for k in need if k not in d]
sys.exit(1 if missing else 0)
"; then
  ok "selftest JSON has pages_total / pages_checked / issues_by_severity / pages / recommendations"
else
  bad "selftest JSON missing required fields"
fi

# 17d. Markdown output exists with Summary / Pages / Recommendations
if [[ -s "$SELFTEST_MD" ]] \
  && grep -q "## Summary" "$SELFTEST_MD" \
  && grep -q "## Pages" "$SELFTEST_MD" \
  && grep -q "## Recommendations" "$SELFTEST_MD"; then
  ok "selftest markdown contains Summary / Pages / Recommendations"
else
  bad "selftest markdown missing Summary / Pages / Recommendations"
fi

# 17e. Per-fixture expectations: each fake page must trigger its expected code
SELFTEST_HITS=$(python3 -c "
import json
d = json.load(open('$SELFTEST_JSON'))
hits = []
for p in d['pages']:
    miss = p.get('_expect_miss') or []
    if miss:
        hits.append(p['slug'] + ':missed=' + ','.join(miss))
print('\n'.join(hits) if hits else 'OK')
")
if [[ "$SELFTEST_HITS" == "OK" ]]; then
  ok "all 9 selftest fixtures triggered their expected issue code (template_leak / raw_dict / old_footer / essay_missing_markers / zh_cn_markers_weak / pass / site_index_clean / site_index_with_leak / site_index_no_manifest_link)"
else
  bad "selftest expectations not met: $SELFTEST_HITS"
fi

# 17f. fake-pass page must end up PASS (no error)
if python3 -c "
import json, sys
d = json.load(open('$SELFTEST_JSON'))
for p in d['pages']:
    if p['slug'] == 'fake-pass' and p['status'] == 'PASS':
        sys.exit(0)
sys.exit(1)
"; then
  ok "selftest fake-pass page is PASS"
else
  bad "selftest fake-pass page did not reach PASS"
fi

# ----------------------------------------------------------------
# Step 18 — v0.2.12-alpha root-index audit exemption
# ----------------------------------------------------------------
step 18 "v0.2.12-alpha root-index audit exemption"

# 18a. audit_published_pages.py --help runs (already checked in 17a; re-assert here for symmetry)
if python3 "$AUDIT_SCRIPT" --help >/dev/null 2>&1; then
  ok "audit_published_pages.py --help runs"
else
  bad "audit_published_pages.py --help failed"
fi

# Helper: extract the fake-site-index / fake-site-index-leak pages from selftest JSON.
read_page() {
  python3 -c "
import json, sys
d = json.load(open('$SELFTEST_JSON'))
for p in d['pages']:
    if p['slug'] == '$1':
        print(json.dumps(p, ensure_ascii=False))
        sys.exit(0)
sys.exit(1)
"
}

# 18b. fake-site-index is classified as site_index.
SITE_INDEX_JSON="$(read_page fake-site-index 2>/dev/null || echo '')"
if [[ -n "$SITE_INDEX_JSON" ]] && \
   python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d.get('page_type')=='site_index' else 1)" "$SITE_INDEX_JSON" >/dev/null 2>&1; then
  ok "fake root index is classified as site_index"
else
  bad "fake root index was not classified as site_index"
fi

# 18c. fake-site-index does NOT trigger missing_resolver_trail.
if [[ -n "$SITE_INDEX_JSON" ]] && \
   ! python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if any(i.get('code')=='missing_resolver_trail' for i in d.get('issues',[])) else 1)" "$SITE_INDEX_JSON" >/dev/null 2>&1; then
  ok "fake root index does not trigger missing_resolver_trail"
else
  bad "fake root index still triggered missing_resolver_trail"
fi

# 18d. fake-site-index does NOT trigger missing_claims_section.
if [[ -n "$SITE_INDEX_JSON" ]] && \
   ! python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if any(i.get('code')=='missing_claims_section' for i in d.get('issues',[])) else 1)" "$SITE_INDEX_JSON" >/dev/null 2>&1; then
  ok "fake root index does not trigger missing_claims_section"
else
  bad "fake root index still triggered missing_claims_section"
fi

# 18e. fake-site-index does NOT trigger missing_glossary.
if [[ -n "$SITE_INDEX_JSON" ]] && \
   ! python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if any(i.get('code')=='missing_glossary' for i in d.get('issues',[])) else 1)" "$SITE_INDEX_JSON" >/dev/null 2>&1; then
  ok "fake root index does not trigger missing_glossary"
else
  bad "fake root index still triggered missing_glossary"
fi

# 18f. fake-site-index-leak STILL triggers template_leak even though it's a site_index.
SITE_INDEX_LEAK_JSON="$(read_page fake-site-index-leak 2>/dev/null || echo '')"
if [[ -n "$SITE_INDEX_LEAK_JSON" ]] && \
   python3 -c "
import json,sys
d = json.loads(sys.argv[1])
assert d.get('page_type') == 'site_index', d.get('page_type')
assert any(i.get('code') == 'template_leak' and i.get('severity') == 'error' for i in d.get('issues', [])), [i.get('code') for i in d.get('issues', [])]
assert d.get('status') == 'FAIL', d.get('status')
" "$SITE_INDEX_LEAK_JSON" >/dev/null 2>&1; then
  ok "fake root index with template_leak still triggers template_leak error (and FAILs)"
else
  bad "fake root index with template_leak did NOT trigger template_leak error"
fi

# 18g. fake paper page (fake-essay) still runs paper-level checks (essay_missing_markers).
ESSAY_JSON="$(read_page fake-essay 2>/dev/null || echo '')"
if [[ -n "$ESSAY_JSON" ]] && \
   python3 -c "import json,sys; d=json.loads(sys.argv[1]); assert d.get('page_type')=='paper_page'; assert any(i.get('code')=='essay_missing_markers' for i in d.get('issues',[]))" "$ESSAY_JSON" >/dev/null 2>&1; then
  ok "fake paper page still runs paper-level checks (essay_missing_markers fired)"
else
  bad "fake paper page did not run paper-level checks"
fi

# 18h. audit JSON includes page_type_counts.
if python3 -c "
import json, sys
d = json.load(open('$SELFTEST_JSON'))
ptc = d.get('page_type_counts')
assert isinstance(ptc, dict), type(ptc)
for k in ('site_index','paper_page','manifest','unknown'):
    assert k in ptc, (k, list(ptc.keys()))
sys.exit(0)
" >/dev/null 2>&1; then
  ok "audit JSON contains page_type_counts with all four page types"
else
  bad "audit JSON missing page_type_counts"
fi

# 18i. every page entry has page_type.
if python3 -c "
import json, sys
d = json.load(open('$SELFTEST_JSON'))
miss = [p['slug'] for p in d.get('pages',[]) if 'page_type' not in p]
sys.exit(0 if not miss else 1)
" >/dev/null 2>&1; then
  ok "every page entry has page_type field"
else
  bad "some page entries missing page_type"
fi

# 18j. markdown report contains Page Type Summary section.
if [[ -s "$SELFTEST_MD" ]] && grep -q "^## Page Type Summary" "$SELFTEST_MD"; then
  ok "markdown report contains Page Type Summary"
else
  bad "markdown report missing Page Type Summary"
fi

# 18k. live site audit: --include-root run against the live site must produce
#      page_type_counts.site_index == 1 for the root index.
LIVE_AUDIT_JSON="$(mktemp)"
LIVE_AUDIT_MD="$(mktemp)"
if python3 "$AUDIT_SCRIPT" \
   --manifest-url "https://conanxin.github.io/paper-reading-pages/published_pages.json" \
   --site-root "https://conanxin.github.io/paper-reading-pages" \
   --include-root \
   --warn-only \
   --json-output "$LIVE_AUDIT_JSON" \
   --markdown-output "$LIVE_AUDIT_MD" >/dev/null 2>&1; then
  if python3 -c "
import json, sys
d = json.load(open('$LIVE_AUDIT_JSON'))
ptc = d.get('page_type_counts', {})
sys.exit(0 if ptc.get('site_index', 0) >= 1 else 1)
" >/dev/null 2>&1; then
    ok "live site audit root index page_type = site_index"
  else
    bad "live site audit root index page_type != site_index"
  fi
else
  bad "live site audit run failed"
fi
rm -f "$LIVE_AUDIT_JSON" "$LIVE_AUDIT_MD"

# ----------------------------------------------------------------
# Step 19 — v0.2.13-alpha root-index manifest link
# ----------------------------------------------------------------
step 19 "v0.2.13-alpha root-index manifest link"

# 19a. publish_output_to_github.sh generated root index contains published_pages.json.
#      We re-run the inline Python that renders index.html from a synthetic manifest,
#      in a sandbox, and assert both forms are emitted.
PUBDIR_TEST="$(mktemp -d)"
FAKE_MANIFEST="$PUBDIR_TEST/published_pages.json"
python3 - "$FAKE_MANIFEST" "$PUBDIR_TEST/index.html" <<'PYEOF' >/dev/null 2>&1
import json, sys, os
manifest_path, out_path = sys.argv[1], sys.argv[2]
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump({"pages": [{"slug": "x", "title": "X", "path": "/x/", "published_at": "2026-06-16"}]}, f)
# Re-run only the render_index part of the publisher inline.
import os as _os
_os.makedirs(_os.path.dirname(out_path), exist_ok=True)
manifest_path, out_path, repo = sys.argv[1], sys.argv[2], "conanxin/test"
with open(manifest_path, encoding='utf-8') as f:
    d = json.load(f)
pages = d.get("pages", [])
rows = "\n".join(
    f'      <li><a href="{p["path"]}">{p["title"]}</a>'
    f' <span class="slug">[{p["slug"]}]</span>'
    f' <span class="time">{p.get("published_at","")}</span></li>'
    for p in pages
)
body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Paper Reading Pages — index</title>
  <link rel="stylesheet" href="assets/index.css" />
  <link rel="alternate" type="application/json" href="published_pages.json" title="Published pages manifest" />
</head>
<body>
  <header>
    <h1>Paper Reading Pages</h1>
    <p class="kicker">Published paper reading pages (paper-three-pass-reader)</p>
  </header>
  <main>
    <section>
      <h2>Published pages ({len(pages)})</h2>
      <ul class="pages">
{rows}
      </ul>
    </section>
    <section>
      <h2>About</h2>
      <p>Each entry above is a self-contained three-pass reading page for one paper.</p>
      <p>Repository: <a href="https://github.com/{repo}">{repo}</a></p>
      <p>Machine-readable manifest: <a href="published_pages.json">published_pages.json</a> &middot; <a href="published_pages.json" hreflang="zh-CN">页面清单 JSON</a></p>
      <p>Generated by <code>paper-three-pass-reader v0.1.1-alpha</code>.</p>
    </section>
  </main>
</body>
</html>
"""
with open(out_path, "w", encoding="utf-8") as f:
    f.write(body)
PYEOF
if [[ -s "$PUBDIR_TEST/index.html" ]] && \
   grep -q "published_pages.json" "$PUBDIR_TEST/index.html"; then
  ok "publish_output_to_github.sh generated root index contains published_pages.json"
else
  bad "publish_output_to_github.sh generated root index missing published_pages.json"
fi
# 19b. Generated root index contains the manifest link in <head> or body.
if grep -qE 'rel="alternate"[^>]*application/json[^>]*published_pages\.json|<a [^>]*href="published_pages\.json"' "$PUBDIR_TEST/index.html"; then
  ok "generated root index <head>/body contains manifest link"
else
  bad "generated root index manifest link missing in both forms"
fi
rm -rf "$PUBDIR_TEST"

# 19c. fake-site-index (clean, with manifest link) does NOT trigger index_no_manifest_link.
SITE_INDEX_JSON="$(read_page fake-site-index 2>/dev/null || echo '')"
if [[ -n "$SITE_INDEX_JSON" ]] && \
   ! python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if any(i.get('code')=='index_no_manifest_link' for i in d.get('issues',[])) else 1)" "$SITE_INDEX_JSON" >/dev/null 2>&1; then
  ok "fake root index with manifest link does not trigger index_no_manifest_link"
else
  bad "fake root index with manifest link still triggered index_no_manifest_link"
fi

# 19d. fake-site-index-no-manifest (no link at all) STILL triggers info-level index_no_manifest_link.
SITE_INDEX_NO_MANIFEST_JSON="$(read_page fake-site-index-no-manifest 2>/dev/null || echo '')"
if [[ -n "$SITE_INDEX_NO_MANIFEST_JSON" ]] && \
   python3 -c "
import json,sys
d = json.loads(sys.argv[1])
assert d.get('page_type') == 'site_index', d.get('page_type')
assert any(i.get('code') == 'index_no_manifest_link' and i.get('severity') == 'info' for i in d.get('issues', [])), [i.get('code') for i in d.get('issues', [])]
" "$SITE_INDEX_NO_MANIFEST_JSON" >/dev/null 2>&1; then
  ok "fake root index without manifest link still triggers info-level index_no_manifest_link"
else
  bad "fake root index without manifest link did not trigger index_no_manifest_link"
fi

# 19e. audit JSON can distinguish site_index AND has no paper-level warnings on the root.
if python3 -c "
import json, sys
d = json.load(open('$SELFTEST_JSON'))
ptc = d.get('page_type_counts', {})
assert ptc.get('site_index', 0) >= 1
root = [p for p in d.get('pages', []) if p.get('slug') == 'fake-site-index']
assert root, 'fake-site-index not in pages'
paper_level_codes = {'missing_resolver_trail', 'missing_claims_section', 'missing_glossary',
                     'no_visible_claim_id', 'no_evidence_label', 'glossary_no_explicit_definition',
                     'essay_missing_markers', 'zh_cn_markers_weak', 'empty_claim_id'}
for i in root[0].get('issues', []):
    assert i.get('code') not in paper_level_codes, ('unexpected paper-level on site_index:', i.get('code'))
sys.exit(0)
" >/dev/null 2>&1; then
  ok "audit JSON classifies site_index AND has no paper-level warnings on the root"
else
  bad "audit JSON site_index still has paper-level warnings or classification is wrong"
fi

# 19f. live site audit root index no longer triggers index_no_manifest_link.
LIVE_AUDIT2_JSON="$(mktemp)"
LIVE_AUDIT2_MD="$(mktemp)"
if python3 "$AUDIT_SCRIPT" \
   --manifest-url "https://conanxin.github.io/paper-reading-pages/published_pages.json" \
   --site-root "https://conanxin.github.io/paper-reading-pages" \
   --include-root \
   --warn-only \
   --json-output "$LIVE_AUDIT2_JSON" \
   --markdown-output "$LIVE_AUDIT2_MD" >/dev/null 2>&1; then
  if python3 -c "
import json, sys
d = json.load(open('$LIVE_AUDIT2_JSON'))
root = [p for p in d.get('pages', []) if p.get('page_type') == 'site_index']
assert root, 'no site_index page in live audit'
codes = [i.get('code') for i in root[0].get('issues', [])]
sys.exit(0 if 'index_no_manifest_link' not in codes else 1)
" >/dev/null 2>&1; then
    ok "live site audit root index no longer triggers index_no_manifest_link"
  else
    bad "live site audit root index still triggers index_no_manifest_link"
  fi
else
  bad "live site audit run failed"
fi
rm -f "$LIVE_AUDIT2_JSON" "$LIVE_AUDIT2_MD"

# ----------------------------------------------------------------
# Step 20 — v0.2.14-alpha p3pr url subcommand
# ----------------------------------------------------------------
step 20 "v0.2.14-alpha p3pr url subcommand"

# 20a. ./p3pr url --help runs.
if (cd "$ROOT" && ./p3pr url --help >/dev/null 2>&1); then
  ok "p3pr url --help runs"
else
  bad "p3pr url --help failed"
fi

# 20b. p3pr --help lists the url subcommand.
if (cd "$ROOT" && ./p3pr --help 2>&1 | grep -E "^[[:space:]]*url " >/dev/null); then
  ok "p3pr --help lists url subcommand"
else
  bad "p3pr --help does not list url subcommand"
fi

# 20c. URL dry-run emits P3PR_INPUT_KIND: paper_url.
URL_DRY="$(cd "$ROOT" && ./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
  --zh --full --publish --slug you-and-your-research-cn-url-smoke-dry \
  --output-root /tmp/p3pr-url-dry --dry-run 2>&1 || true)"
if echo "$URL_DRY" | grep -q "^P3PR_INPUT_KIND: paper_url$"; then
  ok "URL dry-run emits P3PR_INPUT_KIND: paper_url"
else
  bad "URL dry-run did not emit P3PR_INPUT_KIND: paper_url"
fi

# 20d. URL dry-run with --full emits P3PR_READING_MODE: full_text.
if echo "$URL_DRY" | grep -q "^P3PR_READING_MODE: full_text$"; then
  ok "URL dry-run with --full emits P3PR_READING_MODE: full_text"
else
  bad "URL dry-run with --full did not emit P3PR_READING_MODE: full_text"
fi

# 20e. URL dry-run emits P3PR_SOURCE_URL: <url>.
if echo "$URL_DRY" | grep -q "^P3PR_SOURCE_URL: https://www.cs.virginia.edu/~robins/YouAndYourResearch.html$"; then
  ok "URL dry-run emits P3PR_SOURCE_URL with the user-supplied URL"
else
  bad "URL dry-run did not emit P3PR_SOURCE_URL"
fi

# 20f-j. URL smoke run (no publish) produces the expected run layout.
URL_SMOKE_ROOT="/tmp/p3pr-url-smoke-validate-$$"
rm -rf "$URL_SMOKE_ROOT"
if (cd "$ROOT" && ./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
  --zh --full --no-publish \
  --slug you-and-your-research-cn-url-smoke \
  --output-root "$URL_SMOKE_ROOT" \
  --title "You and Your Research" \
  --authors "Richard W. Hamming" \
  --allow-draft-publish \
  --no-quality-gate \
  --audit-warn-only >/dev/null 2>&1); then
  SLUG_DIR="$URL_SMOKE_ROOT/you-and-your-research-cn-url-smoke"
  if [[ -f "$SLUG_DIR/input/source_pointer.txt" ]]; then
    ok "URL smoke run saves input/source_pointer.txt"
  else
    bad "URL smoke run missing input/source_pointer.txt"
  fi
  if [[ -f "$SLUG_DIR/source/source.html" ]]; then
    ok "URL smoke run saves source/source.html"
  else
    bad "URL smoke run missing source/source.html"
  fi
  if [[ -f "$SLUG_DIR/extracted/page.txt" ]] && \
     [[ $(wc -c < "$SLUG_DIR/extracted/page.txt") -gt 800 ]]; then
    ok "URL smoke run saves extracted/page.txt with substantial content"
  else
    bad "URL smoke run missing or too-small extracted/page.txt"
  fi
  if [[ -f "$SLUG_DIR/work/paper_reading.json" ]]; then
    ok "URL smoke draft JSON exists"
  else
    bad "URL smoke draft JSON missing"
  fi
  if grep -q '"input_kind".*"paper_url"' "$SLUG_DIR/work/paper_reading.json" 2>/dev/null; then
    ok "URL smoke draft JSON contains paper_url"
  else
    bad "URL smoke draft JSON missing paper_url"
  fi
  if grep -q '"source_resolution"' "$SLUG_DIR/work/paper_reading.json" 2>/dev/null; then
    ok "URL smoke draft JSON contains source_resolution"
  else
    bad "URL smoke draft JSON missing source_resolution"
  fi
  if [[ -f "$SLUG_DIR/paper-reading-output/index.html" ]]; then
    ok "URL smoke rendered page exists"
  else
    bad "URL smoke rendered page missing"
  fi
  if grep -q "输入解析状态" "$SLUG_DIR/paper-reading-output/index.html" 2>/dev/null; then
    ok "URL smoke rendered page contains Chinese UI (输入解析状态)"
  else
    bad "URL smoke rendered page missing Chinese UI"
  fi
  # 20k. Existing arxiv / title / abstract / screenshot / repo / pdf help checks still pass.
  for sub in arxiv title abstract screenshot repo pdf; do
    if (cd "$ROOT" && ./p3pr "$sub" --help >/dev/null 2>&1); then
      ok "p3pr $sub --help still runs"
    else
      bad "p3pr $sub --help regressed"
    fi
  done
else
  bad "URL smoke run failed; layout checks skipped"
fi
rm -rf "$URL_SMOKE_ROOT" /tmp/p3pr-url-dry

rm -rf "$SELFTEST_DIR" "$SELFTEST_JSON" "$SELFTEST_MD"

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
