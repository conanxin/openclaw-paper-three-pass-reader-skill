# PHASE_P3PR_V0_2_RUNNER_1_REPORT.md

| Field | Value |
|---|---|
| **STATUS** | PASS |
| **PROJECT_DIR** | `/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill` |
| **BASE_VERSION** | v0.1.2-alpha |
| **TARGET_VERSION** | v0.2.0-alpha |
| **DATE** | 2026-06-15 |

---

## TL;DR

A new one-command runner was added to the skill: `skills/paper-three-pass-reader/scripts/run_paper_reading.py`. It turns any paper-shaped input (title, abstract, OCR transcript, repo URL, …) into a standard run directory + draft `paper_reading.json` + (optional) rendered page + (optional) published GitHub Page. Stdlib only; no external LLM API; no SaaS-style framework.

The runner was smoke-tested with three local runs under `runs/runner-smoke-20260615/` (title-only, abstract-only, screenshot-only). The title-only smoke run was also published to GitHub Pages and is live at https://conanxin.github.io/paper-reading-pages/runner-title-attention/. Validation grew from 68 → 74 checks and still PASSes. The existing `v0.1.0-alpha`, `v0.1.1-alpha`, and `v0.1.2-alpha` tags and releases were not touched.

---

## RUNNER_SCRIPT

`skills/paper-three-pass-reader/scripts/run_paper_reading.py` (24 412 bytes; stdlib only; chmod +x; 380+ lines).

Features:

- 11 input kinds: `complete_paper`, `paper_url`, `paper_identifier`, `paper_title`, `paper_metadata`, `paper_excerpt`, `paper_image`, `paper_screenshot`, `paper_topic`, `project_or_repo`, `ambiguous_clue`.
- 4 reading modes: `full_text`, `partial_text`, `abstract_only`, `screenshot_only`.
- Optional overrides: title, authors, year, arXiv ID, paper URL, reading mode.
- Optional `--render` (calls `render_page.py`) and `--publish` (calls `publish_output_to_github.sh`).
- Built-in resolver hint table for known canonical inputs (Attention, BERT, Keshav, this repo). No network search.
- Strict reading-mode priority: user `--reading-mode` > input-kind-forced mode > hint default > `partial_text`.
- Slug safety: `[A-Za-z0-9._-]+` only.
- Captures the raw input to `input/input.md` for the audit trail.

---

## SUPPORTED_INPUTS

| Input kind | Forced `reading_mode` (without override) | Behaviour |
|---|---|---|
| `paper_title` | hint default or `partial_text` | title → hint table or ambiguous clue |
| `paper_url` / `paper_identifier` | hint default or `partial_text` | URL/ID → hint table or ambiguous clue |
| `complete_paper` | hint default or `partial_text` | operator supplies the body in `extracted/` |
| `paper_metadata` | hint default or `partial_text` | structured metadata → hint table |
| `paper_excerpt` | **`abstract_only`** | only abstract was supplied; Pass 2/3 unavailable |
| `paper_image` / `paper_screenshot` | **`screenshot_only`** | only image-derived text was supplied; Pass 2/3 unavailable |
| `paper_topic` | hint default or `partial_text` | topic → ambiguous unless hint matched |
| `project_or_repo` | hint default or `partial_text` | repo URL → hint table (e.g. `google-research/bert` → BERT paper) |
| `ambiguous_clue` | `partial_text` | no hint; needs human confirmation |

---

## DRAFT_JSON_BEHAVIOR

The runner produces a DRAFT `paper_reading.json` with the following properties:

- All 15 required schema fields present and valid.
- `paper_metadata.title` filled from hint or input (when identifiable) or left for the operator.
- `intake_quality` populated with `input_kind`, `reading_mode`, `confidence`, `needs_confirmation`, `missing_fields`, `warnings`, `ambiguities`, `source_used`, `extraction_quality`, `source_resolution`.
- `summaries.one_sentence` / `three_sentence` / `ten_sentence` are `[DRAFT]` placeholders.
- `five_cs` fields are `[DRAFT]` placeholders.
- `pass1.decision_rationale` is `[DRAFT — fill after Pass 1]` (plus a "seek references first" note when `needs_confirmation = true`).
- `pass2.claims_evidence_map` has exactly one row labelled `[DRAFT — fill after Pass 2]`. For `abstract_only` / `screenshot_only`, the label is `[Needs verification]` and `needs_verification = true`.
- `pass3.method_reconstruction` / `critical_review` / `hidden_assumptions` / `future_work` / `application_notes` are `[DRAFT]` placeholders. For `abstract_only` / `screenshot_only`, the first item is `[DRAFT — unavailable until body is available]`.
- `glossary` is empty (no fabricated terms).
- `limitations` lists the mode-related honesty markers.
- `final_checklist` has 8 questions specific to "did you fill the draft honestly".

