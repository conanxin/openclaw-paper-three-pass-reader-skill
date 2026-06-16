# Phase P3PR-V0.2.19 — `p3pr status` + `p3pr doctor`

## STATUS

PASS

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.2.18-alpha

## TARGET_VERSION

v0.2.19-alpha

## PROBLEM

As the project's `runs/` directory and the live `gh-pages` site grow, the
operator needs to be able to ask, in a single command:

1. **What's local?** — which run directories exist, which are still drafts,
   which are rendered, which are published.
2. **What's online?** — which pages are in `published_pages.json`, is the
   manifest reachable.
3. **Is the toolchain healthy?** — required scripts present, `gh` logged in,
   git working tree clean, `validate.sh` passing.

Before v0.2.19 the answer required `ls runs/`, opening the manifest in a
browser, and remembering which checks `scripts/validate.sh` covers. The fix
is two read-only observability subcommands.

## FIX_SUMMARY

- **`p3pr status`** — scans `runs/` and reads `published_pages.json`.
  - `_scan_runs()` walks `<runs_root>/*/`, picks any directory that has
    `work/paper_reading.json` (or `fill-pack/paper_reading.json` + `fill-pack/`)
    as a run, reads `audit_*.json` / `quality_gate_zh_cn.json` /
    `paper-reading-output/index.html`, and classifies the run with
    `_classify_run_status()`. Cross-references the manifest slugs to flag
    `published` runs.
  - `_fetch_manifest()` reads `--manifest-file` (if given) or fetches
    `--manifest-url` (unless `--offline`), returning a `source` of `'url'`,
    `'file'`, `'offline'`, or `'unavailable'`.
  - `_summarize_manifest()` normalizes the manifest into `pages_total` /
    `pages[]` / `root_index_present` / `manifest_valid`.
  - `_status_print_summary()` prints a fixed `P3PR_STATUS_*` block, optional
    JSON via `--json-output`, and a human-readable per-run breakdown.
- **`p3pr doctor`** — runs read-only toolchain health checks.
  - `_doctor_collect()` walks 7 groups: local env (python3, git, p3pr shim),
    required scripts, required data/docs, git state, gh CLI / auth, optional
    `validate.sh`, light HEAD probe of site root + manifest.
  - Dirty working tree, missing gh, and unreachable site all surface as WARN
    (with a `→` recommendation line) — never FAIL.
  - `--json-output` writes the full check list + summary as JSON.
- Both subcommands have their own dedicated argparse parsers
  (`build_status_parser`, `build_doctor_parser`) and are wired into the
  main `build_parser` stub-subparsers for clean `--help` output.
- Both are 100% read-only. They never write to runs, never modify the
  working tree, never call `git commit`, never re-authenticate `gh`.

## STATUS_COMMAND

```
./p3pr status [--runs] [--site] [--all]
              [--runs-root <path>]
              [--manifest-url <url>] [--manifest-file <path>] [--site-root <url>]
              [--json-output <path>]
              [--limit <n>] [--filter <text>]
              [--show-warnings|--hide-warnings]
              [--show-drafts|--hide-drafts]
              [--show-published|--hide-published]
              [--offline]
```

Default: both `--runs` and `--site` (no flags needed). With network enabled
the manifest is fetched from `--manifest-url` (default
`https://conanxin.github.io/paper-reading-pages/published_pages.json`).
With `--offline` the site block falls back to `WARN / unavailable`.

## DOCTOR_COMMAND

```
./p3pr doctor [--quick] [--full]
              [--offline] [--skip-network] [--skip-validation]
              [--manifest-url <url>] [--site-root <url>]
              [--json-output <path>]
```

Default: `--quick` (no validation). `--full` runs `scripts/validate.sh` and
adds its PASS/FAIL to the summary. `--offline` (or `--skip-network`) skips
the HTTP probes of the site root + manifest.

## SMOKE_RUNS

Stashed at `runs/p3pr-status-doctor-smoke-20260616/`:

- `./p3pr status --runs --offline --json-output runs/.../status_runs.json`
  — exit 0, JSON written, contains `runs` (2 records) + `summary` with
  draft/rendered/published/blocked counters all 0 except rendered=1
  rendered_with_warnings=1.
- `./p3pr status --site --manifest-url .../published_pages.json
  --json-output runs/.../status_site.json` — exit 0, JSON written,
  `pages_total=13`, `manifest_source=url`, `status=PASS`.
- `./p3pr doctor --offline --json-output runs/.../doctor_offline.json` —
  exit 0, JSON written, 25 checks; `summary.pass=24`, `summary.warn=1`
  (git_working_tree is dirty because this v0.2.19 work is uncommitted at
  smoke time), `summary.fail=0`. `status=WARN` overall.
- `./p3pr doctor --quick --json-output runs/.../doctor_quick.json` —
  exit 0, JSON written, 25 checks; live HTTP probes both PASS (HTTP 200);
  `summary.warn=1` (still the dirty tree), `summary.fail=0`. `status=WARN`
  overall.

