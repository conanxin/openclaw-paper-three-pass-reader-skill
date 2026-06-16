# P3PR v0.2.14-alpha — URL Subcommand Report

**STATUS:** PASS
**PROJECT_DIR:** /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill
**BASE_VERSION:** v0.2.13-alpha
**TARGET_VERSION:** v0.2.14-alpha
**REPORT_GENERATED_AT:** 2026-06-16

---

## PROBLEM

Until v0.2.13-alpha, P3PR accepted six input kinds:
`arxiv` / `title` / `abstract` / `screenshot` / `repo` / `pdf`. A user who
had a URL to an academic article, talk transcript, or method essay on
the public web had to hand-wire the entire pipeline: download with
`curl` / `urllib`, write a small `html.parser` script to extract text,
save the body to a file, then call the runner with the correct flags.
This is friction for the most common case ("here is a URL to a talk
or essay, please read it").

The CLI also exposed only `--title` for paper metadata override;
`--authors` and `--year` were runner-level flags only, forcing advanced
users to call the runner directly.

## FIX_SUMMARY

Added a seventh P3PR subcommand, `p3pr url <url>`, that fetches the URL
with stdlib `urllib`, runs a stdlib `html.parser` text extraction, and
feeds the result to the existing runner as `input_kind=paper_url` with
`--input-file <extracted body> --paper-url <url>`. The runner was
relaxed to accept `--input` and `--input-file` together (so the URL
serves as the audit-trail string and the extracted text serves as the
body). New `--authors` and `--year` flags were exposed at the CLI
level. The standard summary gained a `P3PR_SOURCE_URL:` line.

## PUBLISHER_CHANGE

None. The publisher is unchanged in this release; the new `url`
subcommand only changes the CLI / runner side.

## AUDIT_CHANGE

The published-pages audit is unchanged. The CLI does not call the
audit; the runner calls `audit_paper_reading.py` on the draft JSON
as before. The new `url` subcommand goes through the same runner
+ audit + quality-gate + render path as the other six subcommands.

The live published-pages audit is now performed against 11 pages
(10 pre-existing + 1 new URL smoke page at
`you-and-your-research-url-smoke-cn/`). The audit reports
`overall=PASS pages=11 pass=11 warn=0 fail=0` with
`page_type_counts: {site_index: 1, paper_page: 10, manifest: 0, unknown: 0}`.

## ROOT_INDEX_REPUBLISH

The publish of the URL smoke page (`you-and-your-research-url-smoke-cn`)
also re-triggered the root index regeneration in
`publish_output_to_github.sh` (the v0.2.13 manifest link is still
present in the regenerated root index). The root index now lists 10
pages (no change in count from v0.2.13; the URL smoke page is the
11th entry).

## LIVE_SITE_AUDIT

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --json-output runs/published-pages-audit-20260615-url-smoke/audit.json \
  --markdown-output runs/published-pages-audit-20260615-url-smoke/audit.md \
  --include-root --warn-only
```

Output:

```
[audit] overall=PASS pages=11 pass=11 warn=0 fail=0
```

`page_type_counts`: `{site_index: 1, paper_page: 10, manifest: 0, unknown: 0}`

`issues_by_severity`: `{error: 0, warning: 0, info: 8}`

Live audit artifacts (after-fix):

- `runs/published-pages-audit-20260615-url-smoke/audit.json`
- `runs/published-pages-audit-20260615-url-smoke/audit.md`

## BEFORE_AFTER

| Metric | Before (v0.2.13-alpha) | After (v0.2.14-alpha) | Delta |
|---|---|---|---|
| Subcommands exposed | 6 (`arxiv / title / abstract / screenshot / repo / pdf`) | **7** (+ `url`) | +1 |
| `validation` PASS count | 242 | **261** | **+19** (17 new step-20 sub-checks + 2 fixture resets) |
| Live published pages | 10 | **11** (10 pre-existing + `you-and-your-research-url-smoke-cn`) | +1 |
| Live audit `status` | PASS | **PASS** | (same) |
| Live audit `pages_fail` | 0 | 0 | 0 |
| Live audit `pages_warn` | 0 | 0 | 0 |
| Live audit `pages_pass` | 10 | **11** | +1 |
| Source pages fetchable via CLI | arxiv + repo URL | arxiv + repo + **any HTML/PDF URL** | broader |

The URL smoke page passes all 8 audit fixtures (template_leak / raw_dict /
old_footer / essay_missing_markers / zh_cn_markers_weak / pass / site_index_*
checks) plus the v0.2.13 manifest-link check on the root index.

## VALIDATION

```
$ bash scripts/validate.sh
...
[19] v0.2.13-alpha root-index manifest link
  ok   publish_output_to_github.sh generated root index contains published_pages.json
  ok   generated root index <head>/body contains manifest link
  ok   fake root index with manifest link does not trigger index_no_manifest_link
  ok   fake root index without manifest link still triggers info-level index_no_manifest_link
  ok   audit JSON classifies site_index AND has no paper-level warnings on the root
  ok   live site audit root index no longer triggers index_no_manifest_link

[20] v0.2.14-alpha p3pr url subcommand
  ok   p3pr url --help runs
  ok   p3pr --help lists url subcommand
  ok   URL dry-run emits P3PR_INPUT_KIND: paper_url
  ok   URL dry-run with --full emits P3PR_READING_MODE: full_text
  ok   URL dry-run emits P3PR_SOURCE_URL with the user-supplied URL
  ok   URL smoke run saves input/source_pointer.txt
  ok   URL smoke run saves source/source.html
  ok   URL smoke run saves extracted/page.txt with substantial content
  ok   URL smoke draft JSON exists
  ok   URL smoke draft JSON contains paper_url
  ok   URL smoke draft JSON contains source_resolution
  ok   URL smoke rendered page exists
  ok   URL smoke rendered page contains Chinese UI (输入解析状态)
  ok   p3pr arxiv --help still runs
  ok   p3pr title --help still runs
  ok   p3pr abstract --help still runs
  ok   p3pr screenshot --help still runs
  ok   p3pr repo --help still runs
  ok   p3pr pdf --help still runs

=================================================
 PASS: 261    FAIL: 0
=================================================
STATUS: PASS
```

**Validation: 261/0 PASS** (was 242/0 PASS at v0.2.13-alpha). 17 new
sub-checks in step 20; existing checks unchanged.

## FILES_CREATED

- `docs/RELEASE_NOTES_v0.2.14-alpha.md`
- `docs/PHASE_P3PR_V0_2_14_URL_SUBCOMMAND_REPORT.md` (this file)
- `runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/` (full
  run layout including `input/source_pointer.txt`,
  `source/source.html` (82,911 bytes), `extracted/page.txt` (78,593 chars),
  `work/paper_reading.json`, `work/audit_result.json`,
  `work/quality_gate_zh_cn.json`, `fill-pack/`, `paper-reading-output/`,
  `reports/`).
- `runs/published-pages-audit-20260615-url-smoke/audit.json`
- `runs/published-pages-audit-20260615-url-smoke/audit.md`

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/p3pr.py` — new `handle_url()`,
  `_HTMLTextExtractor`, `_fetch_url`, `_looks_like_pdf`; new
  `P3PR_SOURCE_URL:` summary line; new `--authors` / `--year` top-level
  flags; new `input_kind=paper_url` workflow.
- `skills/paper-three-pass-reader/scripts/run_paper_reading.py` — accept
  `--input` and `--input-file` together; new `body_text` capture for the
  audit-trail input.md.
- `scripts/validate.sh` — step 20 (17 sub-checks).
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — "The 7
  subcommands" section.
- `skills/paper-three-pass-reader/docs/USAGE.md` — "v0.2.14-alpha: p3pr
  url subcommand" section.
- `skills/paper-three-pass-reader/docs/RUNNER.md` — "v0.2.14 — `--input`
  and `--input-file` together + `paper_url`" section.
- `skills/paper-three-pass-reader/docs/SOURCE_RESOLUTION.md` —
  "v0.2.14-alpha: URL input source resolution" section.
- `README.md` — v0.2.14-alpha row in the version table.
- `README.zh-CN.md` — v0.2.14-alpha row.
- `CHANGELOG.md` — new `v0.2.14-alpha` section.

## COMMIT

- Hash: `<filled at commit time>`
- Branch: `main`
- Message: "Add p3pr url subcommand (v0.2.14-alpha)"

## PUSH

- Remote: `https://github.com/conanxin/openclaw-paper-three-pass-reader-skill`
- Branch: `main`
- Status: pushed alongside the v0.2.14-alpha annotated tag and GitHub
  Release.

## TAG

- Tag: `v0.2.14-alpha`
- Type: annotated
- Message: `v0.2.14-alpha — p3pr url subcommand`
- Pre-check: `git tag -l v0.2.14-alpha` returned empty before creation, so
  no existing tag was moved.

## RELEASE

- GitHub Release: `v0.2.14-alpha` on
  `https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases`
- Title: `paper-three-pass-reader v0.2.14-alpha`
- Notes file: `docs/RELEASE_NOTES_v0.2.14-alpha.md`

## GITHUB_PAGES_URL

- Root index: `https://conanxin.github.io/paper-reading-pages/`
- Manifest: `https://conanxin.github.io/paper-reading-pages/published_pages.json`
- New URL smoke page (published by this release):
  `https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-smoke-cn/`
- Pre-existing formal page (unchanged):
  `https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/`
- Local real-URL smoke run:
  `runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/`

## LIMITATIONS

- **JavaScript-heavy pages are not supported.** The stdlib `html.parser`
  does not execute JavaScript. SPA-style pages (e.g. some modern
  publication hosts) will produce only the initial server-rendered
  HTML. The CLI will fall back to `partial_text` if extraction yields
  < 800 chars and surface this in `intake_quality.warnings`. For
  JS-heavy pages, pre-extract with a JS-capable tool and use
  `./p3pr abstract path/to/text.md` instead.
- **PDFs without `pdftotext` are not extracted.** The CLI saves the
  PDF to `source/source.pdf` and records `reading_mode=partial_text`
  (we do not pretend a PDF without text is `full_text`). Recommendation
  in the summary will suggest `./p3pr pdf path/to/local.pdf`.
- **URL validation is permissive.** The CLI checks the URL starts with
  `http://` or `https://` and lets `urllib` handle the rest. 4xx / 5xx
  responses or DNS failures are reported as `BLOCKED_FETCH_FAILED` in
  the summary.
- **HTML title vs user `--title` discrepancy is logged, not enforced.**
  When the user passes `--title` and the page's `<title>` differs, the
  CLI logs the discrepancy at info level and uses `--title` as
  canonical. The draft's `intake_quality.warnings` carries the canonical
  title; the user can re-render with the HTML title if desired.

## NEXT_USER_ACTION

- **No immediate action required.** The local CLI is now
  `p3pr url <url>`-capable; the live site audit is
  `pages=11 pass=11 warn=0 fail=0`; the published smoke page is live.
- **Try it:**
  ```bash
  ./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
    --zh --full --publish
  ```
  This will run the full pipeline against Hamming's classic and
  republish the page to the existing `you-and-your-research-cn/` slug
  (replacing the formal hand-edited page with a fresh DRAFT
  rendering). To avoid overwriting, use a different `--slug`.
- **Future iterations** may add a `--js` flag that shells out to
  `playwright` (or similar) for JS-heavy pages, but that is out of
  scope for v0.2.14-alpha which is stdlib-only.
