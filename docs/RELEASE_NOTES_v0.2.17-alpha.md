# paper-three-pass-reader v0.2.17-alpha

## Summary

This release adds `p3pr finalize <run-dir>`, the second-stage CLI command for completing a filled paper-reading run. `finalize` chains audit → zh-CN quality gate → render → optional publish → optional published-pages audit into a single command with hard guards at every step.

## Why

Before v0.2.17, after a human or agent filled `work/paper_reading.json`, users still had to manually chain the audit, quality gate, render, publish, and published-pages audit commands — and had to remember the v0.2.15 hard guard against publishing when `paper-reading-output/index.html` is missing. `p3pr finalize` turns that second stage into one command with the guards built in.

## Included

- New `./p3pr finalize <run-dir>` subcommand
- Audit orchestration
- zh-CN quality gate orchestration (auto-detected from run dir naming or explicit `--lang`)
- Render orchestration to `<run-dir>/paper-reading-output/`
- Optional publish orchestration via `publish_output_to_github.sh`
- Optional published-pages audit after publish
- `--dry-run` support
- Fixed-format `P3PR_FINALIZE_*` summary output on every exit path
- Hard guard against publishing when `paper-reading-output/index.html` is missing (carried from v0.2.15)
- Hard guard against missing `work/paper_reading.json` (BLOCK)
- Hard guard against audit FAILED (BLOCK)
- Hard guard against quality-gate FAILED unless `--allow-draft-publish`
- Hard guard against quality-gate WARN unless `--allow-warnings`
- Validation coverage for finalize dry-run, local finalize, publish path, and block paths (16 new sub-checks, total 279/0 PASS)

## Dogfood

The command was dogfooded on the filled URL run for Richard Hamming's *You and Your Research*:

- Live dogfood page: <https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-finalize-cn/>
- Live published-pages audit: 12/12 PASS, 0 fail, 0 warn

## Compatibility

- Existing `p3pr url`, `arxiv`, `title`, `abstract`, `screenshot`, `repo`, and `pdf` commands remain unchanged.
- Existing run directories remain compatible — finalize reads whatever the runner wrote.
- Existing pages remain published.
- No old tags moved.
- No old releases deleted.

## Flags

| Flag | Purpose |
| --- | --- |
| `--publish` / `--no-publish` | Toggle publish step (default: `--no-publish`) |
| `--repo <repo>` | Target GitHub Pages repo (default: `conanxin/paper-reading-pages`) |
| `--branch <branch>` | Target branch (default: `gh-pages`) |
| `--site-path <path>` | Override the site subpath (default: `<run-dir-basename>`) |
| `--page-title <title>` | Override the page title |
| `--allow-warnings` | Allow zh-CN quality-gate WARN to proceed |
| `--allow-draft-publish` | Allow zh-CN quality-gate FAILED (draft) to proceed |
| `--skip-quality-gate` | Skip the quality gate step entirely |
| `--skip-published-audit` | Skip the published-pages audit step |
| `--published-audit` / `--no-published-audit` | Explicitly toggle the post-publish audit |
| `--dry-run` | Print a `P3PR_FINALIZE_DRY_RUN` plan block, no side effects |
| `--json-output <path>` | Write the finalize summary JSON to a file |
