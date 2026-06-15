# Changelog

All notable changes to `paper-three-pass-reader` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.2.3-alpha] — 2026-06-15

### Added

- **First-class Chinese (zh-CN) output support** — the runner, fill-pack, audit, and renderer all carry language fields. Pages are now fully bilingual-capable.
- **Runner language propagation** — `run_paper_reading.py` now writes `target_language` and `ui_language` to the draft JSON. Both default to whatever `--language` was passed (default `zh-CN`).
- **Renderer UI localization** — `render_page.py` reads `ui_language` and applies a deterministic English→Chinese UI label map. The map covers: section headings, key terms, evidence labels (preserved in English), tabs, accordions, all metadata labels.
- **Audit Chinese content check** — when `target_language` / `ui_language` = `zh-CN`, the audit scans 5 main interpretive fields (`summaries.one_sentence`, `pass2.main_ideas`, `pass3.method_reconstruction`, `pass3.critical_review`, `glossary.definitions`) and warns if fewer than 50% contain Chinese characters. Evidence labels, paper names, and method names in English do NOT trigger the warning.
- **Second Me Chinese full-text run** — new run directory `runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/` with 12 claims, 7 figure/table entries, 14 glossary terms, 12-item checklist. Audit: PASS, 0 errors / 0 warnings.
- **Chinese page published** — `https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/` (HTTP 200).
- **Validation extended** — `scripts/validate.sh` now has 120 checks (was 108). New step 10 covers: runner `--language` flag, zh-CN draft `target_language` / `ui_language`, Chinese fill-pack content, Chinese UI label presence, audit Chinese-content warning, Second Me zh-CN real run audit, Second Me zh-CN page label check.

### Notes

- Evidence labels remain **fixed English enums** (`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`) regardless of UI language. They are intentionally untranslatable so the audit can match them.
- Paper titles, method names, benchmark names, and author names remain in their original form (English or Chinese as the author wrote them).
- Re-rendering an `en` draft still produces an English page; the locale only kicks in when the JSON explicitly says `ui_language = "zh-CN"`.

## [v0.2.4-alpha] — 2026-06-15

### Added

- **zh-CN quality gate** — new `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`. Goes beyond "does this draft have Chinese?" to "is the Chinese explanation actually a reading?". Catches: low CJK coverage, long English blobs (carryover from English draft), too-few glossary/claims/checklist items, full_text mode with no `[Paper evidence]` claims, missing Pass 2/3 in full_text mode.
- **Audit `--quality-gate` integration** — when `target_language` / `ui_language` is `zh-CN` and the flag is passed, the audit calls the quality gate after the structural audit and exits non-zero on quality-gate FAIL. Without the flag, the audit prints a hint to re-run with `--quality-gate`.
- **Runner `--quality-gate` integration** — `run_paper_reading.py --quality-gate` (only effective with `--language zh-CN`) runs the quality gate after the audit and writes `work/quality_gate_zh_cn.json` and `reports/quality_gate_zh_cn.md`. Quality-gate FAIL blocks `--render` and `--publish` unless `--audit-warn-only` is set.
- **Fill-pack `11_zh_cn_quality_gate.md`** — new step in the agent fill pack that explains what the quality gate checks, how to fix common WARN/FAIL patterns, why evidence labels stay in English, and why "has CJK chars" is not enough.
- **Bad zh-CN sample** — `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/` for validation: declares `target_language = zh-CN` but contains English content + only 2 claims + empty glossary + 2-item checklist. Quality gate returns FAIL with 4 errors and 4 warnings. This guards against the quality gate becoming a rubber stamp.
- **Validation extended** — `scripts/validate.sh` now has 129 checks (was 120). New step 11 covers: quality-gate script help, executable, Second Me zh-CN PASS, bad sample FAIL, runner `--quality-gate` flag, audit `--quality-gate` flag, fill-pack `11_zh_cn_quality_gate.md` present, audit `--quality-gate` integration PASS, audit default hint on zh-CN run.
- **Documentation** — new `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md`. `RUNNER.md`, `AUDIT.md`, `AGENT_FILL_PACK.md`, `USAGE.md`, `README.md`, `CHANGELOG.md`, `docs/AUTOFILL_RUNS.md`, `docs/REALPAPER_RUNS.md` updated. Release notes and phase report.

### Design notes

