# Phase P3PR-V0.2.18 — `p3pr finalize` UX Polish

## STATUS

PASS

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.2.17-alpha

## TARGET_VERSION

v0.2.18-alpha

## PROBLEM

After v0.2.17 added `p3pr finalize <run-dir>`, the daily two-stage workflow still required the user to pass `--site-path` and `--page-title` on the finalize command. The summary block also said generic things like "warnings exist" and gave the operator no concrete next step.

The fix is to make `finalize` infer the site-path and page-title from the filled `paper_reading.json`, and to make the summary block actionable.

## FIX_SUMMARY

- Added `_slugify_title()` (stdlib-only ASCII slug with stable rules: lowercase, strip, non-alnum→`-`, merge dashes, cap at 80 chars). CJK-only inputs return `''` so the caller falls back to run-dir basename.
- Added `infer_site_path(run_dir, work_json, explicit)` and `infer_page_title(run_dir, work_json, explicit)`.
- Added `summarize_finalize_warnings(audit_json, qg_json)` that reads the audit and quality-gate JSON, collects all `severity == warn` entries, and produces a single-line `|`-joined summary (up to 3 items, with `... (+N more)` when longer).
- Added `build_finalize_next_action(...)` that returns a state-aware one-liner for the operator.
- Added new summary fields: `P3PR_READING_MODE`, `P3PR_LANGUAGE`, `P3PR_SITE_PATH`, `P3PR_PAGE_TITLE`, `P3PR_AUDIT_STATUS`, `P3PR_QUALITY_GATE_STATUS`, `P3PR_WARNING_COUNT`, `P3PR_WARNING_SUMMARY`.
- Refactored dry-run to print `inferred_site_path` / `inferred_page_title` with source attribution.
- Preserved every v0.2.15 and v0.2.17 publish guard.

## SITE_PATH_INFERENCE

Precedence:

1. Explicit `--site-path` (used as-is, no slugification).
2. `paper_metadata.page_slug` / `paper_metadata.slug` / `paper_metadata.default_slug` (or top-level `page_slug` / `slug` / `default_slug`).
3. `paper_metadata.title` (or top-level `title`) passed through `_slugify_title()`.
4. Run-dir basename (CJK-only titles reach this fallback).

## PAGE_TITLE_INFERENCE

Precedence:

1. Explicit `--page-title` (used as-is).
2. `paper_metadata.page_title` (or top-level `page_title`).
3. For zh-CN target/ui language: `paper_metadata.title_zh` / `paper_metadata.title_zh_cn` (or top-level).
4. `paper_metadata.title` (or top-level `title`).
5. Run-dir basename.

## WARNING_SUMMARY

`summarize_finalize_warnings` reads `<run-dir>/work/audit_final.json` and `<run-dir>/work/quality_gate_zh_cn.json` if present. For each, it scans `warnings` / `issues` / `findings` / `problems` keys and keeps only entries with `severity == "warn"` or `"warning"`. Each entry is normalized to a one-line string: `code: message (at path)` when both code/message/path exist, falling back to just `code` or `code: message` when only some are present. The summary is the first 3 lines `|`-joined; longer lists get `... (+N more)`. Empty case: `P3PR_WARNING_COUNT: 0`, `P3PR_WARNING_SUMMARY: no warnings`.

## DRY_RUN_OUTPUT

`./p3pr finalize <run-dir> --publish --dry-run` now prints:

```
P3PR_FINALIZE_DRY_RUN: true
would_read_json: ...
would_audit: True (audit_paper_reading.py)
would_quality_gate: True (target_language=zh-CN, ui_language=zh-CN, skip_quality_gate=False)
would_render: True (render_page.py → .../paper-reading-output)
would_publish: True (repo=..., branch=...)
inferred_site_path: ... (source: auto from paper_reading.json / run-dir)
inferred_page_title: ... (source: auto from paper_reading.json)
P3PR_SITE_PATH: ...
P3PR_PAGE_TITLE: ...
P3PR_READING_MODE: full_text
P3PR_LANGUAGE: zh-CN/zh-CN
published_audit_after_publish: True
```

No side effects. Side-channel: explicit `--site-path` / `--page-title` flips the `source:` line accordingly.

## PUBLISH_GUARDS

Carried over from v0.2.15 / v0.2.17, all intact:

- Missing `work/paper_reading.json` → `P3PR_FINALIZE_STATUS: BLOCKED` (clear "work/paper_reading.json missing" message).
- Audit FAILED → `P3PR_FINALIZE_STATUS: BLOCKED`.
- Audit non-zero return code → `P3PR_FINALIZE_STATUS: BLOCKED`.
- Quality-gate FAILED (zh-CN) → `P3PR_FINALIZE_STATUS: BLOCKED` unless `--allow-draft-publish`.
- Quality-gate WARN (zh-CN) → `P3PR_FINALIZE_STATUS: WARN` unless `--allow-warnings`.
- Render FAILED → `P3PR_FINALIZE_STATUS: BLOCKED`.
- Missing `paper-reading-output/index.html` after render → `P3PR_FINALIZE_STATUS: BLOCKED` (v0.2.15 hard guard).
- Publish step non-zero → `P3PR_FINALIZE_STATUS: BLOCKED` (with local page path printed so the operator can inspect).

## SMOKE_RUNS

