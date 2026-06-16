# P3PR One-Line CLI — paper-three-pass-reader (v0.2.14-alpha)

## What it is

`p3pr` is a thin shell shim at the repo root that exec's a Python CLI wrapper
(`skills/paper-three-pass-reader/scripts/p3pr.py`). It orchestrates the existing
runner / fill-pack / audit / zh-CN quality gate / renderer / publisher into a
single command, so you do not have to remember the long argv.

It does **not** do any deep reading. It does **not** call external LLM APIs. It
chains existing scripts.

## The 7 subcommands

```bash
# arXiv ID
./p3pr arxiv 2503.08102 --zh --full --publish

# arXiv URL
./p3pr arxiv https://arxiv.org/abs/2503.08102 --zh --full --publish

# Title (best-effort hint lookup)
./p3pr title "Attention Is All You Need" --zh --full --publish

# Abstract (path to .md / .txt)
./p3pr abstract path/to/abstract.md --zh --publish

# Screenshot / poster / page OCR transcript
./p3pr screenshot path/to/transcript.md --zh --publish

# GitHub repo
./p3pr repo https://github.com/google-research/bert --zh --full --publish

# Local PDF
./p3pr pdf path/to/paper.pdf --zh --full --publish

# HTML / PDF URL (v0.2.14)
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html --zh --full --publish
```

