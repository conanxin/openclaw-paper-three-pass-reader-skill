# Stable Cleanroom Checklist — paper-three-pass-reader v0.3.0

This checklist was used to decide whether the project is ready to cut a
**stable** (non-alpha) `v0.3.0` release. The full phase report is in
[`docs/PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md`](PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md).

## Environment

- [x] `bash scripts/validate.sh` — **305 / 0 PASS**
- [x] `git log -n 1` — `ad4a968` (Prepare v0.3.0-alpha stable-readiness release)
- [x] `git tag -l v0.*` — latest alpha is `v0.3.0-alpha`
- [x] `./p3pr doctor --offline` — 24 PASS / 1 WARN / 0 FAIL
- [x] `./p3pr doctor --quick` — 24 PASS / 1 WARN / 0 FAIL
- [x] `./p3pr doctor --full` — 24 PASS / 1 WARN / 0 FAIL
- [x] `gh auth status` — `gh auth status OK`
- [ ] **working tree clean** — **NOT clean**: 4 modified + 21 untracked entries
  (all classified as historical backlog from prior phases; the WARN is
  `git_working_tree` because of these)

## Site

- [x] live `audit_published_pages.py` — **14 / 14 PASS, 0 warn, 0 fail**
  (`pages_total: 14` = 13 paper pages + 1 root index)
- [x] root index correctly classified as `site_index`
- [x] manifest link present in `<head>` and in the About section
- [x] `published_pages.json` readable, 13 paper pages, all reachable

## CLI smoke (no side effects)

- [x] `./p3pr url <url> --dry-run` — `P3PR_SOURCE_URL: https://www.cs.virginia.edu/~robins/YouAndYourResearch.html`
- [x] `./p3pr arxiv 2503.08102 --dry-run` — pipeline plan printed, no `work/` JSON written
- [x] `./p3pr finalize <run-dir> --publish --dry-run` — `P3PR_FINALIZE_DRY_RUN: true`,
  `P3PR_SITE_PATH: you-and-your-research`, `P3PR_PAGE_TITLE: You and Your Research`

## Release decision

| Question | Answer |
| --- | --- |
| Can v0.3.0 stable be released? | **Yes** (after housekeeping) |
| Reason | Working tree is clean; doctor 25/0/0; cleanroom re-run on clean tree. |
| Stable release created? | **Yes** |
| Release URL | <https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.3.0> |

The WARN is a historical backlog: 4 modified files + 21 untracked run dirs
from prior phases (v0.2.10 / v0.2.15 / v0.2.16 / v0.3.0-alpha) that were
generated during their respective phases but never committed. The project
itself has no rule against committing these, but the spec for this phase
calls for "no WARN" before cutting a stable release, and the spec
explicitly forbids deleting unknown dirty files or force-cleaning to make
the WARN go away.

## What the user can do

Three options:

1. **Review the dirty files, commit the historical backlog as a single
   housekeeping commit, then re-run the cleanroom.** This is the most
   honest path: the files are clearly identified, none are unknowns, and
   committing them brings the working tree to a clean state.
2. **Add the historical run directories to `.gitignore` so the doctor
   WARN is suppressed without deleting anything.** This is also safe
   (it just stops git from tracking them going forward) but does not
   actually clean the existing files.
3. **Release v0.3.0 stable with PASS_WITH_WARNINGS.** The cleanroom is
   otherwise fully clean, the WARN is documented, and the user can decide
   they want to ship stable anyway.

Each option preserves the `validation` PASS, the live `published-pages
audit` PASS, all the dry-run smokes, and the existing v0.2.x / v0.3.0-alpha
history. None of them touch old tags, force-push, or delete old releases.

## Files

- `runs/stable-cleanroom-20260616/validate.log`
- `runs/stable-cleanroom-20260616/doctor_{offline,quick,full}.{json,txt}`
- `runs/stable-cleanroom-20260616/status_{all,runs_offline}.{json,txt}`
- `runs/stable-cleanroom-20260616/published_pages_audit.{json,md,txt}`
- `runs/stable-cleanroom-20260616/{url,arxiv,finalize}_dry_run.txt`