- The quality gate is **structural + bilingual-discipline**, not LLM-truth-judging. It catches specific failure modes that "audit alone" misses but does not score translation quality subjectively.
- Evidence labels remain fixed English enums for audit compatibility. Explanatory text around them is Chinese.
- The default zh-CN thresholds (8 claims, 10 glossary, 8 checklist, 50% CJK ratio) are tuned for full_text real-paper readings, not weak-mode drafts. For weak-mode drafts, the quality gate should be run with `--warn-only`.

## [v0.2.5-alpha] — 2026-06-15

### Added

- **One-line CLI** — `p3pr` (shell shim at repo root) wraps `skills/paper-three-pass-reader/scripts/p3pr.py` (stdlib-only Python). The CLI orchestrates the existing runner / fill-pack / audit / zh-CN quality gate / renderer / publisher into a single command:
  - `./p3pr arxiv 2503.08102 --zh --full --publish`
  - `./p3pr title "Attention Is All You Need" --zh --full --publish`
  - `./p3pr abstract path/to/abstract.md --zh --publish`
  - `./p3pr screenshot path/to/transcript.md --zh --publish`
  - `./p3pr repo https://github.com/google-research/bert --zh --full --publish`
  - `./p3pr pdf path/to/paper.pdf --zh --full --publish`
- **Defaults**: `language = zh-CN`, `fill_pack = true`, `audit = true`, `quality_gate = true` (only when `language == zh-CN`), `render = true`, `publish = false`, `repo = conanxin/paper-reading-pages`, `branch = gh-pages`.
- **Boundaries enforced**: weak-mode drafts (screenshot_only / abstract_only) do NOT pretend full_text. `--publish` is BLOCKED on quality-gate FAIL unless `--allow-draft-publish` is set. `--dry-run` skips downloads / extraction.
- **Fixed-format summary** at end of every CLI run:
  `P3PR_STATUS` / `P3PR_INPUT_KIND` / `P3PR_READING_MODE` / `P3PR_RUN_DIR` / `P3PR_JSON` / `P3PR_FILL_PACK` / `P3PR_LOCAL_PAGE` / `P3PR_PAGE_URL` / `P3PR_NEXT_ACTION`.
- **CLI smoke runs** — `runs/p3pr-cli-smoke-20260615/` has 2 local smoke runs (screenshot + abstract) and 4 dry-runs (arxiv / title / repo / pdf). CLI smoke runs do not pretend full_text on weak inputs.
- **Validation extended** — `scripts/validate.sh` now has 151 checks (was 129). New step 12 covers: p3pr shim executable, p3pr help, all 6 subcommands, arxiv dry-run summary, title / repo dry-runs, screenshot smoke JSON + fill-pack, abstract smoke reading_mode, weak-input not pretending full_text.
- **Documentation** — new `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md`. `README.md`, `CHANGELOG.md`, `RUNNER.md`, `USAGE.md`, `ZH_CN_QUALITY_GATE.md` updated. Release notes and phase report.

### Design notes

- The CLI is a **thin wrapper**; it does NOT call external LLM APIs and does NOT do any deep reading. The reading is the fill-pack job.
- Subcommands share the same flag set (forwarded from parent argparse) so users can put flags before or after the subcommand.
- The CLI keeps its own copy of the resolver hints (`HINTS` dict) so dry-runs can resolve without invoking the runner.

### Changed

- `render_page.py` — `render_index` now reads `ui_language` and applies the UI map. Backward compatible: when `ui_language` is absent or `"en"`, behaviour is unchanged.
- `audit_paper_reading.py` — added step 8 (language check). Does not change PASS/WARN/FAIL semantics for `en` drafts.
- `run_paper_reading.py` — `make_draft` now writes `target_language` and `ui_language` at the top level (after `schema_version`).

### Notes

- Evidence labels remain **fixed English enums** (`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`) regardless of UI language. They are intentionally untranslatable so the audit can match them.
- Paper titles, method names, benchmark names, and author names remain in their original form (English or Chinese as the author wrote them).
- Re-rendering an `en` draft still produces an English page; the locale only kicks in when the JSON explicitly says `ui_language = "zh-CN"`.

## [v0.2.2-alpha] — 2026-06-15

### Added

- **Auto-fill smoke run** — `runs/v022-fulltext-autofill-secondme-20260615/second-me-fulltext-autofill/`. End-to-end PDF download + pdftotext extraction + runner draft + agent fill + audit + render + publish for arXiv:2503.08102 ("AI-native Memory 2.0: Second Me", Mindverse.ai).
- **Skill bug fixes** during the smoke:
  - `run_paper_reading.py` no longer `return rc` on audit FAIL when `--fill-pack` is requested (the fill-pack is the task list, must be written even when audit fails).
  - `render_page.py` now tolerates string entries in `pass2.key_references` (same pattern as `claims_evidence_map`).