`p3pr url <url>` is the v0.2.14-alpha addition. It fetches the URL, runs a
stdlib-only `html.parser` text extraction (no LLM, no BeautifulSoup, no JS), and
feeds the result to the runner as `input_kind=paper_url` with `--input-file`
+ `--paper-url`. PDFs without `pdftotext` extraction stay at `partial_text`.
See [USAGE.md](USAGE.md#v0214-alpha-p3pr-url-subcommand) for full details.

## All flags

| Flag | Effect |
| --- | --- |
| `--zh` / `--en` | Output language (default `--zh` / `zh-CN`) |
| `--language {zh-CN,en}` | Same as above, but spelled out |
| `--full` | Force `reading_mode = full_text` (downloads PDF if arxiv) |
| `--partial` | Force `reading_mode = partial_text` |
| `--abstract-only` | Force `reading_mode = abstract_only` |
| `--screenshot-only` | Force `reading_mode = screenshot_only` |
| `--slug <slug>` | Override auto-generated slug |
| `--output-root <dir>` | Override output root (default `runs/p3pr-cli-YYYYMMDD`) |
| `--title "<text>"` | Override paper title |
| `--publish` / `--no-publish` | Default `--no-publish` |
| `--repo <owner/repo>` | Default `conanxin/paper-reading-pages` |
| `--branch <name>` | Default `gh-pages` |
| `--page-title "<text>"` | Override the title in the published page |
| `--fill-pack` / `--no-fill-pack` | Default `--fill-pack` |
| `--audit` / `--no-audit` | Default `--audit` |
| `--quality-gate` / `--no-quality-gate` | Default `--quality-gate` (only effective for `--zh`) |
| `--render` / `--no-render` | Default `--render` |
| `--audit-warn-only` | Treat audit WARN as PASS (allow render/publish) |
| `--allow-draft-publish` | Allow publishing even when quality gate FAILS |
| `--dry-run` | Print the plan; do nothing else |

## How it interacts with the existing pipeline

```
argv   →  parse (p3pr.py)
         ↓
       build runner argv
         ↓
       run_paper_reading.py → writes run layout + draft JSON
                                 ↓
                               (audit) audit_paper_reading.py
                                 ↓
                               (quality gate) quality_gate_zh_cn.py
                                 ↓
                               (render) render_page.py
                                 ↓
                               (publish) publish_output_to_github.sh
         ↓
       fixed-format summary:
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

The CLI never modifies the existing scripts. It only orchestrates them.

## Boundaries

- The CLI does NOT call any external LLM API.
- The CLI does NOT pretend an abstract-only / screenshot-only draft is full_text.
- If you ask for `--full` on a screenshot / abstract input, the CLI downgrades
  to the appropriate weak mode (because there is no full body to ground
  Pass 2/3 on).
- For arxiv / pdf inputs, `--full` does download the PDF and run pdftotext.
  If extraction fails, the CLI downgrades to `partial_text` and prints the
  reason.
- For weak-mode drafts (screenshot / abstract), `--publish` is BLOCKED by
  default because the quality gate cannot pass without filling the draft.
  Pass `--allow-draft-publish` to publish anyway.

## The `--publish` vs `--allow-draft-publish` difference

| State | `--publish` | `--allow-draft-publish` |
| --- | --- | --- |
| Quality gate PASS, full reading | publishes | publishes |
| Quality gate WARN, weak reading | publishes with WARN note | publishes |
| Quality gate FAIL, weak reading | BLOCKED | publishes anyway (as draft) |
| Quality gate FAIL, full reading | BLOCKED | publishes anyway (likely broken) |

Use `--allow-draft-publish` only when you understand that the published page
is the unfilled draft. The CLI will print a clear `P3PR_STATUS: WARN` summary
in that case.

## From draft to full reading

If the CLI returns `P3PR_STATUS: WARN` or `BLOCKED`, the next step is to
fill the draft, not to re-run the CLI blindly:

```bash
# 1. Inspect the run
cd runs/p3pr-cli-20260615/<slug>
ls work/ fill-pack/

# 2. Read the fill-pack and fill work/paper_reading.json per the
#    stage instructions (00_README.md through 11_zh_cn_quality_gate.md).
#    The fill-pack is in your language (zh-CN by default).

# 3. Re-audit and re-run quality gate
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input work/paper_reading.json --quality-gate
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input work/paper_reading.json

# 4. Re-render locally
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input work/paper_reading.json \
  --output paper-reading-output

# 5. Re-publish
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --site-path <slug> \
  --page-title "<title>" \
  --message "Re-publish <slug> after fill"
```

The CLI does not currently auto-loop this; you run the steps manually. This
keeps the CLI honest about what it can and cannot do.

## Re-publish after editing

If the page is already published and you just want to update the rendered
HTML, the cleanest path is:

```bash
# Edit work/paper_reading.json
# Then:
./p3pr arxiv 2503.08102 --zh --full --publish --no-quality-gate
```

(Use `--no-quality-gate` only if the gate was already PASS in the previous
run. Otherwise the gate will re-validate.)

## Common questions

**Q: Why is the CLI not doing the actual reading?**
A: The CLI is a thin wrapper. The actual reading is the fill-pack job: an
agent or a human reads the paper body and writes the analysis into
`work/paper_reading.json`. The CLI scaffolds the run, runs the structural
audit, runs the quality gate, renders the page, and (optionally) publishes.
The reading itself is the human/agent work, not the CLI.

**Q: Can the CLI work without internet?**
A: Mostly yes. The CLI does NOT call external APIs. The only network step
is the arxiv PDF download, which only happens if you run `./p3pr arxiv ...`
without `--dry-run`. With local PDFs, repo hints, and titles in the resolver
table, you can run the CLI fully offline.

**Q: Why does the CLI default to `--zh` / `zh-CN`?**
A: The home user is Chinese-first. The whole project (renderer, audit,
quality gate, fill-pack, documentation) supports both languages, but the
default is Chinese. Pass `--en` to switch.

**Q: How do I add a new subcommand?**
A: Add a `handle_<name>(args)` function in `p3pr.py`, register it in
`build_parser()` and in the `handlers` dict in `main()`. Keep it stdlib-only
and do not call external APIs.

**Q: How do I add a new hint?**
|A: As of v0.2.6, there is **only one place** to add hints:
`skills/paper-three-pass-reader/data/resolver_hints.json`. The CLI, the
runner, the tests, and the docs all read from this single file. The runner
auto-rebuilds its `RESOLVER_HINTS` back-compat dict from the shared JSON
on import. The CLI delegates to `scripts/resolver_hints.py` and writes
its view into `work/resolver_source.json` which the runner overlays via
`--resolver-source`. See `docs/RESOLVER_HINTS.md` for the full design +
how to add new paper / repo hints.

**Q: Why does the runner write a structured `source_resolution` block?**
A: So agents can see exactly how a paper was resolved. The block records
the full trail: `steps`, `hint_input`, `resolver_source`, `resolver_helper`,
`resolver_status`, `resolver_match_type`, `confidence`, `matched_paper_id`,
`matched_canonical_title`, `matched_arxiv_id`, `matched_alias`, `matched_repo`,
`candidates`, and `source_resolution_step`. The CLI overlay
(`work/resolver_source.json`) is one of the steps. See
[`RESOLVER_HINTS.md`](RESOLVER_HINTS.md#structured-source_resolution-block-v027).

**Q: What if the resolver helper itself crashes?**
A: It does not fail the run. The runner wraps the helper call in `try/except`.
On any exception it records `resolver_status=error`, sets
`degraded=ambiguous_clue`, appends a warning to `intake_quality.warnings`,
and continues with rc=0. A broken helper is treated as `ambiguous_clue`,
not as a fatal error. This is verified by a hostile-resolver test in
`scripts/validate.sh` step 14. See
[`RESOLVER_HINTS.md`](RESOLVER_HINTS.md#resolver-degradation-behaviour-v027).

## See also

- `p3pr --help` — the full flag list.
- `./p3pr <subcommand> --help` — subcommand-specific help.
- [`RUNNER.md`](RUNNER.md) — what the underlying runner does.
- [`USAGE.md`](USAGE.md) — examples of using runner / audit / quality gate directly.
- [`ZH_CN_QUALITY_GATE.md`](ZH_CN_QUALITY_GATE.md) — what the quality gate checks.
- [`SOURCE_RESOLUTION.md`](SOURCE_RESOLUTION.md) — what the renderer, audit, fill-pack, and zh-CN quality gate actually read from the structured top-level `source_resolution` block.

---

## v0.2.10-alpha: published-pages regression audit

`p3pr` does not auto-audit the live site. To get a structured report of which published pages still carry legacy-render artefacts, run `audit_published_pages.py` directly:

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --json-output runs/published-pages-audit-20260615/audit.json \
  --markdown-output runs/published-pages-audit-20260615/audit.md \
  --include-root \
  --warn-only
```

The audit is read-only — it never writes to `gh-pages`, never republishes anything, and never modifies any local files outside the output paths you pass. See [`PUBLISHED_PAGES_AUDIT.md`](PUBLISHED_PAGES_AUDIT.md) for the full reference.

---

## v0.2.17-alpha: `p3pr finalize <run-dir>` — the second-stage CLI

`p3pr` ships with a one-line CLI for the **first** stage (draft + fill-pack from
a paper, an arXiv ID, a GitHub repo, a PDF, or a URL). v0.2.17 adds a matching
one-line CLI for the **second** stage — finalizing a run directory that already
has a filled `work/paper_reading.json`:

```bash
./p3pr finalize runs/2026-06-16/you-and-your-research --publish
```

`finalize` runs, in order:

1. **Audit** — `audit_paper_reading.py` → `work/audit_final.json`. FAIL blocks.
2. **zh-CN quality gate** (only if zh-CN) — `quality_gate_zh_cn.py` →
   `work/quality_gate_zh_cn.json`. FAIL blocks unless `--allow-draft-publish`;
   WARN is non-blocking unless `--allow-warnings` is set.
3. **Render** — `render_page.py` → `<run-dir>/paper-reading-output/`.
4. **Hard guard** — if `paper-reading-output/index.html` is missing, BLOCK
   (v0.2.15 publish-gate; this is what stops 404 stubs from being pushed).
5. **Publish** (only with `--publish`) — `publish_output_to_github.sh`.
6. **Published-pages audit** (default on after publish) —
   `audit_published_pages.py` → `work/published_pages_audit_after_finalize.json`.

A full `P3PR_FINALIZE_STATUS` summary block is printed on every exit (PASS,
WARN, or BLOCKED). For details, see [`USAGE.md`](USAGE.md) §"v0.2.17-alpha:
`p3pr finalize <run-dir>` — the second-stage CLI".

## v0.2.18-alpha: `p3pr finalize` UX polish

`finalize` now infers the gh-pages site-path and the published page title from
`paper_reading.json`. The two-stage flow gets shorter:

```bash
# Stage 1 — draft + fill-pack (no publish, no render)
./p3pr url <url> --zh --full --no-publish

# Stage 2 — site-path and page-title inferred; just run finalize --publish
./p3pr finalize <run-dir> --publish
```

### Inference precedence

- **site-path** — explicit `--site-path` → `paper_metadata.page_slug` /
  `slug` / `default_slug` → slugified `paper_metadata.title` → run-dir basename.
  CJK-only titles reach the run-dir fallback (no pypinyin dependency).
- **page-title** — explicit `--page-title` → `paper_metadata.page_title` → for
  zh-CN runs `paper_metadata.title_zh` / `title_zh_cn` → `paper_metadata.title`
  → run-dir basename. The English title is preserved (no auto-translation).

### Richer summary block

Every finalize exit now prints:

- `P3PR_READING_MODE` — `full_text` / `abstract_only` / `screenshot_only` / `partial_text`.
- `P3PR_LANGUAGE` — `target_language/ui_language`.
- `P3PR_SITE_PATH`, `P3PR_PAGE_TITLE` — the inferred (or explicit) values.
- `P3PR_AUDIT_STATUS`, `P3PR_QUALITY_GATE_STATUS` — short status codes.
- `P3PR_WARNING_COUNT`, `P3PR_WARNING_SUMMARY` — up to 3 actual warnings,
  `|`-joined, with `... (+N more)` when longer.
- `P3PR_NEXT_ACTION` — state-aware one-liner (BLOCKED audit / BLOCKED quality
  gate / WARN / PASS / not-published) telling the operator exactly what to do
  next, with the path of the work dir / file to edit.

### When to override

- `--site-path` — when the inferred slug collides with a previous page or
  doesn't slugify well (e.g. CJK-only title).
- `--page-title` — when the publisher page title needs to differ from the
  paper's own title.
- `--allow-warnings` — only for English-source papers whose long English blobs
  trip the quality-gate warning. Do not use it to silence structural errors.

All v0.2.15 / v0.2.17 publish guards are preserved (verified by validation
step 22). Validation 293/0 PASS.

## v0.2.19-alpha: `p3pr status` + `p3pr doctor` — read-only observability

The CLI now has 10 subcommands. `p3pr status` and `p3pr doctor` are the two
read-only observability subcommands; everything else either produces or
finalizes a paper reading.

### `./p3pr status`

Scans `runs/` and reads `published_pages.json`. Default scope is both. Each
run is classified as `draft` / `filled` / `audited` / `rendered` /
`rendered_with_warnings` / `published` / `blocked` / `unknown`. Cross-
references the manifest to flag `published` runs.

```bash
./p3pr status                                # both runs + site, network-allowed
./p3pr status --runs --offline               # local runs only, no HTTP
./p3pr status --site --manifest-file ./local_manifest.json
./p3pr status --runs --json-output status_runs.json
```

The fixed summary block (`P3PR_STATUS_STATUS` / `P3PR_RUNS_*` /
`P3PR_SITE_PAGES` / `P3PR_NEXT_ACTION`) is documented in
[`STATUS_AND_DOCTOR.md`](STATUS_AND_DOCTOR.md).

### `./p3pr doctor`

Runs read-only health checks on the local toolchain. Default is `--quick`
(no validation); `--full` runs `scripts/validate.sh`. `--offline` /
`--skip-network` skip HTTP probes. `--json-output` writes the full check
list as JSON.

```bash
./p3pr doctor                                # quick
./p3pr doctor --offline                      # quick, no HTTP
./p3pr doctor --full                         # runs scripts/validate.sh
./p3pr doctor --offline --json-output doctor.json
```

The 7 check groups: local env (python3, git, p3pr shim), required scripts,
required data/docs, git state, gh CLI / auth, optional validation, light
HEAD probe of the site. Dirty working tree and missing gh are WARN, never
FAIL. doctor never auto-fixes anything.

### Recommended daily checks

```bash
./p3pr status                       # where are my runs / pages
./p3pr doctor --offline             # is the toolchain healthy
./p3pr doctor --full                # pre-release, also runs validation
```

All v0.2.15 / v0.2.17 / v0.2.18 publish guards and finalize UX are unchanged.
Validation 305/0 PASS.

## v0.3.0-alpha: stable-readiness release candidate

No new subcommands or features. v0.3.0-alpha is the first stable-readiness
release candidate. The full checklist is in
[`STABLE_READINESS_CHECKLIST.md`](../../../../docs/STABLE_READINESS_CHECKLIST.md).
The phase report is in
[`PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md`](../../../../docs/PHASE_P3PR_V0_3_0_STABLE_READINESS_REPORT.md).

### Bug fix in v0.3.0-alpha

`p3pr doctor`'s per-check status is uppercase (`PASS` / `WARN` / `FAIL`)
but the summary counter dict used lowercase keys. The `if s in summary`
lookup was always failing, so `summary.pass` / `summary.warn` / `summary.fail`
were always `0`. v0.3.0-alpha lowercases the status before the lookup.
Verified by re-running `./p3pr doctor --full` on the v0.3.0-alpha state:
24 PASS / 1 WARN / 0 FAIL.

### v0.3.0-alpha readiness results

- `bash scripts/validate.sh` — 305 / 0 PASS
- `./p3pr doctor --offline` / `--quick` / `--full` — 24 PASS / 1 WARN / 0 FAIL
- live `audit_published_pages.py` — 14 / 14 PASS, 0 warn, 0 fail
- URL dry-run smoke — no side effects
- finalize dry-run smoke — no side effects

### Not yet stable

This is `v0.3.0-alpha`, not `v0.3.0` stable. See
[`STABLE_READINESS_CHECKLIST.md`](../../../../docs/STABLE_READINESS_CHECKLIST.md)
§"Not yet stable" for the criteria that should be met before the next
stable release.

### v0.3.0 stable (released)

`v0.3.0` is the first **stable** release. No new features; the delta
from `v0.3.0-alpha` is a single housekeeping commit that committed
the historical backlog and added 21 untracked run dirs to
`.gitignore`, bringing the working tree to a clean state. The final
cleanroom on the clean tree reported 305/0 validation, 25/0/0
doctor, 14/14 live audit. See
[`PHASE_P3PR_V0_3_0_CLEANROOM_HOUSEKEEPING_REPORT.md`](../../../../docs/PHASE_P3PR_V0_3_0_CLEANROOM_HOUSEKEEPING_REPORT.md)
for the full delta.
