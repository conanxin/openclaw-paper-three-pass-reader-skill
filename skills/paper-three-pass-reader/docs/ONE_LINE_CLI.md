# P3PR One-Line CLI — paper-three-pass-reader (v0.2.5-alpha)

## What it is

`p3pr` is a thin shell shim at the repo root that exec's a Python CLI wrapper
(`skills/paper-three-pass-reader/scripts/p3pr.py`). It orchestrates the existing
runner / fill-pack / audit / zh-CN quality gate / renderer / publisher into a
single command, so you do not have to remember the long argv.

It does **not** do any deep reading. It does **not** call external LLM APIs. It
chains existing scripts.

## The 6 subcommands

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
```

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