- **Documentation** — `docs/AUTOFILL_RUNS.md`, `docs/PHASE_P3PR_V0_2_2_FULLTEXT_AUTO_FILL_SMOKE_REPORT.md`, `docs/RELEASE_NOTES_v0.2.2-alpha.md`.

### Notes

- No schema or page-template changes; only runner/render robustness.

## [v0.2.1-alpha] — 2026-06-15

### Added

- **Agent Fill Pack** — new `--fill-pack` flag on the runner. Generates 11 markdown files (`00_README.md` through `10_quality_gate.md`) plus `prompts.json`, `field_checklist.json`, and `draft_status.json` inside `<run_dir>/fill-pack/`. Step instructions adapt to the current reading mode (weak modes carry explicit "weak-input" caveats).
- **Structural audit** — new `skills/paper-three-pass-reader/scripts/audit_paper_reading.py`. Checks JSON shape, enum validity, reading-mode discipline (no over-claims in weak modes), claims-evidence whitelist, and final_checklist counts. Output is a JSON document + markdown summary.
- **Runner audit integration** — `--audit` flag invokes the audit after the draft is written. If audit status is FAIL, the runner refuses to render or publish (relax with `--audit-warn-only`).
- **Runner profile + language** — `--agent-profile` (default / strict / beginner / researcher / engineer), `--language` (zh-CN / en), `--max-claims`, `--max-figures`.
- **Docs** — `skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md`, `skills/paper-three-pass-reader/docs/AUDIT.md`. RUNNER.md / USAGE.md / OUTPUT_SCHEMA.md extended with v0.2.1 sections.
- **Validation** — `scripts/validate.sh` extended to 108 checks across 9 steps, covering the new flags, scripts, and 3 reading-mode smoke runs (title / abstract / screenshot).

### Notes

- The audit is **structural + reading-mode discipline** only. It does not judge whether the paper's content is correct.
- The fill pack is **task instructions**, not auto-filling. It does not call any external LLM API.

## [v0.2.0-alpha] — 2026-06-15

### Added

- **One-command runner** — `skills/paper-three-pass-reader/scripts/run_paper_reading.py`.
  - Turns any paper-shaped input (title, abstract, OCR transcript, repo URL, etc.) into a standard run directory + draft `paper_reading.json` + (optional) rendered page + (optional) published GitHub Page.
  - Stdlib only. No external LLM API.
  - Built-in resolver hints for a handful of well-known papers (Attention, BERT, How to Read a Paper, this repo) — for smoke testing and for the most common canonical inputs. No network search.
  - Strict reading-mode discipline: `paper_excerpt` always forces `abstract_only`; `paper_screenshot` always forces `screenshot_only`; the user's `--reading-mode` override wins over both the input-kind-forced mode and the hint default.
  - Unknown inputs become `ambiguous_clue` drafts with `needs_confirmation = true` and `confidence = low` — never silently guessed.
  - Drafts are explicitly marked with `[DRAFT]` placeholders so the operator knows what to fill in.
  - New docs: `skills/paper-three-pass-reader/docs/RUNNER.md`.

### Changed (validation)

- `scripts/validate.sh` gained an 8th step ("v0.2 runner") with 6 new smoke checks:
  1. Runner script exists and is executable.
  2. `runner --help` exits 0.
  3. title-only smoke run produces `work/paper_reading.json`.
  4. abstract_only smoke page contains `abstract_only`.
  5. screenshot_only smoke page contains `screenshot_only`.
  6. sample render still passes.
- Total: **74 PASS / 0 FAIL**.

### Changed (docs)

- `README.md` / `README.zh-CN.md`: added a "One-command runner" section and a v0.2.0-alpha row in the version history.
- `CHANGELOG.md`: new v0.2.0-alpha section.
- New `docs/RELEASE_NOTES_v0.2.0-alpha.md`.
- New `docs/PHASE_P3PR_V0_2_RUNNER_1_REPORT.md`.

### Smoke runs

The runner was smoke-tested with three local runs under `runs/runner-smoke-20260615/`:

- `runner-title-attention` (input kind: `paper_title` → `reading_mode = full_text`)
- `runner-abstract-keshav` (input kind: `paper_excerpt` → `reading_mode = abstract_only`)
- `runner-screenshot-keshav` (input kind: `paper_screenshot` → `reading_mode = screenshot_only`)

