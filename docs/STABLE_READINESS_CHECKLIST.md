# Stable Readiness Checklist — paper-three-pass-reader v0.3.0-alpha

This checklist was used to decide whether the project is ready to cut a
stable-readiness alpha release. The decision and the actual results from
this run are recorded in
[`docs/PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md`](PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md).

## Core CLI

The `p3pr` one-line CLI has 10 subcommands.

- [x] `p3pr url <url>` — fetch HTML / PDF from URL, run pipeline
- [x] `p3pr arxiv <id>` — arXiv ID / URL, with hint-based resolver
- [x] `p3pr pdf <path>` — local PDF
- [x] `p3pr title <title>` — title-based hint lookup
- [x] `p3pr abstract <path>` — abstract / OCR text file
- [x] `p3pr screenshot <path>` — screenshot / poster transcript
- [x] `p3pr repo <url>` — GitHub repo URL hint lookup
- [x] `p3pr finalize <run-dir>` — second-stage CLI (audit + qgate + render + publish)
- [x] `p3pr status` — read-only run + manifest summary
- [x] `p3pr doctor` — read-only toolchain health check

## Quality gates

- [x] `audit_paper_reading.py` — structural audit
- [x] `quality_gate_zh_cn.py` — zh-CN bilingual discipline gate
- [x] `audit_published_pages.py` — published-pages regression audit
- [x] `scripts/validate.sh` — 305 sub-checks across 23 steps

## Publishing

- [x] `publish_output_to_github.sh` — pushes to `gh-pages`
- [x] root index page rendered, with manifest link in `<head>` and visible About link
- [x] `published_pages.json` regenerated on every publish
- [x] manifest link validated by `_check_site_index()` (audit step 13, passes live)
- [x] `page_type` classification: `site_index` / `paper_page` / `manifest` / `unknown` (v0.2.12)
- [x] root index exempted from paper-page checks (template_leak / raw_dict still apply)

## Evidence discipline

- [x] `reading_mode` discipline: `full_text` ≥ 800 chars HTML body, `partial_text` otherwise
- [x] `evidence labels`: `[Paper evidence]` / `[Author claim]` / `[Agent inference]`
- [x] structured `source_resolution` (top-level + legacy `intake_quality.source_resolution` list both supported)
- [x] no template leak (`{% else %}` and raw `{'label': ...}` dicts) in rendered pages
- [x] no old footer (`generator_version` exposed; pages rebuilt under v0.2.9+ all use the new footer)
- [x] claim IDs and glossary definitions display correctly (v0.2.9)

## Stable guards

- [x] v0.2.15 — `p3pr --publish` BLOCKs on missing `paper-reading-output/index.html` (verified by validation step 20l)
- [x] v0.2.17 — `p3pr finalize` BLOCKs on missing `work/paper_reading.json` (verified by validation step 22e)
- [x] v0.2.18 — site-path / page-title auto-inference, richer summary (verified by validation step 22)
- [x] v0.2.19 — `status` / `doctor` are read-only and never auto-fix (verified by validation step 23)

## Read-only observability

- [x] `p3pr status --runs` — scan local `runs/` directory
- [x] `p3pr status --site` — read `published_pages.json`
- [x] `p3pr doctor --quick` — quick health check (no validation)
- [x] `p3pr doctor --full` — health check + `validate.sh`
- [x] `p3pr doctor --offline` — skip HTTP probes
- [x] both commands emit JSON via `--json-output`
- [x] both commands print fixed `P3PR_STATUS_*` / `P3PR_DOCTOR_*` summary blocks
- [x] dirty working tree and missing gh are WARN, never FAIL

## Readiness results (this run)

| Check | Result |
| --- | --- |
| `bash scripts/validate.sh` | 305/0 PASS |
| `./p3pr doctor --offline` | 24 PASS / 1 WARN (dirty tree) / 0 FAIL |
| `./p3pr doctor --quick` | 24 PASS / 1 WARN (dirty tree) / 0 FAIL |
| `./p3pr doctor --full` | 24 PASS / 1 WARN (dirty tree) / 0 FAIL |
| `./p3pr status --runs --site` | PASS, 2 local runs (1 published, 1 rendered), 13 manifest pages |
| live published-pages audit | 14/14 PASS, 0 warn, 0 fail (overall PASS) |
| URL dry-run smoke | `P3PR_SOURCE_URL` printed, no side effects |
| finalize dry-run smoke | `inferred_site_path` + `P3PR_SITE_PATH` printed, no side effects |
| **Release decision** | **PASS_WITH_WARNINGS** — see phase report |

## Not yet stable

This is `v0.3.0-alpha`, not `v0.3.0` stable. The next stable release should
follow after a few more real paper runs and at least one more audit cycle.

## Compatibility

- All existing v0.2.x run directories remain compatible (verified by re-running
  finalize on the v0.2.16 dogfood run).
- All existing GitHub Pages remain published.
- All existing tags (v0.2.0-alpha through v0.2.19-alpha) are not moved.
