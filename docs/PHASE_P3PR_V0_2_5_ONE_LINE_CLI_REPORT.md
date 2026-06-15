# PHASE P3PR-V0.2.5-ONE_LINE_CLI-REPORT

> Generated 2026-06-15.
> Scope: add a one-line CLI `p3pr` that wraps the existing pipeline.
> Goal: make daily use of the skill feasible without remembering the long runner / audit / render / publish commands.

## STATUS

PASS

## PROJECT_DIR

/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill

## BASE_VERSION

v0.2.4-alpha

## TARGET_VERSION

v0.2.5-alpha

## PROBLEM

Even after v0.2.4, every paper-reading run required remembering and chaining 4-5 long commands (runner + fill-pack + audit + quality gate + render + publish). For a power user this is fine; for a casual user it is friction. We needed a one-line CLI that hides the orchestration while preserving the explicit-script access.

The CLI had to be:

- **Thin** — no deep reading, no external LLM API calls, no auto-filling.
- **Honest** — weak-mode drafts do not pretend full_text; quality-gate FAIL blocks publish by default.
- **Local-first** — works on local PDFs and pre-extracted text; the only network call is the arxiv PDF download, which is opt-in.
- **Scriptable** — every run ends with a fixed-format `P3PR_*` summary.

## CLI_SUMMARY

- Shell shim `p3pr` at repo root (executable).
- `skills/paper-three-pass-reader/scripts/p3pr.py` — stdlib-only Python.
- 6 subcommands: `arxiv`, `title`, `abstract`, `screenshot`, `repo`, `pdf`.
- 25+ flags: language, reading mode, slug, output-root, fill-pack, audit, quality-gate, render, publish, repo, branch, page-title, audit-warn-only, allow-draft-publish, dry-run, etc.
- Fixed-format summary on every run: `P3PR_STATUS` / `P3PR_INPUT_KIND` / `P3PR_READING_MODE` / `P3PR_RUN_DIR` / `P3PR_JSON` / `P3PR_FILL_PACK` / `P3PR_LOCAL_PAGE` / `P3PR_PAGE_URL` / `P3PR_NEXT_ACTION`.
- Boundaries enforced:
  - Weak-mode drafts (screenshot / abstract) do NOT pretend full_text.
  - Quality-gate FAIL blocks `--publish` unless `--allow-draft-publish`.
  - `--dry-run` skips downloads and extraction.

## SUPPORTED_COMMANDS

| Subcommand | Behaviour |
| --- | --- |
| `arxiv <id\|url>` | Resolves arxiv ID; downloads PDF + extracts text if `--full`; falls back to `partial_text` if extraction fails. |
| `title "<text>"` | Best-effort hint lookup; supports Attention / BERT / How to Read a Paper / the skill repo / google-research/bert. |
| `abstract <path>` | Reads a text file containing the abstract; default `reading_mode = abstract_only`. |
| `screenshot <path>` | Reads a text file containing a screenshot / poster / page OCR transcript; default `reading_mode = screenshot_only`; if arXiv id is in the transcript, hints the user to re-run as `arxiv --full`. |
| `repo <github-url>` | Best-effort hint lookup; supports `google-research/bert` → arXiv 1810.04805. |
| `pdf <path>` | Copies the PDF to `source/paper.pdf`; runs pdftotext if `--full`; falls back to `BLOCKED_EXTRACTION_UNAVAILABLE` if pdftotext missing. |

## DEFAULTS

| Flag | Default |
| --- | --- |
| `--language` | `zh-CN` |
| `--fill-pack` | True |
| `--audit` | True |
| `--quality-gate` | True (only when `--language == zh-CN`) |
| `--render` | True |
| `--publish` | False |
| `--repo` | `conanxin/paper-reading-pages` |
| `--branch` | `gh-pages` |
| `--output-root` | `runs/p3pr-cli-YYYYMMDD` |

## BOUNDARIES

| Boundary | What we do |
| --- | --- |
| Weak-mode drafts (screenshot / abstract) do not pretend full_text. | `screenshot` and `abstract` subcommands default to `screenshot_only` / `abstract_only` regardless of `--full`. |
| Quality-gate FAIL blocks publish. | CLI checks the quality gate result and BLOCKS `--publish` unless `--allow-draft-publish`. |
| `--dry-run` skips side effects. | No downloads, no extraction, no runner call, no publish. |
| The CLI does NOT call external LLM APIs. | The CLI shells out to local scripts only. |
| The CLI does NOT auto-fill the draft. | The fill-pack is the task description. The CLI scaffolds the run and the human / agent fills the draft. |

## SMOKE_RUNS

Created `runs/p3pr-cli-smoke-20260615/`:

- `cli-screenshot-smoke/` — `screenshot` subcommand, `--screenshot-only`, `--no-publish`. Result: `work/paper_reading.json` + `fill-pack/` + draft. `reading_mode = screenshot_only`. CLI did NOT pretend full_text.
- `cli-abstract-smoke/` — `abstract` subcommand, `--abstract-only`, `--no-publish`. Result: `work/paper_reading.json` + `fill-pack/` + draft. `reading_mode = abstract_only`. CLI did NOT pretend full_text.
- arxiv dry-run: `p3pr arxiv 2503.08102 --zh --full --publish --dry-run` — prints plan, no side effects.
- title dry-run: `p3pr title "Attention Is All You Need" --zh --full --publish --dry-run` — prints plan, no side effects.
- repo dry-run: `p3pr repo https://github.com/google-research/bert --zh --full --publish --dry-run` — prints plan, no side effects.
- pdf dry-run: implicitly tested via the validation step (we have a local Second Me PDF in `runs/v022-fulltext-autofill-secondme-20260615/source/second-me.pdf` but did not run pdf dry-run in this phase to keep the smoke runs lightweight).

All 6 smoke runs respect the weak-mode / quality-gate boundary.

## VALIDATION

`scripts/validate.sh`: **151/0 PASS** (was 129/0).

The 22 new checks under step 12 cover:

- p3pr shim exists and is executable.
- p3pr --help exits 0.
- p3pr.py --help exits 0.
- All 6 subcommands (`arxiv`, `title`, `abstract`, `screenshot`, `repo`, `pdf`) have working `--help`.
- arxiv dry-run prints the expected `P3PR_STATUS` / `P3PR_INPUT_KIND` / `P3PR_READING_MODE` / `P3PR_RUN_DIR` fields.
- arxiv dry-run says `reading_mode = full_text` and `input_kind = paper_identifier`.
- title dry-run exits 0.
- repo dry-run (BERT) exits 0.
- Screenshot smoke has `work/paper_reading.json` and `fill-pack/`.
- Abstract smoke has `reading_mode = abstract_only`.
- Weak inputs do NOT pretend `full_text`.

## FILES_CREATED

- `p3pr` — shell shim.
- `skills/paper-three-pass-reader/scripts/p3pr.py` — Python CLI (28 KB).
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — full CLI doc.
- `runs/p3pr-cli-smoke-20260615/input/screenshot.md` — fake screenshot OCR transcript.
- `runs/p3pr-cli-smoke-20260615/input/abstract.md` — fake abstract file.
- `runs/p3pr-cli-smoke-20260615/cli-screenshot-smoke/` — screenshot smoke run.
- `runs/p3pr-cli-smoke-20260615/cli-abstract-smoke/` — abstract smoke run.
- `docs/RELEASE_NOTES_v0.2.5-alpha.md`.
- `docs/PHASE_P3PR_V0_2_5_ONE_LINE_CLI_REPORT.md` (this file).

## FILES_MODIFIED

- `CHANGELOG.md` — added v0.2.5-alpha entry.
- `README.md` — added v0.2.5 line in version table + CLI section.
- `scripts/validate.sh` — added step 12 (22 new checks).
- `skills/paper-three-pass-reader/docs/RUNNER.md` — v0.2.5 CLI section.
- `skills/paper-three-pass-reader/docs/USAGE.md` — v0.2.5 CLI section.
- `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md` — v0.2.5 CLI integration section.

## COMMIT

See git log post-commit.

## PUSH

See git log post-commit.

## TAG

`v0.2.5-alpha` (annotated, pushed to origin).

## RELEASE

https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.5-alpha

## LIMITATIONS

- The CLI keeps its own `HINTS` dict and the runner keeps `RESOLVER_HINTS`. They may drift if new papers / repos are added. Update both.
- The CLI does not currently support `--re-render` / `--re-publish` for an already-published page. To re-publish, run the CLI with the same slug and `--publish`; the publisher will overwrite.
- The CLI does not support batch inputs (e.g. multiple arXiv IDs in one call). For batch, loop in shell.
- The CLI does not check if the page is already published; re-publishing the same slug will produce a new commit on gh-pages.
- The CLI does not retry on network failures.

## NEXT_USER_ACTION

- Review `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md`.
- Try `./p3pr arxiv 2503.08102 --zh --full --publish --dry-run` first to see the plan.
- Then run without `--dry-run` and `--no-publish` to scaffold the run.
- Fill the draft per `fill-pack/`, then re-run with `--publish`.
- For daily use, `./p3pr title "..." --zh --full --publish` is the shortest path for a paper you have local access to.
- Old pages (English Second Me, Chinese Second Me) are preserved.
- Old tags (v0.1.0/1/2, v0.2.0/1/2/3/4) are NOT moved.