`runner-title-attention` was also published to https://conanxin.github.io/paper-reading-pages/runner-title-attention/ as part of validation.

### No changes to

- The three-pass reading design.
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape.
- The `v0.1.0-alpha` / `v0.1.1-alpha` / `v0.1.2-alpha` tags or releases (kept untouched).

## [v0.1.2-alpha] — 2026-06-15

### Fixed

- **`publish_output_to_github.sh` in multi-page index mode.** The cleanup step that runs when both `--site-path` and `--page-title` are passed previously used a `find … -exec rm` pattern that wiped **all** non-infrastructure root entries — including sibling per-page subdirectories. After this fix, the cleanup only removes known-stale files left over from prior single-page deploys (`README.md`, `data/`, `reports/`, `index.html.bak`, `README.zh-CN.md`). Other published-page subdirectories are preserved across re-publishes.

### Why a new release, not a tag rewrite

- `v0.1.1-alpha` was already published (annotated tag `f30f21b` → commit `00ba84f`). The fix commit (`ffa3fd4`) landed on `main` after that release.
- This project treats published tags as immutable: no force-move, no force-push, no history rewrite.
- The fix is therefore released as `v0.1.2-alpha` (annotated tag → current `main` HEAD). `v0.1.1-alpha` remains exactly where it was.

### No changes to

- The three-pass reading design.
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape.
- The `v0.1.0-alpha` tag or release.
- The `v0.1.1-alpha` tag or release (kept untouched).

### Verified live after release

- `https://conanxin.github.io/paper-reading-pages/` — root index, HTTP 200, 1044 bytes.
- `https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/` — slug page, HTTP 200, 44 439 bytes.
- `https://conanxin.github.io/paper-reading-pages/published_pages.json` — manifest, HTTP 200, 237 bytes.

### Validation

`scripts/validate.sh` still PASSes 68 / 0 (no change to validation suite for v0.1.2).

## [v0.1.1-alpha] — 2026-06-15

### Changed (hardening)

- **Renderer is now defensively normalised.** `render_page.py` accepts `claims_evidence_map`, `figures_tables`, `glossary`, and `final_checklist` entries that are plain strings, missing fields, or have invalid enum values. All are coerced into safe dicts with sensible defaults; invalid evidence labels are downgraded to `[Uncertain]`; invalid confidence values become `low`. The page never crashes on a malformed entry.
- **`figures_tables` no longer crashes on string entries.** Strings become `{kind: "note", evidence_label: "[Uncertain]", explanation: <original>}`. Empty titles get a placeholder.
- **`claims_evidence_map` accepts strings as claims.** Each string becomes a single-row claim with `confidence: low`, `needs_verification: true`, `evidence_label: [Uncertain]`.
- **`final_checklist` accepts strings as questions.** Each string becomes `{question: <string>, answerable: true}`.
- **`pass1.decision` is validated** against the four legal values; anything else falls back to `CONTINUE_FULL`.
- **`paper_metadata.reading_mode` and `intake_quality.reading_mode` are validated** against the four legal modes; anything else falls back to `full_text`.
- **`data/` mirrors now include `glossary.json` and `final_checklist.json`** in addition to the previous seven files.
- **`render_page.py` report generators** (`pass2_figures_tables.md`, `pass2_claims_evidence_map.md`) no longer crash on string entries — they coerce on the fly.

### Added (publish script)

- **`publish_output_to_github.sh` supports `--site-path` and `--page-title`** for multi-page publishing. In multi-page mode the output dir is copied into `<branch>/<site-path>/` and other published pages are preserved.
- **Root `index.html` regenerated** from a `published_pages.json` manifest when `--site-path` + `--page-title` are passed. Existing entries are upserted by slug; the manifest is sorted by `published_at`.
- **Root branch cleanup in index mode** automatically removes stale `data/`, `reports/`, top-level `README.md`, etc. (anything not in the allowed infrastructure set: `.nojekyll`, `assets/`, `index.html`, `published_pages.json`, per-page subdirs).
- **`--check` mode** now also reports that `--site-path` and `--page-title` are supported.
- **URL echo** is now computed correctly: `https://<owner>.github.io/<repo>/<site-path>/` (was previously a `sed` mess that produced broken URLs).

### Changed (validation)

