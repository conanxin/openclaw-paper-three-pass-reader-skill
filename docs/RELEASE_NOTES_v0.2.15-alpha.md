# Release Notes — paper-three-pass-reader v0.2.15-alpha

**Tag:** `v0.2.15-alpha`
**Date:** 2026-06-16
**Status:** alpha (consumer-tested via dogfood)

## What changed

v0.2.15-alpha is a small, surgical release driven by the v0.2.15 dogfood phase
(`docs/PHASE_P3PR_V0_2_15_URL_SUBCOMMAND_DOGFOOD_REPORT.md`). It does not add new
user-facing features. It fixes one real bug surfaced by the dogfood.

### Bug fix: `p3pr ... --publish` no longer pushes a 404 stub when render was skipped

**Symptom.** Running `./p3pr url <url> --publish` (or any other subcommand) when the
runner correctly skipped render — because the audit (or zh-CN quality gate) FAILED
— would push an empty `paper-reading-output/` directory to `gh-pages`. The result was a
page entry in `published_pages.json` with no `index.html`, i.e. a 404 on the live site
even though the CLI exited 0 with `P3PR_STATUS: PASS`.

**Why it happened.** `run_paper_reading.py` correctly skips its own publish path when
audit FAILED, prints `[skip] publish skipped because audit FAILED.`, and returns 0.
`p3pr.py` runs the runner as a subprocess, sees rc=0, and then **re-invokes** the
publisher for its own `--publish` step — without checking whether the render actually
produced an `index.html`. The runner's "skip" message was lost in the CLI flow.

**Fix.** `skills/paper-three-pass-reader/scripts/p3pr.py` now checks
`paper-reading-output/index.html` exists before calling the publisher. If it doesn't,
the CLI BLOCKs hard with `P3PR_STATUS: BLOCKED`, prints a clear "render was skipped
because the audit (or quality gate) FAILED" message, and exits 1. The new BLOCK
applies **even when `--allow-draft-publish` is set**, because a missing `index.html` is
a publish-shaped bug the user almost certainly did not intend. The user is pointed at
the fill-pack and instructed to re-run with `--no-publish` first, or pass
`--audit-warn-only` to force render.

### Regression guard

`scripts/validate.sh` step 20l adds two new sub-checks:

- `v0.2.15-alpha: p3pr url blocks publish when render was skipped (rc=1)` — runs a real
  `p3pr url` against the smoke URL with `--allow-draft-publish --publish`, expects rc≠0
  and a stderr line mentioning "render was skipped".
- `v0.2.15-alpha: no empty stub on gh-pages for blocked run` — confirms the slug
  `v215-empty-stub-check` does not appear on `gh-pages` (HTTP 200) after the blocked
  run.

Total validation count: 261 → **263** (status PASS).

### Cleanup of the broken stub

The dogfood that surfaced this bug created a broken stub at
`https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-cn/`
on `gh-pages`. That directory contained only `.nojekyll` (no `index.html`) and the
manifest entry pointed at a 404. As part of v0.2.15, the stub directory and its
manifest entry were removed from the `gh-pages` branch. The live
`published-pages-audit` is back to `11/11 PASS, 0 fail, 0 warn`.

## How to use (no change for end-users)

There is no new user-facing flag or subcommand. v0.2.15-alpha is the same
`p3pr ...` surface as v0.2.14-alpha, with one extra internal guarantee:

> If you see `P3PR_STATUS: BLOCKED` with the new v0.2.15 message
> `render was skipped (audit/qg FAILED)`, the fix is working as intended.
> Follow the fill-pack, re-run with `--no-publish`, then publish.

## Upgrading

Pull `v0.2.15-alpha`, no migration steps. Existing fill-packs, drafts, and rendered
pages are untouched.

## Validation

```
$ bash scripts/validate.sh
...
PASS: 263    FAIL: 0
STATUS: PASS
```

## Audit

```
$ python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
    --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
    --site-root https://conanxin.github.io/paper-reading-pages \
    --include-root --warn-only
[audit] overall=PASS pages=11 pass=11 warn=0 fail=0
```

## Acknowledgments

Reported by the v0.2.15 dogfood phase (operator: Conan Xin, local Hermes agent).