Additional offline smoke runs (during development):

- `./p3pr status` (no flags) — 2 local runs, 1 published (the
  attention-is-all-you-need consumer run is in the manifest), 1 just rendered.
  13 manifest pages. Overall status PASS.
- `./p3pr status --runs --runs-root /tmp/p3pr-malformed-… --offline` on a
  fixture with `{not valid json` in `work/paper_reading.json` — exit 0,
  no crash (regression guard verified by validation step 23e).

## VALIDATION

```
=================================================
 PASS: 305    FAIL: 0
=================================================
STATUS: PASS
```

Step [23] v0.2.19-alpha p3pr status + doctor subcommands (12 sub-checks, all
green). Total validation covers: every subcommand, every published page, every
block path in v0.2.15 / v0.2.17 / v0.2.18, slugify behavior, summary block
fields, the v0.2.15 publish-gate, the v0.2.18 finalize UX, status JSON shape,
fake-manifest file support, malformed-run regression, doctor offline /
quick modes, dirty-tree-as-WARN invariant.

## FILES_CREATED

- `docs/RELEASE_NOTES_v0.2.19-alpha.md`
- `docs/PHASE_P3PR_V0_2_19_STATUS_AND_DOCTOR_REPORT.md`
- `skills/paper-three-pass-reader/docs/STATUS_AND_DOCTOR.md`
- `runs/p3pr-status-doctor-smoke-20260616/status_runs.json`
- `runs/p3pr-status-doctor-smoke-20260616/status_site.json`
- `runs/p3pr-status-doctor-smoke-20260616/doctor_offline.json`
- `runs/p3pr-status-doctor-smoke-20260616/doctor_quick.json`

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/p3pr.py` — added
  `DEFAULT_MANIFEST_URL` / `DEFAULT_SITE_ROOT` / `DEFAULT_RUNS_ROOT`,
  `_classify_run_status`, `_read_json_safely`, `_scan_runs`,
  `_fetch_manifest`, `_summarize_manifest`, `_status_print_summary`,
  `handle_status`, `_status_recommendations`, `_doctor_check_exists`,
  `_doctor_check_executable`, `_doctor_check_command`,
  `_doctor_check_git_state`, `_doctor_check_gh_status`,
  `_doctor_check_validation`, `_doctor_check_site_health`, `_doctor_collect`,
  `_doctor_print_summary`, `handle_doctor`, `build_status_parser`,
  `build_doctor_parser`. Registered `status` / `doctor` on the main
  `build_parser` and wired them into `main()`.
- `scripts/validate.sh` — new step [23] (12 sub-checks for v0.2.19).
- `README.md` — Quick Start updated, version table updated.
- `README.zh-CN.md` — version table updated, version footer updated.
- `CHANGELOG.md` — full v0.2.19-alpha entry.
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — new
  `p3pr status` / `p3pr doctor` section.
- `skills/paper-three-pass-reader/docs/USAGE.md` — new section.
- `skills/paper-three-pass-reader/docs/RUNNER.md` — new section.

## COMMIT

`Add p3pr status and doctor commands`

## PUSH

`git push origin main`

## TAG

`v0.2.19-alpha` (annotated)

## RELEASE

<https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.19-alpha>

## LIMITATIONS

- `status` does not introspect draft `field_checklist.json` / `draft_status.json`
  for finer-grained stage info; it only reads `work/paper_reading.json` +
  `work/audit_*.json` + `work/quality_gate_zh_cn.json` + the rendered page +
  the manifest.
- `status` cannot tell you why a run is `blocked`; for that you still have to
  open `work/audit_final.json` (or `work/audit_result.json`) and read the
  failures. The next-action line tells you which file to open, not what is
  wrong with it.
- `doctor` does not run `validate.sh` by default (it is `--full`-gated) to
  keep the quick path fast. Use `p3pr doctor --full` for pre-release checks.
- `doctor`'s HEAD probe is shallow: 10-second timeout, no body fetch. It does
  not verify the page content.
- The `published` classification is based on the manifest slug matching the
  inferred `site_path_guess`. If the manifest uses a different slug scheme
  (e.g. trailing slash, or `path` instead of `slug`), the run may show as
  `rendered` even though the page is online. Re-publish with a clean slug to
  fix, or override `--site-path` on the publish command.

## NEXT_USER_ACTION

- Try `./p3pr status` and `./p3pr doctor --offline` to confirm everything
  looks correct.
- If the live site returns HTTP 200 and the manifest has 13 pages but `status`
  shows fewer local runs, that's expected — the consumer runs from older
  releases (v0.2.10 / v0.2.15 / v0.2.16) live under their own per-release
  run dirs and may or may not be picked up depending on whether they have
  `work/paper_reading.json`.
- Pre-release, run `./p3pr doctor --full` to make sure `validate.sh` still
  passes after any local edits.
- Next planned phase is v0.2.20 (no content scope defined yet — wait for
  user direction).
