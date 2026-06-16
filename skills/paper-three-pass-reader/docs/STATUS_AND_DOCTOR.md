# Status & Doctor (`p3pr status`, `p3pr doctor`)

This document describes the two read-only observability subcommands added in
v0.2.19-alpha. Both are designed to never modify runs and never auto-fix
problems.

## Why these commands exist

As the project grows, three questions keep coming up:

1. **Local state** — Which `runs/` directories exist, which are still drafts,
   which have been audited, which are rendered, which are published? What
   stage is each run at, and what's the next action for it?
2. **Online state** — Which pages are actually on `gh-pages`? Is the manifest
   reachable? Is the site root reachable?
3. **Toolchain health** — Is the repo clean? Is `gh` logged in? Does
   `scripts/validate.sh` pass? Are the required scripts and docs present?

`p3pr status` answers (1) and (2). `p3pr doctor` answers (3). Both print a
fixed-format summary and can emit JSON for machine consumption.

## `./p3pr status`

Scans `runs/` (configurable with `--runs-root`) and reads the
`published_pages.json` manifest (configurable with `--manifest-url` or
`--manifest-file`). Default scope is both. With `--runs` you get just the
local scan; with `--site` you get just the manifest.

```bash
./p3pr status                                # both runs + site, network-allowed
./p3pr status --runs                         # local runs only
./p3pr status --site                         # site manifest only
./p3pr status --offline                      # runs scan + site summary in WARN mode
./p3pr status --runs --offline --json-output status_runs.json
./p3pr status --site --manifest-file ./local_manifest.json
```

### Run status taxonomy

| Status | Meaning |
| --- | --- |
| `unknown` | directory has a `fill-pack/` but no `work/paper_reading.json` |
| `draft` | `work/paper_reading.json` exists but no audit / no quality gate / no render |
| `filled` | `work/paper_reading.json` + `fill-pack/`, but no audit yet |
| `audited` | audit + (zh-CN) quality gate PASS, no `paper-reading-output/index.html` yet |
| `rendered` | `paper-reading-output/index.html` exists, not in the published-pages manifest |
| `rendered_with_warnings` | rendered, quality gate WARN, not yet published |
| `published` | site-path is found in the published-pages manifest |
| `blocked` | audit FAILED or quality-gate FAILED — must edit `work/paper_reading.json` |

### Site summary

`--site` reads `published_pages.json` (URL by default, local file with
`--manifest-file`, skipped entirely with `--offline`) and prints:

- `pages_total` (number of pages in the manifest)
- `pages[]` (title, slug, url, published_at per page)
- `manifest_source` (`url` / `file` / `offline` / `unavailable`)
- `root_index_present` (whether the manifest advertises a root index)

### Fixed summary block

Every `./p3pr status` exit prints:

```text
P3PR_STATUS_STATUS: PASS | WARN | FAIL
P3PR_RUNS_ROOT: <path>
P3PR_RUNS_TOTAL: <n>
P3PR_RUNS_DRAFT: <n>
P3PR_RUNS_FILLED: <n>
P3PR_RUNS_AUDITED: <n>
P3PR_RUNS_RENDERED: <n>
P3PR_RUNS_RENDERED_WITH_WARNINGS: <n>
P3PR_RUNS_PUBLISHED: <n>
P3PR_RUNS_BLOCKED: <n>
P3PR_SITE_PAGES: <n or unknown>
P3PR_SITE_STATUS: PASS | WARN | FAIL | skipped
P3PR_SITE_MANIFEST_SOURCE: url | file | offline | unavailable | skipped
P3PR_NEXT_ACTION: <state-aware one-liner>
```

### Status is read-only

`status` never writes to runs, never calls `git commit`, never pushes. It only
reads `work/paper_reading.json`, `work/audit_*.json`, `work/quality_gate_*.json`,
and `paper-reading-output/index.html`. The only file it writes is
`--json-output`.

## `./p3pr doctor`

Runs read-only health checks on the local toolchain. By default it is **quick**
(no `validate.sh`, no full audit) and prints a `P3PR_DOCTOR_*` summary. With
`--full` it runs `scripts/validate.sh`. With `--offline` it skips HTTP probes.

```bash
./p3pr doctor                                # quick
./p3pr doctor --offline                      # quick, no HTTP probes
./p3pr doctor --full                         # runs scripts/validate.sh
./p3pr doctor --skip-validation              # skips the validation script
./p3pr doctor --offline --json-output doctor.json
```

### Check groups

The doctor runs the following checks:

| Group | Check | What it does | Failure mode |
| --- | --- | --- | --- |
| Local env | `python3` on PATH | `shutil.which("python3")` | WARN (not FAIL) |
| Local env | `git` on PATH | `shutil.which("git")` | WARN (not FAIL) |
| Local env | `p3pr_shim` exists + executable | file + `os.X_OK` | FAIL on missing, WARN on not-exec |
| Scripts | `run_paper_reading`, `render_page`, `audit_paper_reading`, `quality_gate_zh_cn`, `audit_published_pages`, `publish_output_to_github`, `source_resolution_utils`, `resolver_hints` | file exists | FAIL on missing |
| Data/docs | `resolver_hints.json`, `SKILL.md`, `README.md`, `README.zh-CN.md`, `CHANGELOG.md` | file exists | FAIL on missing |
| Git | `git_repo`, `git_branch`, `git_working_tree`, `git_latest_tag` | `git -C root …` | dirty tree is WARN (not FAIL) |
| GitHub | `gh_cli` on PATH, `gh auth status` | subprocess | missing / not-logged-in is WARN (not FAIL) |
| Validation | `validate.sh` (full only) | subprocess | PASS / FAIL on `bash scripts/validate.sh` exit code |
| Site | `site_root_http`, `site_manifest_http` | HEAD probe | WARN on network errors |