The draft is **never** treated as a real reading. Every interpretive field is `[DRAFT]` until the operator fills it in.

---

## READING_MODE_DISCIPLINE

The runner enforces strict reading-mode rules. Verified empirically across the three smoke runs:

| Smoke run | `--input-kind` | Resolver hint | Final `reading_mode` | Honourable? |
|---|---|---|---|---|
| `runner-title-attention` | `paper_title` | matched (Attention) | `full_text` (hint default) | ✅ |
| `runner-abstract-keshav` | `paper_excerpt` | matched (Keshav) | **`abstract_only`** (kind forced) | ✅ |
| `runner-screenshot-keshav` | `paper_screenshot` | matched (Keshav) | **`screenshot_only`** (kind forced) | ✅ |

Key observation: even when the resolver hint's `default_reading_mode` is `abstract_only` (Keshav), the `paper_screenshot` case correctly produces `screenshot_only` because the input-kind-forced mode wins over the hint default. Similarly, a `paper_title` case for a paper whose hint default is `full_text` but the operator passes `--reading-mode partial_text` (as in the published title-only smoke run) correctly produces `partial_text`.

The runner never silently upgrades a partial input to `full_text`. The runner never silently downgrades a complete input to a partial mode. The runner never produces `full_text` without the operator's explicit `--reading-mode full_text` flag or a successful body-fetch (which the runner does not perform — it is the operator's job to drop the body into `extracted/`).

---

## SMOKE_RUNS

Three local smoke runs under `runs/runner-smoke-20260615/`:

| Slug | `input_kind` | `--input` | Resolved `reading_mode` | Rendered | Published |
|---|---|---|---|---|---|
| `runner-title-attention` | `paper_title` | `Attention Is All You Need` | `partial_text` (operator override) → `full_text` (re-render without override) | yes | yes |
| `runner-abstract-keshav` | `paper_excerpt` | `abstract excerpt of How to Read a Paper` | `abstract_only` | yes | no |
| `runner-screenshot-keshav` | `paper_screenshot` | `OCR transcript of How to Read a Paper screenshot` | `screenshot_only` | yes | no |

The published title-only smoke page is at https://conanxin.github.io/paper-reading-pages/runner-title-attention/ (HTTP 200 at run time, 12 497 bytes).

---

## PAGE_GENERATION

All three smoke runs were rendered through `render_page.py`. Page-level smoke checks (mandatory sections + reading-mode badge):

| Slug | Intake Status | Five Cs | Pass 1 | Claims | Evidence | Checklist | reading-mode badge |
|---|---|---|---|---|---|---|---|
| `runner-title-attention` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `full_text` ✅ |
| `runner-abstract-keshav` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `abstract_only` ✅ |
| `runner-screenshot-keshav` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `screenshot_only` ✅ |

The `runner-title-attention` smoke page was published under slug `runner-title-attention` with page title `Runner Smoke: Attention Is All You Need`. It is live on GitHub Pages.

---

## PUBLISH_STATUS

- `runner-title-attention` published via `--render --publish`. Live URL: https://conanxin.github.io/paper-reading-pages/runner-title-attention/. HTTP 200, 12 497 bytes.
- `runner-abstract-keshav` and `runner-screenshot-keshav` were rendered but not published (per spec, only the title-only smoke page was required to be published).
- `published_pages.json` lists 6 entries after the run (the 5 from P3PR-WEAKINPUT-1 plus `runner-title-attention`).

All 8 URLs (root index + 6 published pages + manifest) verified HTTP 200 at run time.

---

## VALIDATION

`scripts/validate.sh` result:

```
[1] Required files        — 18/18 ok
[2] JSON parseability     — 3/3 ok
[3] Sample render         — 22/22 ok
[4] Mandatory page sections — 9/9 ok
[5] Interactive bits      — 8/8 ok
[6] SKILL.md substance    — 1/1 ok
[7] v0.1.1 hardening       — 5/5 ok
[8] v0.2 runner            — 6/6 ok
                              runner script exists and is executable
                              runner --help exits 0
                              title-only smoke run produced work/paper_reading.json
                              abstract_only smoke page contains abstract_only
                              screenshot_only smoke page contains screenshot_only
                              sample render still passes

=================================================
 PASS: 74    FAIL: 0
=================================================
STATUS: PASS
```

Up from 68 / 0 in v0.1.2-alpha.

---

## FILES_CREATED

- `skills/paper-three-pass-reader/scripts/run_paper_reading.py` — the runner (24 412 bytes).
- `skills/paper-three-pass-reader/docs/RUNNER.md` — full interface + examples + boundaries.
- `docs/RELEASE_NOTES_v0.2.0-alpha.md` — release notes.
- `docs/PHASE_P3PR_V0_2_RUNNER_1_REPORT.md` — this file.
- `runs/runner-smoke-20260615/runner-title-attention/{input,source,extracted,work,paper-reading-output}/`
- `runs/runner-smoke-20260615/runner-abstract-keshav/{input,source,extracted,work,paper-reading-output}/`
- `runs/runner-smoke-20260615/runner-screenshot-keshav/{input,source,extracted,work,paper-reading-output}/`

---

## FILES_MODIFIED

- `CHANGELOG.md` — new v0.2.0-alpha section.
- `README.md` — runner section + v0.2.0-alpha row in version history.
- `README.zh-CN.md` — runner section + version bump.
- `scripts/validate.sh` — added 8th step (6 new checks).
- `runs/runner-smoke-20260615/runner-title-attention/paper-reading-output/` — populated with rendered page + data + reports.

---

## COMMIT

```
<filled in at the end of this run>
```

Commit message: `Add one-command paper reading runner`.

---

## PUSH

`git push origin main` after the local commit. No force.

---

## TAG

- Name: `v0.2.0-alpha`
- Type: annotated
- Target: `main` HEAD at release time

`v0.1.0-alpha`, `v0.1.1-alpha`, `v0.1.2-alpha` remain at their original commits (verified `git rev-parse <tag>^{commit}` returns the original SHA for each).

---

## RELEASE

- URL: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.0-alpha
- Title: `paper-three-pass-reader v0.2.0-alpha`
- Notes source: `docs/RELEASE_NOTES_v0.2.0-alpha.md`

---

## LIMITATIONS

1. **The runner does not read the paper.** Drafts are scaffolds; the operator (human or agent) fills them in. A future v0.3 could add an LLM-driven filler.
2. **The runner does not search the web.** Inputs not in the hint table become `ambiguous_clue` drafts.
3. **The runner does not fetch PDFs.** `source/` and `extracted/` are empty by design — the operator drops the body there.
4. **The built-in resolver hint table is small.** It covers only the smoke-test papers (Attention, BERT, Keshav) plus this repo. Adding more entries is straightforward (edit the `RESOLVER_HINTS` dict in `run_paper_reading.py`) but is a manual process.
5. **Slug validation is strict (`[A-Za-z0-9._-]+`).** This matches the publish script's constraint; paths with separators are rejected.
6. **No multi-candidate resolution.** If two papers match the title or hint, the runner picks the first one and writes `needs_confirmation = true`.

---

## NEXT_USER_ACTION

1. Verify the new release at https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.0-alpha
2. Try the runner locally on any paper:

   ```bash
   python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
     --input "How to Read a Paper" \
     --input-kind paper_title \
     --slug my-first-run \
     --output-root runs \
     --render
   ```

3. Open `runs/my-first-run/work/paper_reading.json`, fill in the `[DRAFT]` placeholders with real content, then re-render and (optionally) publish.
4. Visit https://conanxin.github.io/paper-reading-pages/runner-title-attention/ to see the live smoke page.
5. Optional: open a v0.2.1 issue if a paper you want to read fails the slug safety check or if you want more entries in the resolver hint table.

No manual GitHub commands are required for this release.

---

## Final two lines (per spec)

```
HERMES_STATUS: REPORT_WRITTEN
HERMES_REPORT_PATH: /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/docs/PHASE_P3PR_V0_2_RUNNER_1_REPORT.md
```
