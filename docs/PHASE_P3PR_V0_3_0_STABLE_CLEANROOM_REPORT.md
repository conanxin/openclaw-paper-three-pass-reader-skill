# Phase P3PR-V0.3.0 — Stable Cleanroom

## STATUS

PASS_WITH_WARNINGS — **v0.3.0 stable NOT released** (deferred to user
decision)

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.3.0-alpha

## TARGET_VERSION

v0.3.0 (deferred)

## CLEANROOM_DECISION

**PASS_WITH_WARNINGS — do not release v0.3.0 stable in this phase.**

All core stability conditions are met:

- `validation` — 305 / 0 PASS
- `doctor --offline` — 24 / 1 / 0
- `doctor --quick` — 24 / 1 / 0
- `doctor --full` — 24 / 1 / 0 (also runs validate.sh → 305/0 PASS)
- live `published-pages audit` — 14 / 14 PASS, 0 warn, 0 fail
- URL dry-run smoke — `P3PR_SOURCE_URL` printed, no side effects
- arXiv dry-run smoke — pipeline plan printed, no `work/` JSON written
- finalize dry-run smoke — `P3PR_SITE_PATH` + `P3PR_PAGE_TITLE` printed, no side effects
- gh auth — `gh auth status OK`
- No old tags moved
- No force pushes

The single WARN across all three doctor runs is `git_working_tree`. The
working tree has 4 modified files + 21 untracked entries, all of which
are clearly identifiable historical artifacts from prior phases that
were generated during those phases but never committed. The cleanroom
spec calls for "no WARN" before a stable release and explicitly forbids
deleting unknown dirty files or force-cleaning to suppress the WARN. The
WARN is real and reasonable (the tree really is dirty) and the historical
backlog is documented in the report.

Per the spec: "如果仍有 WARN，但不影响功能，可以发布 PASS_WITH_WARNINGS，但不要标记为 fully clean stable;优先不发布 v0.3.0，除非确认 WARN 合理且不会影响用户。"
Translation: "If there's still a WARN, prefer NOT to release v0.3.0,
unless confirm WARN is reasonable and won't affect users." The WARN is
reasonable (it accurately reports a dirty tree) but it's a deviation from
the "fully clean stable" bar, so this phase does not cut v0.3.0 stable.

## GIT_STATE

HEAD: `ad4a968 Prepare v0.3.0-alpha stable-readiness release`
Latest alpha tag: `v0.3.0-alpha` (annotated, at HEAD)
Latest v0.* tag: `v0.3.0-alpha`

Working tree: **dirty (historical backlog)**

| Type | Path | Source | Disposition |
| --- | --- | --- | --- |
| modified | `docs/PHASE_P3PR_V0_2_10_PUBLISHED_PAGES_REGRESSION_AUDIT_REPORT.md` | v0.2.10 post-release doc polish that was never committed | keep, report |
| modified | `runs/p3pr-url-dogfood-filled-20260616/you-and-your-research-url-dogfood-cn/work/published_pages_audit_after_finalize.json` | v0.2.18 finalize smoke write | keep, report |
| modified | `runs/you-and-your-research-20260615/you-and-your-research-cn/fill-pack/draft_status.json` | v0.2.15 fill-pack | keep, report |
| modified | `runs/you-and-your-research-20260615/you-and-your-research-cn/fill-pack/field_checklist.json` | v0.2.15 fill-pack | keep, report |
| untracked | `runs/p3pr-cli-20260615/` (2.0M, 8 files) | v0.2.5 CLI smoke | keep, report |
| untracked | `runs/p3pr-cli-20260616/` (100K, 3 files) | v0.2.16 CLI smoke | keep, report |
| untracked | `runs/p3pr-cli-smoke-20260615/` (292K, 46 files) | v0.2.5 CLI smoke | keep, report |
| untracked | `runs/p3pr-cli-v26b-smoke/` (136K, 22 files) | v0.2.5 CLI smoke | keep, report |
| untracked | `runs/p3pr-cli-v26b-smoke2/` (180K, 28 files) | v0.2.5 CLI smoke | keep, report |
| untracked | `runs/p3pr-url-dogfood-filled-20260616/...` (660K, 54 files) | v0.2.16 url dogfood (some inner dirs) | keep, report |
| untracked | `runs/published-pages-audit-20260616-url-dogfood-filled/` (20K, 2 files) | v0.2.18 published-pages audit smoke | keep, report |
| untracked | `runs/quality-gate-smoke-20260615/` (20K, 2 files) | v0.2.4 quality gate smoke | keep, report |
| untracked | `runs/resolver-hints-smoke-20260615/` (24K, 5 files) | v0.2.6 resolver hints smoke | keep, report |
| untracked | `runs/second-me-zh-cn-20260615/` (2.2M, 49 files) | v0.2.4 zh-CN smoke | keep, report |
| untracked | `runs/stable-readiness-20260616/stable-readiness-url-smoke/` | v0.3.0-alpha readiness smoke | keep, report |
| untracked | `runs/v022-fulltext-autofill-secondme-20260615/` (2.2M, 49 files) | v0.2.2 autofill smoke | keep, report |
| untracked | `runs/you-and-your-research-20260615/...` (1.1M, 104 files) | v0.2.15 fill-pack smoke | keep, report |
| untracked | `runs/stable-cleanroom-20260616/` (this phase) | this phase's cleanroom artifacts | **commit (this phase)** |