- Dry-run (no flags beyond `--publish`): PASS — `P3PR_FINALIZE_DRY_RUN: true`, inferred `site_path=you-and-your-research`, inferred `page_title=You and Your Research`, source attribution shows "auto from paper_reading.json / run-dir".
- Dry-run with explicit `--site-path my-override-slug --page-title 'My Override Title'`: PASS — overrides take effect; `P3PR_SITE_PATH: my-override-slug`, `P3PR_PAGE_TITLE: My Override Title`, source line shows "explicit --site-path".
- No-publish finalize on filled dogfood run: PASS — `P3PR_FINALIZE_STATUS: WARN` (quality-gate WARN), `P3PR_SITE_PATH: you-and-your-research`, `P3PR_PAGE_TITLE: You and Your Research`, `P3PR_WARNING_COUNT: 1`, `P3PR_WARNING_SUMMARY: Found 4 interpretive field(s)...`, `P3PR_NEXT_ACTION: Review 1 warning(s) in .../work/quality_gate_zh_cn.json (or audit_result.json). Re-run with --allow-warnings if acceptable.`
- Publish finalize on filled dogfood run, new slug `you-and-your-research-url-finalize-ux-cn`, custom page title "Finalize UX：You and Your Research": PASS — `P3PR_FINALIZE_STATUS: PASS`, `P3PR_PAGE_URL: https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-finalize-ux-cn/`, `P3PR_NEXT_ACTION: Done. Page published: ... 1 non-blocking warning(s) noted.`
- Block path (missing `work/paper_reading.json`): PASS — `P3PR_FINALIZE_STATUS: BLOCKED`, clear "work/paper_reading.json missing" message, no publish.
- Slugify unit checks: PASS — `"You and Your Research" -> "you-and-your-research"`, `"  Hello,   World!  " -> "hello-world"`, `"你好世界" -> ""` (fallback to run-dir basename).

## PUBLISHED_PAGE

<https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-finalize-ux-cn/>

Verified live: HTTP 200, content rendered, footer present, no template leak, no raw dict, claims/evidence map present, resolver trail present, zh-CN glossary present, confidence values present, essay practice plan present.

## PUBLISHED_PAGES_AUDIT

Re-ran `audit_published_pages.py` after publishing the new finalize-ux page:

- `pages_total: 13` (was 12 before this release; new finalize-ux page added)
- `pages_checked: 13`
- `pages_pass: 13`
- `pages_warn: 0`
- `pages_fail: 0`
- `overall: PASS`

Stashed at `runs/published-pages-audit-20260616-finalize-ux/audit.json`.

## VALIDATION

```
=================================================
 PASS: 293    FAIL: 0
=================================================
STATUS: PASS
```

Step [22] v0.2.18-alpha p3pr finalize UX polish (14 sub-checks, all green). Total validation covers: every subcommand, every published page, every block path in v0.2.15 / v0.2.17 / v0.2.18, slugify behavior, summary block fields, and the v0.2.15 publish-gate on a real finalize run.

## FILES_CREATED

- `docs/RELEASE_NOTES_v0.2.18-alpha.md`
- `docs/PHASE_P3PR_V0_2_18_FINALIZE_UX_POLISH_REPORT.md`
- `runs/published-pages-audit-20260616-finalize-ux/audit.json` + `audit.md`
- `runs/p3pr-url-dogfood-filled-20260616/you-and-your-research-url-dogfood-cn/work/published_pages_audit_after_finalize.json` (re-stashed from this run)

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/p3pr.py` — added `_slugify_title`, `infer_site_path`, `infer_page_title`, `summarize_finalize_warnings`, `build_finalize_next_action`, expanded `_finalize_print_summary`, refactored `handle_finalize` to use the helpers.
- `scripts/validate.sh` — new step [22] (14 sub-checks for v0.2.18).
- `README.md` — Quick Start updated to drop the explicit `--site-path` / `--page-title` from the recommended two-stage flow, version table updated.
- `README.zh-CN.md` — version table updated, version footer updated.
- `CHANGELOG.md` — full v0.2.18-alpha entry.
- `skills/paper-three-pass-reader/docs/USAGE.md` — finalize section updated.
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — finalize section updated.
- `skills/paper-three-pass-reader/docs/RUNNER.md` — finalize section updated.
- `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md` — finalize section updated.

## COMMIT

`Polish p3pr finalize UX`

## PUSH

`git push origin main`

## TAG

`v0.2.18-alpha` (annotated)

## RELEASE

<https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.18-alpha>

## LIMITATIONS

- `finalize` does not auto-fill paper content. It assumes `work/paper_reading.json` has already been filled by human or agent.
- `--allow-warnings` and `--allow-draft-publish` should be used carefully — they exist to make low-CJK-coverage English papers publishable, but they bypass quality gates.
- `finalize` does not retry network failures during publish.
- The site-path slugifier is ASCII-only and CJK-only titles fall back to the run-dir basename. There is no pypinyin or similar dependency, and none will be added.
- The warning-summary builder reads from `audit_final.json` and `quality_gate_zh_cn.json` only. If a future run uses different output paths the summary will be empty — the operator should still read the full log.

## NEXT_USER_ACTION

- Spot-check the new live dogfood page: <https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-finalize-ux-cn/>.
- Try the streamlined two-stage flow on a fresh URL run to confirm the inferred site-path/page-title look right.
- If the inference ever picks the wrong title, override with `--page-title` (e.g. for papers whose `paper_metadata.title` is the English title and the user wants the Chinese title on the page).
- Next planned phase is v0.2.19 (no content scope defined yet — wait for user direction).
