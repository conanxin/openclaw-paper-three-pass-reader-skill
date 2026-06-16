# paper-three-pass-reader v0.2.19-alpha

## Summary

This release adds `p3pr status` and `p3pr doctor`, two read-only observability
subcommands that answer the two questions operators keep asking: "where are
my runs and pages" and "is the toolchain healthy".

## Included

- **`./p3pr status`** — scans `runs/` and reads `published_pages.json`.
  - Per-run classification: `draft` / `filled` / `audited` / `rendered` /
    `rendered_with_warnings` / `published` / `blocked` / `unknown`.
  - Cross-references the manifest to flag `published` runs.
  - `--runs` / `--site` to narrow scope; `--offline` to skip HTTP fetches.
  - `--runs-root`, `--manifest-url`, `--manifest-file`, `--site-root`,
    `--json-output`, `--limit`, `--filter`, `--show-{warnings,drafts,published}` /
    `--hide-{warnings,drafts,published}`.
  - Fixed `P3PR_STATUS_*` summary block + per-run recommendations.
- **`./p3pr doctor`** — read-only toolchain health check.
  - Local env (python3, git, p3pr shim), required scripts, required docs,
    git state (branch, working tree, latest tag), `gh` CLI + auth, optional
    `scripts/validate.sh`, light HEAD probe of site root + manifest.
  - `--quick` (default, no validation) / `--full` (runs validation).
  - `--offline` / `--skip-network` to skip HTTP probes.
  - `--skip-validation` to skip the validation script entirely.
  - `--json-output` for machine consumption.
  - Fixed `P3PR_DOCTOR_*` summary block + per-check `[ OK ] / [WARN] / [FAIL]` lines.
- **Validation: 12 new sub-checks in step 23.** Total 305/0 PASS.
- **Smoke fixtures** at `runs/p3pr-status-doctor-smoke-20260616/`:
  `status_runs.json` / `status_site.json` / `doctor_offline.json` /
  `doctor_quick.json`.

## Why dirty tree / missing gh are WARN, not FAIL

Doctor is meant to be safe to run any time, including mid-edit. A dirty
working tree is normal during development; `gh` not being logged in is only
a problem for publish flows. Both surface as WARN with a `→` recommendation
line; the operator decides what to do.

## Status taxonomy

| Status | Meaning |
| --- | --- |
| `unknown` | `fill-pack/` only, no `work/paper_reading.json` yet |
| `draft` | `work/paper_reading.json` exists, no audit / qgate / render |
| `filled` | `work/paper_reading.json` + `fill-pack/`, no audit yet |
| `audited` | audit + (zh-CN) quality gate PASS, no rendered page yet |
| `rendered` | `paper-reading-output/index.html` exists, not in manifest |
| `rendered_with_warnings` | rendered, quality gate WARN, not yet published |
| `published` | site-path is found in `published_pages.json` |
| `blocked` | audit FAILED or quality-gate FAILED |

## Compatibility

- All existing p3pr subcommands remain unchanged.
- All v0.2.15 / v0.2.17 / v0.2.18 publish guards and finalize UX unchanged.
- Existing run directories and published pages unchanged.
- No old tags moved.
- No old releases deleted.

## When to use status / doctor

- **Before publishing** — `./p3pr status` to confirm the run is `rendered`
  (or `rendered_with_warnings` and you intend to use `--allow-warnings`) and
  not `blocked`.
- **After publishing** — `./p3pr status --site` to confirm the page is in
  the manifest and the live URL responds.
- **Pre-release** — `./p3pr doctor --full` (runs validation) to confirm
  nothing has regressed.
- **Daily sanity check** — `./p3pr status; ./p3pr doctor --offline`.

## Dogfood

- `./p3pr status` on this repo: 2 runs (1 published, 1 rendered); 13 pages
  in the live manifest; overall status PASS.
- `./p3pr doctor --offline` on this repo: 25 checks (24 PASS, 1 WARN —
  `git_working_tree` is dirty because this v0.2.19 work is uncommitted).
- `./p3pr doctor --quick` on this repo: 25 checks (25 PASS — site_root_http
  and site_manifest_http are now live-probed and both return HTTP 200).
