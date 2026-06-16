# paper-three-pass-reader v0.2.14-alpha

## Summary

This release adds a `p3pr url <url>` subcommand that lets P3PR fetch any
HTML academic article, talk transcript, or research-method post on the
public web and run the full runner / fill-pack / audit / quality-gate /
render / publish pipeline. No more hand-wired `curl + html.parser + runner`.

The CLI is **stdlib-only**: it does not call external LLM APIs, does not need
`requests` / `beautifulsoup4` / `playwright`, and uses Python's built-in
`html.parser` for text extraction. It runs the existing scripts in the
right order, with the right flags.

## Included

- **`p3pr url <url>` subcommand** (7th subcommand, alongside `arxiv / title /
  abstract / screenshot / repo / pdf`). Fetches the URL, extracts plain
  text via stdlib `html.parser`, writes the run layout, and runs the
  pipeline.
- **`--input` + `--input-file` together** in the runner. The CLI passes
  the URL as `--input` (audit trail) and the extracted text path as
  `--input-file` (body). Both are recorded in `input/input.md`. Callers
  that pass only one continue to work.
- **Reading-mode discipline for URL input.** HTML extraction ≥ 800 chars
  → `full_text`; < 800 chars → `partial_text`; PDF without `pdftotext` →
  `partial_text` (never claim `full_text` on a PDF without text).
- **New `P3PR_SOURCE_URL:` line** in the standard summary output.
- **New `--authors` and `--year` flags** exposed at the CLI level
  (previously only available on the runner directly).
- **`input_kind=paper_url` workflow documented end-to-end.** The runner
  records the URL in `paper_metadata.identifiers.url`,
  `paper_metadata.source_kind = "paper_url"`, and the source_resolution
  block via the CLI overlay.
- **Validation step 20** with 17 new sub-checks covering `p3pr url --help`,
  dry-run summary, real-URL smoke run layout, and the existing 6
  subcommands' `--help` (no regressions). Validation is now 261/0 PASS
  (was 242/0 PASS at v0.2.13-alpha).
- **Real-URL smoke run.** `runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/`
  — fetched Hamming's *You and Your Research*
  (https://www.cs.virginia.edu/~robins/YouAndYourResearch.html), extracted
  78,593 chars of text via stdlib HTML parser, ran the full pipeline.
- **Live URL smoke page published.** A separate slug
  `you-and-your-research-url-smoke-cn` was published to
  `conanxin.github.io/paper-reading-pages/you-and-your-research-url-smoke-cn/`
  (does NOT overwrite the formal `you-and-your-research-cn` page). Live
  audit after the publish: `pages=11 pass=11 warn=0 fail=0`.

## Compatibility

- **Existing pages remain readable.** The only consumer page newly
  published is the URL smoke page (`you-and-your-research-url-smoke-cn`).
- **Existing subcommands (`arxiv / title / abstract / screenshot / repo /
  pdf`) are unchanged.**
- **The runner's old "only one of --input / --input-file" check is
  removed** in favour of allowing both. Callers that passed exactly one
  continue to work.
- **No old tags moved.** v0.2.10-alpha / v0.2.12-alpha / v0.2.13-alpha
  stay at their original commits.

## What `p3pr url` is and is not

- ✅ Suitable for: HTML academic articles, talk transcripts, lecture
  notes, long-form essays, research-method posts, plain HTML paper
  web pages.
- ❌ Not suitable for: JavaScript-heavy SPA pages (the stdlib parser
  does not execute JS). For those, pre-extract with a JS-capable tool
  and use `./p3pr abstract path/to/text.md` instead.
- ❌ Not suitable for: a PDF-only URL with no `pdftotext` on PATH. The
  CLI saves the PDF to `source/source.pdf` but cannot extract text. Use
  `./p3pr pdf path/to/local.pdf` for that.

## Files touched (this release)

| File | Purpose |
|---|---|
| `skills/paper-three-pass-reader/scripts/p3pr.py` | New `handle_url()`, `_HTMLTextExtractor`, `_fetch_url`, `_looks_like_pdf`; new `P3PR_SOURCE_URL:` summary line; new `--authors` / `--year` top-level flags; `input_kind=paper_url` workflow. |
| `skills/paper-three-pass-reader/scripts/run_paper_reading.py` | Accept `--input` and `--input-file` together; relaxed old "only one of" check; new `body_text` capture for the audit-trail input.md. |
| `scripts/validate.sh` | Step 20 with 17 new sub-checks for the `url` subcommand. |
| `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` | New "The 7 subcommands" section with the `url` example. |
| `skills/paper-three-pass-reader/docs/USAGE.md` | New "v0.2.14-alpha: p3pr url subcommand" section with reading-mode discipline, run layout, examples. |
| `skills/paper-three-pass-reader/docs/RUNNER.md` | New "v0.2.14 — `--input` and `--input-file` together + `paper_url`" section. |
| `skills/paper-three-pass-reader/docs/SOURCE_RESOLUTION.md` | New "v0.2.14-alpha: URL input source resolution" section. |
| `README.md`, `README.zh-CN.md` | New v0.2.14-alpha row in the version table. |
| `CHANGELOG.md` | New `v0.2.14-alpha` section. |
| `docs/RELEASE_NOTES_v0.2.14-alpha.md` | This file. |
| `docs/PHASE_P3PR_V0_2_14_URL_SUBCOMMAND_REPORT.md` | Final phase report. |
| `runs/p3pr-url-smoke-20260616/` | Local real-URL smoke run. |
| `runs/published-pages-audit-20260615-url-smoke/` | Live audit JSON + Markdown after the URL smoke page is published. |

## Upgrade notes

- `./p3pr url` is purely additive. Existing pipelines that do not use it
  are unaffected.
- The runner's relaxed `--input` + `--input-file` check is backwards-
  compatible. Old callers passing only `--input` work as before; the
  new code path is exercised only when both are present (i.e. by `p3pr url`).
- HTML pages with < 800 chars of extracted text (error pages,
  paywalled redirects, JS-only SPAs) get `partial_text`, not `full_text`.
  This is intentional and matches the existing reading-mode discipline.

## Rollback

v0.2.14-alpha only adds the `url` subcommand, the `--input + --input-file`
relaxation in the runner, and step 20 in validation. Reverting to
v0.2.13-alpha restores the old behaviour. The published smoke page
(`you-and-your-research-url-smoke-cn`) is not auto-deleted but does not
interfere with anything if kept.