### Why dirty tree / missing gh are WARN, not FAIL

`p3pr doctor` is meant to be safe to run any time, including mid-edit.
A dirty working tree is a normal state during development — it's not a
problem with the toolchain. `gh` not being logged in is a problem only
for publish flows; for a quick offline check it's fine to ignore. Both
are surfaced as WARN with a `→` recommendation line so the operator can
decide what to do.

### Fixed summary block

```text
P3PR_DOCTOR_STATUS: PASS | WARN | FAIL
P3PR_DOCTOR_PASS: <n>
P3PR_DOCTOR_WARN: <n>
P3PR_DOCTOR_FAIL: <n>
P3PR_NEXT_ACTION: <state-aware one-liner>
```

After the summary block, doctor prints one line per check with `[ OK ]`,
`[WARN]`, or `[FAIL]` markers, plus a recommendation line for any non-PASS
check. With `--json-output` the same checks are written as a JSON array.

### Doctor is read-only and never auto-fixes

`doctor` never modifies runs, never runs `git clean`, never `chmod`s
anything, never re-authenticates `gh`. It just reports. The operator decides
what to do based on the recommendations.

## Recommended daily checks

```bash
./p3pr status                                # what's local, what's online
./p3pr doctor --offline                      # is the toolchain healthy?
./p3pr doctor --full                         # pre-release check, also runs validation
```

`status` tells you "where are we" and `doctor` tells you "is everything still
working". Together they cover the two most common questions before / after a
publish run.

## JSON shapes

### `p3pr status` JSON

```json
{
  "status": "PASS",
  "runs_root": "runs",
  "runs": [
    {
      "run_dir": "runs/you-and-your-research-20260615",
      "slug": "you-and-your-research",
      "title": "You and Your Research",
      "input_kind": "url",
      "reading_mode": "full_text",
      "target_language": "zh-CN",
      "ui_language": "zh-CN",
      "has_fill_pack": true,
      "has_audit": true,
      "audit_status": "PASS",
      "has_quality_gate": true,
      "quality_gate_status": "WARN",
      "has_rendered_page": true,
      "local_page_path": "runs/.../paper-reading-output/index.html",
      "has_published_hint": false,
      "site_path_guess": "you-and-your-research",
      "status": "rendered_with_warnings",
      "next_action": "Rendered with quality-gate WARN. ..."
    }
  ],
  "site": {
    "status": "PASS",
    "manifest_source": "url",
    "site_root": "https://conanxin.github.io/paper-reading-pages",
    "pages_total": 13,
    "pages": [...],
    "root_index_present": true,
    "manifest_valid": true,
    "next_action": "13 page(s) tracked in manifest."
  },
  "summary": {
    "runs_total": 2,
    "draft": 0, "filled": 0, "audited": 0,
    "rendered": 1, "rendered_with_warnings": 1,
    "published": 0, "blocked": 0, "unknown": 0
  },
  "recommendations": ["..."],
  "next_action": "All clear. ..."
}
```

### `p3pr doctor` JSON

```json
{
  "status": "PASS",
  "checks": [
    {"name": "python3", "status": "PASS", "message": "...", "recommendation": ""},
    {"name": "git", "status": "PASS", "message": "...", "recommendation": ""}
  ],
  "summary": {"pass": 24, "warn": 1, "fail": 0},
  "next_action": "1 doctor check(s) WARN. ..."
}
```

## v0.3.0-alpha bug fix

`p3pr doctor`'s per-check `status` is uppercase (`PASS` / `WARN` / `FAIL`)
but the summary counter dict uses lowercase keys (`pass` / `warn` / `fail`).
The `if s in summary` lookup in `_doctor_print_summary` was always failing,
so the JSON `summary.pass` / `summary.warn` / `summary.fail` values were
always `0`. v0.3.0-alpha lowercases the check status before the lookup.
After the fix, the same doctor run reports `summary: {pass: 24, warn: 1,
fail: 0}` (the 1 WARN is `git_working_tree` because the working tree is
dirty mid-release).

## v0.3.0-alpha readiness results

- `bash scripts/validate.sh` — **305 / 0 PASS**
- `./p3pr doctor --offline` — 24 PASS / 1 WARN (dirty tree) / 0 FAIL
- `./p3pr doctor --quick` — 24 PASS / 1 WARN (dirty tree) / 0 FAIL
- `./p3pr doctor --full` — 24 PASS / 1 WARN (dirty tree) / 0 FAIL
- live `audit_published_pages.py` — 14 / 14 PASS, 0 warn, 0 fail
- URL dry-run smoke + finalize dry-run smoke — no side effects

See
[`STABLE_READINESS_CHECKLIST.md`](../../../../docs/STABLE_READINESS_CHECKLIST.md)
and
[`PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md`](../../../../docs/PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md)
for the full readiness record.

## v0.3.0 stable cleanroom — DEFERRED

`v0.3.0` stable was **deferred** in
[`PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md`](../../../../docs/PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md).
The cleanroom is otherwise fully clean (validation 305/0, live audit
14/14, doctor 24/1/0, all dry-runs PASS) but `p3pr doctor` reports a
`git_working_tree` WARN from a historical backlog. `v0.3.0-alpha`
remains the latest released. See the cleanroom report for the three
options the user can take to unblock `v0.3.0` stable.