Total: 4 modified + 21 untracked (including 1 this-phase dir).

Ignored (project `.gitignore` excludes these; not part of dirty state):
`runs/attention-is-all-you-need-20260615/extracted/`,
`runs/attention-is-all-you-need-20260615/paper-reading-output/data/{final_checklist,glossary}.json`,
`runs/attention-is-all-you-need-20260615/source/`,
`runs/fill-pack-smoke-20260615/*/paper-reading-output/`.

## VALIDATION

```
=================================================
 PASS: 305    FAIL: 0
=================================================
STATUS: PASS
```

Full log: `runs/stable-cleanroom-20260616/validate.log`. 23 steps, 305
sub-checks. Covers: required files, sample render, mandatory page
sections, every subcommand, every published page, every block path in
v0.2.15 / v0.2.17 / v0.2.18 / v0.2.19, slugify behavior, summary block
fields, the v0.2.15 publish-gate, the v0.2.18 finalize UX, status JSON
shape, fake-manifest file support, malformed-run regression, doctor
offline / quick modes, dirty-tree-as-WARN invariant.

## DOCTOR_OFFLINE

- File: `runs/stable-cleanroom-20260616/doctor_offline.{json,txt}`
- `status: WARN`
- `summary: {pass: 24, warn: 1, fail: 0}`
- WARN check: `git_working_tree` (24 unchanged).

## DOCTOR_QUICK

- File: `runs/stable-cleanroom-20260616/doctor_quick.{json,txt}`
- `status: WARN`
- `summary: {pass: 24, warn: 1, fail: 0}`
- `site_root_http: 200 OK`, `site_manifest_http: 200 OK`.
- WARN check: `git_working_tree` (24 unchanged).

## DOCTOR_FULL

- File: `runs/stable-cleanroom-20260616/doctor_full.{json,txt}`
- `status: WARN`
- `summary: {pass: 24, warn: 1, fail: 0}`
- `validation_script: validate.sh exited 0 (PASS)`.
- WARN check: `git_working_tree` (24 unchanged).

## STATUS_COMMAND

- File: `runs/stable-cleanroom-20260616/status_all.{json,txt}` (online)
  - `status: PASS`
  - `runs_total: 2` (1 published, 1 rendered)
  - `site_pages: 13`, `site_status: PASS`, `site_manifest_source: url`
- File: `runs/stable-cleanroom-20260616/status_runs_offline.{json,txt}` (offline)
  - `status: WARN` (site_status `skipped`, expected with --offline)
  - `runs_total: 2` (2 rendered)
  - `site_pages: 0` (intentional; site not requested with --site)