- **`scripts/validate.sh` gained a 7th step** ("v0.1.1 hardening") with four new smoke checks:
  1. `render_page.py` handles `figures_tables` string entries without crashing.
  2. Publish-script help advertises `--site-path`.
  3. Publish-script help advertises `--page-title`.
  4. Publish-script `--check` exits 0.
  5. The Attention run re-renders cleanly.
- Existing 6 steps are unchanged. Total: 68 PASS / 0 FAIL.

### Changed (docs)

- `README.md` / `README.zh-CN.md`: added v0.1.1 to the version footer, added a short "Multi-page publishing" section.
- `skills/paper-three-pass-reader/docs/GITHUB_PAGES_PUBLISHING.md`: added "Multi-page mode" with `--site-path` / `--page-title` examples.
- `skills/paper-three-pass-reader/docs/USAGE.md`: added slug-publish example.
- `docs/REALPAPER_RUNS.md`: bumped `LOCAL_OUTPUT_PATH` and `GITHUB_PAGES` to reflect the slug URL.
- New `docs/RELEASE_NOTES_v0.1.1-alpha.md`.
- New `docs/PHASE_P3PR_0_1_1_REALPAPER_HARDENING_REPORT.md`.

### No changes to

- The three-pass reading design.
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape (additive only — the new fields are `glossary.json` and `final_checklist.json` mirrors).
- The `v0.1.0-alpha` tag and release.

## [v0.1.0-alpha] — 2026-06-15

### Added

- **Stage 0 — Paper Intake and Resolution.** Normalises any of: complete paper (PDF / text / LaTeX / HTML), paper URL (arXiv, DOI, OpenReview, ACM/IEEE/Springer/Nature/ScienceDirect, PubMed/bioRxiv/medRxiv), paper identifier (arXiv ID, DOI), paper title, paper metadata (title + author + year + venue), paper excerpt (abstract / intro / conclusion / BibTeX / citation), paper image / screenshot (title page / abstract / figure / table / slide / poster / photo), paper topic clue, GitHub repo, project page, and ambiguous social-media clue into a canonical paper record.
- **Reading modes.** Every run is explicitly tagged `full_text`, `partial_text`, `abstract_only`, or `screenshot_only` — the skill never pretends to have read more than it has.
- **Stage 1 — First Pass with Five Cs.** Category, Context, Correctness, Contributions, Clarity, plus an explicit *continue-or-stop* decision.
- **Stage 2 — Second Pass.** Main ideas, figures & tables, key references, and the **Claims → Evidence map**: every load-bearing claim paired with the figure/table/section that grounds it.
- **Stage 3 — Third Pass.** Method reconstruction, critical review, and a concrete **reproduction plan** an engineer could actually follow.
- **Interactive HTML reading page.** Hero summary, paper metadata, intake status, 1/3/10-sentence summaries, paper map, Five Cs dashboard, Pass 1/2/3 tabs, Claims-Evidence map (filterable), Figures & Tables, Glossary, Method Reconstruction, Limitations, Related Work, Reproduction Plan, Open Questions, and a "Do I understand this paper?" checklist. Tabs, accordions, claim filter, confidence labels, reading-mode badge, evidence labels, progress timeline, glossary chips. **Local-only, no backend, no external assets.**
- **Evidence discipline.** Every interpretive statement carries one of `[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`.
- **Three scripts.**
  - `render_page.py` — JSON → interactive HTML page (stdlib only).
  - `create_output_skeleton.py` — generate empty `paper-reading-output/` skeleton for a new paper.
  - `publish_output_to_github.sh` — push the page to a `gh-pages` branch of an existing GitHub repo; refuses to silently create a new repo.
- **Validation.** `scripts/validate.sh` runs a smoke check: file presence, JSON validity, sample render, page-section presence.
- **Sample data.** `examples/sample_paper_reading.json` and `examples/sample_intake_quality.json` built from S. Keshav's *How to Read a Paper* (2007) — works offline, no network fetch.
- **Docs.** `README.md` (EN), `README.zh-CN.md`, `LICENSE` (MIT), `CHANGELOG.md`, `USAGE.md`, `OUTPUT_SCHEMA.md`, `GITHUB_PAGES_PUBLISHING.md`, `DESIGN_RATIONALE.md`.

### Notes

- This is an **alpha**. Inputs are normalised but PDF/HTML parsing is the caller's responsibility. The skill provides the workflow, the page, and the evidence discipline — not the text extraction pipeline.
- The Keshav sample is meta by design (we use the reading-method paper as the worked example of reading it).
- Backwards-compatibility: this is the first tagged release; no migration needed.
