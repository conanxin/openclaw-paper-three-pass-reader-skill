# paper-three-pass-reader v0.3.0 — DEFERRED

## Summary

This is a **deferred** release notes file. v0.3.0 stable was not cut in
this phase because the cleanroom still has a `git_working_tree` WARN.

## Why deferred

`bash scripts/validate.sh` is 305 / 0 PASS.
The live `published-pages audit` is 14 / 14 PASS, 0 warn, 0 fail.
`./p3pr doctor --offline` / `--quick` / `--full` all report **24 PASS / 1 WARN / 0 FAIL**.
URL dry-run + arXiv dry-run + finalize dry-run all PASS without side effects.

The single WARN is `git_working_tree` — 4 modified files and 21 untracked
dirs from prior phases that were never committed. The cleanroom spec for
this phase calls for "no WARN" before a stable release, and explicitly
forbids deleting unknown dirty files or force-cleaning to suppress the
WARN.

The phase report is in
[`PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md`](PHASE_P3PR_V0_3_0_STABLE_CLEANROOM_REPORT.md)
and lists three concrete options the user can take to unblock v0.3.0.

## What was ready to be released (had it been cut)

- One-line input commands: `url`, `arxiv`, `pdf`, `title`, `abstract`,
  `screenshot`, `repo`.
- Two-stage workflow with `p3pr finalize`.
- zh-CN-first reading pages.
- fill-pack workflow.
- audit and zh-CN quality gate.
- structured source resolution.
- GitHub Pages publishing.
- published-pages audit.
- `p3pr status` and `p3pr doctor` (read-only observability).
- site root index and manifest discovery.

## Stability invariants verified

- v0.2.15 publish-gate: `p3pr --publish` BLOCKs on missing
  `paper-reading-output/index.html` (validated by step 20l).
- v0.2.17 finalize BLOCKs on missing `work/paper_reading.json`
  (validated by step 22e).
- v0.2.18 finalize UX: auto site-path / page-title inference, richer
  summary (validated by step 22).
- v0.2.19 status / doctor are read-only, never auto-fix (validated by
  step 23).
- v0.3.0-alpha bug fix: doctor summary counter now correctly lowercases
  check status (was always 0/0/0 before the fix).

## Compatibility

If/when v0.3.0 stable is cut, the compatibility promise will be:

- Existing v0.2.x and v0.3.0-alpha run directories remain compatible.
- Existing Pages remain published.
- Existing tags are not moved.

## Notes

This deferred release does not add new features. It marks the current
workflow as the candidate for v0.3.0 stable pending the working-tree
backlog decision.