No `blocked` runs. No `draft` runs. No `rendered_with_warnings` runs.
Historical consumer runs from v0.2.0 / v0.2.6 are present in `runs/` but
not picked up because they don't have `work/paper_reading.json` (they
predate the unified runner contract). That is a historical artifact, not
a defect.

## PUBLISHED_PAGES_AUDIT

- File: `runs/stable-cleanroom-20260616/published_pages_audit.{json,md,txt}`
- `pages_total: 14` (13 paper pages + 1 root index)
- `pages_checked: 14`
- `pages_pass: 14`
- `pages_warn: 0`
- `pages_fail: 0`
- `overall: PASS`
- Root index correctly classified as `site_index`. Manifest link
  present. No info-level findings.

## SMOKE_TESTS

- **URL dry-run** — `./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html --zh --full --no-publish --slug stable-cleanroom-url-smoke --output-root runs/stable-cleanroom-20260616 --title "You and Your Research" --authors "Richard W. Hamming" --dry-run` — exit 0; `P3PR_SOURCE_URL: https://www.cs.virginia.edu/~robins/YouAndYourResearch.html` printed; pipeline plan + `P3PR_NEXT_ACTION: remove --dry-run to actually run the pipeline`; no `work/paper_reading.json` written; only the empty `input/` and `extracted/` stub dirs.
- **arXiv dry-run** — `./p3pr arxiv 2503.08102 --zh --full --no-publish --slug stable-cleanroom-arxiv-smoke --output-root runs/stable-cleanroom-20260616 --dry-run` — exit 0; `P3PR_RUN_DIR: runs/stable-cleanroom-20260616/stable-cleanroom-arxiv-smoke`, `P3PR_FILL_PACK`, `P3PR_LOCAL_PAGE` printed; no `work/paper_reading.json` written.
- **Finalize dry-run** — `./p3pr finalize runs/p3pr-url-dogfood-filled-20260616/you-and-your-research-url-dogfood-cn --publish --dry-run` — exit 0; `P3PR_FINALIZE_DRY_RUN: true`, `P3PR_SITE_PATH: you-and-your-research`, `P3PR_PAGE_TITLE: You and Your Research`, `P3PR_READING_MODE: full_text`, `P3PR_LANGUAGE: zh-CN/zh-CN`; no `work/audit_final.json` re-written, no `work/quality_gate_zh_cn.json` re-written, no render, no publish.

## STABLE_CLEANROOM_CHECKLIST

The full checklist is in
[`docs/STABLE_CLEANROOM_CHECKLIST.md`](STABLE_CLEANROOM_CHECKLIST.md).
All boxes except "working tree clean" are checked. The release decision
is `No` because of the doctor WARN on `git_working_tree`.

## FILES_CREATED

- `docs/STABLE_CLEANROOM_CHECKLIST.md`
- `docs/RELEASE_NOTES_v0.3.0.md` (deferred, marked as DEFERRED)
- `docs/PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md` (this file)
- `runs/stable-cleanroom-20260616/validate.log`
- `runs/stable-cleanroom-20260616/doctor_offline.{json,txt}`
- `runs/stable-cleanroom-20260616/doctor_quick.{json,txt}`
- `runs/stable-cleanroom-20260616/doctor_full.{json,txt}`
- `runs/stable-cleanroom-20260616/status_all.{json,txt}`
- `runs/stable-cleanroom-20260616/status_runs_offline.{json,txt}`
- `runs/stable-cleanroom-20260616/published_pages_audit.{json,md,txt}`
- `runs/stable-cleanroom-20260616/url_dry_run.txt`
- `runs/stable-cleanroom-20260616/arxiv_dry_run.txt`
- `runs/stable-cleanroom-20260616/finalize_dry_run.txt`
- `runs/stable-cleanroom-20260616/stable-cleanroom-url-smoke/` (dry-run stubs)
- `runs/stable-cleanroom-20260616/stable-cleanroom-arxiv-smoke/` (dry-run stubs)

## FILES_MODIFIED

