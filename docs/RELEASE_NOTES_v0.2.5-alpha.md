# Release Notes — v0.2.5-alpha

## Overview

Adds a one-line CLI `p3pr` that wraps the existing pipeline (runner + fill-pack + audit + zh-CN quality gate + render + publish) into a single command.

The CLI does NOT do any deep reading itself and does NOT call external LLM APIs. It is a thin shell shim. The reading is the fill-pack job; the CLI scaffolds the run, runs the structural audit + quality gate, renders the page, and (optionally) publishes.

## Changes

### New `p3pr` shell shim

`p3pr` at the repo root, executable. It exec's `python3 skills/paper-three-pass-reader/scripts/p3pr.py`.

### New `p3pr.py` Python CLI

`skills/paper-three-pass-reader/scripts/p3pr.py`. Stdlib-only. Subcommands:

- `arxiv <id|URL>` — arXiv ID or URL; downloads PDF + extracts text if `--full`.
- `title "<text>"` — best-effort hint lookup.
- `abstract <path>` — path to a text file containing the abstract.
- `screenshot <path>` — path to a text file containing a screenshot / poster / page OCR transcript.
- `repo <github-url>` — best-effort hint lookup.
- `pdf <path>` — local PDF.

### Flags

- `--zh` / `--en` (or `--language zh-CN|en`, default `--zh`).
- `--full` / `--partial` / `--abstract-only` / `--screenshot-only` — force reading mode.
- `--slug <slug>` / `--output-root <dir>` / `--title "<text>"`.
- `--publish` (default off) / `--no-publish`.
- `--repo <owner/repo>` (default `conanxin/paper-reading-pages`).
- `--branch <name>` (default `gh-pages`).
- `--page-title "<text>"` — override the title in the published page.
- `--fill-pack` / `--no-fill-pack` (default on).
- `--audit` / `--no-audit` (default on).
- `--quality-gate` / `--no-quality-gate` (default on; only effective with `--zh`).
- `--render` / `--no-render` (default on).
- `--audit-warn-only` — treat audit WARN as PASS for the runner's render block.
- `--allow-draft-publish` — allow publishing even when quality gate FAILS.
- `--dry-run` — print the plan; do not run anything (no downloads, no extraction, no publishing).

### Defaults

| Flag | Default |
| --- | --- |
| `--language` | `zh-CN` |
| `--fill-pack` | True |
| `--audit` | True |
| `--quality-gate` | True (only when `language == zh-CN`) |
| `--render` | True |
| `--publish` | False |
| `--repo` | `conanxin/paper-reading-pages` |
| `--branch` | `gh-pages` |
| `--output-root` | `runs/p3pr-cli-YYYYMMDD` |

### Boundaries enforced

- Weak-mode drafts (screenshot_only / abstract_only) do NOT pretend full_text.
- For arxiv / pdf inputs, `--full` downloads the PDF and runs pdftotext. If extraction fails, the CLI downgrades to `partial_text` and prints the reason.
- For weak-mode drafts, `--publish` is BLOCKED by default because the quality gate cannot pass without filling the draft. Pass `--allow-draft-publish` to publish anyway.
- `--dry-run` skips downloads and extraction.

### Fixed-format summary

Every CLI run ends with a fixed-format summary:

```
P3PR_STATUS: PASS|WARN|BLOCKED|DRY_RUN
P3PR_INPUT_KIND: paper_identifier|...
P3PR_READING_MODE: full_text|abstract_only|...
P3PR_RUN_DIR: ...
P3PR_JSON: ...
P3PR_FILL_PACK: ...
P3PR_LOCAL_PAGE: ...
P3PR_PAGE_URL: ...
P3PR_NEXT_ACTION: ...
```

The status field is one of `PASS`, `WARN`, `BLOCKED`, or `DRY_RUN`. `WARN` means the run was created but content is shallow (e.g. weak-mode draft, quality-gate WARN). `BLOCKED` means the publish step was refused because of quality-gate FAIL (without `--allow-draft-publish`).

### CLI smoke runs

`runs/p3pr-cli-smoke-20260615/` has:

- 2 local smoke runs (screenshot + abstract) — produce run layout + fill-pack + draft JSON.
- 4 dry-runs (arxiv / title / repo / pdf) — print plan only, no side effects.

All 6 smoke runs respect the weak-mode / quality-gate boundary: weak inputs do NOT pretend full_text.

### Validation extended

`scripts/validate.sh` now has 151 checks (was 129). New step 12 covers:

- p3pr shim executable.
- p3pr help works.
- All 6 subcommands have working `--help`.
- arxiv dry-run prints the expected `P3PR_*` fields.
- title / repo dry-runs exit 0.
- Screenshot smoke has `work/paper_reading.json` + `fill-pack`.
- Abstract smoke has `reading_mode = abstract_only`.
- Weak inputs do not pretend `full_text`.

### Documentation

- New `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md`.
- `README.md`, `CHANGELOG.md`, `skills/paper-three-pass-reader/docs/RUNNER.md`, `USAGE.md`, `ZH_CN_QUALITY_GATE.md` updated.
- New `docs/RELEASE_NOTES_v0.2.5-alpha.md` (this file).
- New `docs/PHASE_P3PR_V0_2_5_ONE_LINE_CLI_REPORT.md`.

## Design notes

- The CLI is a **thin wrapper**. It does NOT call external LLM APIs. The reading is the fill-pack job.
- Subcommands share the same flag set. The user can put flags before or after the subcommand.
- The CLI keeps its own copy of the resolver hints (`HINTS` dict) so dry-runs can resolve without invoking the runner.
- The CLI never modifies the existing scripts; it only orchestrates them.
- The CLI's `HINTS` and the runner's `RESOLVER_HINTS` may drift if new papers / repos are added. Update both.

## Validation

- `scripts/validate.sh`: **151/0 PASS** (was 129/0).

## Migration guide

Existing workflows that use the runner / audit / render / publish directly are unchanged. The CLI is additive. To migrate:

```bash
# Before (v0.2.4):
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "arXiv:2503.08102" --input-kind paper_identifier --slug myslug \
  --output-root runs/myrun --reading-mode full_text --language zh-CN \
  --fill-pack --audit --quality-gate --render
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/myrun/myslug/work/paper_reading.json --quality-gate
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input runs/myrun/myslug/work/paper_reading.json
# (fill draft, re-render, re-publish manually)

# After (v0.2.5):
./p3pr arxiv 2503.08102 --zh --full --slug myslug --output-root runs/myrun --no-publish
# (fill draft per fill-pack)
./p3pr arxiv 2503.08102 --zh --full --slug myslug --output-root runs/myrun --publish
```

The CLI prints `P3PR_*` summaries to make it easy to script on top of.

## Artifacts

- Skill repo: `conanxin/openclaw-paper-three-pass-reader-skill`
- Tag: `v0.2.5-alpha`
- CLI shim: `p3pr`
- CLI script: `skills/paper-three-pass-reader/scripts/p3pr.py`
- CLI smoke: `runs/p3pr-cli-smoke-20260615/`
- Old pages preserved: https://conanxin.github.io/paper-reading-pages/second-me-fulltext-autofill/ and https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/
- Release: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.5-alpha