- `README.md` — small wording update: keep v0.3.0-alpha as `current`, add
  a v0.3.0 row to the version table marked as `deferred`. Quick Start
  unchanged.
- `README.zh-CN.md` — same version-table update; footer unchanged
  (still v0.3.0-alpha, since v0.3.0 stable was not released).
- `CHANGELOG.md` — `v0.3.0` entry marked as **deferred** with a
  cross-link to this report.
- `docs/STABLE_READINESS_CHECKLIST.md` — note that v0.3.0 stable was
  deferred; the v0.3.0-alpha row is still the latest released.
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — note that
  v0.3.0 stable was deferred.
- `skills/paper-three-pass-reader/docs/USAGE.md` — same.
- `skills/paper-three-pass-reader/docs/STATUS_AND_DOCTOR.md` — same.

The user will see in the version table that v0.3.0 is a deferred row
between v0.3.0-alpha and the next v0.3.x release.

## COMMIT

`Stage v0.3.0 stable cleanroom artifacts (release deferred)`

This commit adds the cleanroom artifacts (3 docs, 3 doctor JSONs + 3
text logs, 2 status JSONs + 2 text logs, published_pages_audit.{json,md,txt},
validate.log, 3 dry-run logs) but does not touch the historical
backlog. The working tree remains dirty for the user's decision.

## PUSH

`git push origin main`

## TAG

**None** — per the spec, the v0.3.0 tag is not created because the
release decision is `No`. `v0.3.0-alpha` remains the latest released
tag.

## RELEASE

**None** — no GitHub Release for v0.3.0 is created. The deferred release
notes live at `docs/RELEASE_NOTES_v0.3.0.md` for the user to promote to
the actual release notes once the WARN is resolved.

## LIMITATIONS

- `p3pr doctor` reports a `git_working_tree` WARN that blocks the v0.3.0
  stable release. The WARN is accurate (the tree really is dirty) and
  the historical backlog is documented but not yet committed.
- The cleanroom artifacts from this phase (`runs/stable-cleanroom-20260616/`)
  are themselves added to the dirty-state on next `git status`, but only
  by 1 new untracked dir (counted as part of the 21 above). They are
  committed in this phase's single commit.
- URL + arXiv dry-runs create empty `input/` and `extracted/` stub dirs
  as a small side effect. This is the same behavior as in v0.2.18 /
  v0.3.0-alpha readiness and is not a regression.

## NEXT_USER_ACTION

Three options to unblock v0.3.0 stable:

1. **Review the historical backlog in `git status` and commit it as a
   single housekeeping commit** (e.g. `git add -A && git commit -m
   "Housekeeping: commit historical v0.2.x and v0.3.0-alpha run
   artifacts"`). Then re-run this cleanroom: doctor will report
   `git_working_tree: working tree clean` → PASS, doctor overall → PASS,
   and the cleanroom will cut v0.3.0 stable. The historical artifacts
   are clearly identifiable (4 modified files + 21 untracked dirs, all
   from prior phases); nothing in the backlog is unknown. This is the
   most honest path.

2. **Add the historical run directories to `.gitignore`** to make git
   stop tracking them going forward, then `git clean -nd` (dry run
   preview) to see what would be removed. This is safe in the sense that
   the artifacts are reproducible from the same commands, but the
   existing files would still be untracked (or removed by a follow-up
   `git clean -fd`). Doctor will then report `git_working_tree: working
   tree clean` after the cleanup, and v0.3.0 stable can be cut.

3. **Decide the WARN is acceptable and ship v0.3.0 stable as
   `PASS_WITH_WARNINGS`** with a "known historical backlog" note in the
   release notes. This deviates from the cleanroom spec's "no WARN"
   rule but preserves the v0.3.0 timeline. The user can do this by
   replying to this report with "release anyway" and a follow-up phase
   will be executed to cut the tag + release.

If the user does not respond, the next phase should wait for direction.
The historical backlog does not affect functionality, the live site is
healthy, and v0.3.0-alpha is the current `latest` release.
