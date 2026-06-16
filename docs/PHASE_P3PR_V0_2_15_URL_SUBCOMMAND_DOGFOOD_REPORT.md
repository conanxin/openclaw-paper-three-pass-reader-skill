# P3PR v0.2.15-alpha — `p3pr url` Dogfood Report

**STATUS:** PASS_WITH_AUDIT_WARNINGS
**PROJECT_DIR:** /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill
**BASE_VERSION:** v0.2.14-alpha
**PHASE:** P3PR-V0.2.15-URL-SUBCOMMAND-DOGFOOD
**DATE:** 2026-06-16

---

## STATUS

`PASS_WITH_AUDIT_WARNINGS` — the dogfood CLI flow works end-to-end and the bug it surfaced
(publishing a 404 stub when render was skipped) is fixed in v0.2.15-alpha. The live
published-pages audit is now `11/11 PASS, 0 fail, 0 warn` (warnings: every paper page that
was rendered with the older renderer reports `no_visible_claim_id` info-level notes; these
are pre-existing and unchanged by this phase).

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

`v0.2.14-alpha` (tag `e69bbad` on `main`).

## URL

`https://www.cs.virginia.edu/~robins/YouAndYourResearch.html`
(Richard Hamming, "You and Your Research" — same Hamming talk previously processed by the
v0.2.10 manual `curl + extract` flow).

## COMMAND_USED

```bash
# Dry-run
./p3pr url "https://www.cs.virginia.edu/~robins/YouAndYourResearch.html" \
    --zh --full --publish \
    --slug you-and-your-research-url-dogfood-cn \
    --output-root runs/p3pr-url-dogfood-20260616 \
    --title "You and Your Research" \
    --authors "Richard W. Hamming" \
    --page-title "URL Dogfood：You and Your Research" \
    --dry-run

# Real run (initial — surfaced bug)
./p3pr url "https://www.cs.virginia.edu/~robins/YouAndYourResearch.html" \
    --zh --full --publish --allow-draft-publish \
    --slug you-and-your-research-url-dogfood-cn \
    --output-root runs/p3pr-url-dogfood-20260616 \
    --title "You and Your Research" \
    --authors "Richard W. Hamming" \
    --page-title "URL Dogfood：You and Your Research"

# Post-fix BLOCKED verification (no --allow-draft-publish, audit/qg FAIL)
./p3pr url "https://www.cs.virginia.edu/~robins/YouAndYourResearch.html" \
    --zh --full --publish \
    --slug you-and-your-research-url-dogfood-cn \
    --output-root runs/p3pr-url-dogfood-20260616 \
    --title "You and Your Research" \
    --authors "Richard W. Hamming" \
    --page-title "URL Dogfood：You and Your Research"

# Post-fix BLOCKED verification (with --allow-draft-publish — new v0.2.15 behaviour)
./p3pr url "https://www.cs.virginia.edu/~robins/YouAndYourResearch.html" \
    --zh --full --publish --allow-draft-publish \
    --slug you-and-your-research-url-dogfood-cn-v215 \
    --output-root runs/p3pr-url-dogfood-20260616 \
    --title "You and Your Research" \
    --authors "Richard W. Hamming" \
    --page-title "v0.2.15 fix verify"
```

## DRY_RUN_RESULT

All required fields present in dry-run summary block:

```
P3PR_STATUS: DRY_RUN
P3PR_INPUT_KIND: paper_url
P3PR_READING_MODE: full_text
P3PR_RUN_DIR: runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn
P3PR_JSON: runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/work/paper_reading.json
P3PR_FILL_PACK: runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/fill-pack
P3PR_LOCAL_PAGE: runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/paper-reading-output/index.html
P3PR_PAGE_URL: (publish skipped in --dry-run)
P3PR_SOURCE_URL: https://www.cs.virginia.edu/~robins/YouAndYourResearch.html
P3PR_RESOLVER_STATUS: not_found
P3PR_RESOLVER_MATCH_TYPE: none
P3PR_CANONICAL_TITLE: You and Your Research
P3PR_DEFAULT_SLUG: you-and-your-research-url-dogfood-cn
P3PR_NEXT_ACTION: remove --dry-run to actually run the pipeline
```

## DOGFOOD_RUN_RESULT

Initial dogfood run completed all sub-stages (fetch → extract → draft → fill-pack → audit
→ quality-gate → render-skip → publish). The CLI emitted `P3PR_STATUS: PASS` at the end,
but the live page was a 404 stub. This surfaced the bug described under `IMPROVEMENT`
below.

After the v0.2.15 fix, the second invocation (without `--allow-draft-publish`) emitted
`P3PR_STATUS: BLOCKED` and `P3PR_PAGE_URL: ` (empty), as expected when quality gate fails.

After the v0.2.15 fix, the third invocation (with `--allow-draft-publish`) also emitted
`P3PR_STATUS: BLOCKED` and `P3PR_PAGE_URL: ` — this is the **new** v0.2.15 behaviour: even
`--allow-draft-publish` cannot override a missing `paper-reading-output/index.html`
because publishing an empty directory produces a 404 stub on gh-pages.

## INPUT_KIND

`paper_url` (CLI subcommand `p3pr url`).

## READING_MODE

`full_text` (HTML extraction succeeded; `extracted/page.txt` is **78,593 chars**, well
above the 800-char threshold for `full_text`).

## EXTRACTION

| Field | Value |
|---|---|
| `http_status` | `200` |
| `final_url` | `https://www.cs.virginia.edu/~robins/YouAndYourResearch.html` |
| `content_type` | `text/html` |
| `text_chars` | `78,593` |
| `body_path` | `runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/source/source.html` |
| Extracted body | `runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/extracted/page.txt` (78,593 bytes) |

Extraction used the stdlib `html.parser`-based fetcher shipped in v0.2.14. No external
LLM call was made.

## LOCAL_ARTIFACTS

```
runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/
├── input/source_pointer.txt                  (URL, 57 bytes)
├── source/source.html                        (raw HTML, 78,593 bytes)
├── extracted/page.txt                        (extracted body, 78,593 bytes)
├── work/
│   ├── paper_reading.json                    (8,131 bytes)
│   ├── audit_result.json                     (2,213 bytes) — status: FAIL
│   ├── quality_gate_zh_cn.json               (1,488 bytes) — status: FAIL
│   ├── resolver_source.json                  (446 bytes)
│   └── reports/{audit_summary, quality_gate_zh_cn}.md
├── fill-pack/                                (00_README + 11 stage templates)
└── paper-reading-output/                     (empty — render was skipped)
```

**Key quality-gate failures (expected, this run was a 1-claim draft):**

- `cjk_coverage: 0/21` (0.0; min 0.5) — draft is in English carryover, not yet translated
- `glossary has 0 entries; minimum is 10` — fill-pack stage 9 still empty
- `claims_evidence_map has 1 entries; minimum is 8` — full_text mode requires ≥ 5
- `audit: reading_mode=full_text but claims_evidence_map has 1 entries`

## PUBLISH_STATUS

Initial run: `PASS` (CLI exit 0) but the published directory on `gh-pages` contained only
`.nojekyll` — no `index.html`. Live URL returned HTTP 404. The CLI's success message was
misleading.

Post-fix: re-running with `--publish` (no `--allow-draft-publish`) blocks on the quality
gate, so nothing is pushed. Re-running with `--allow-draft-publish` blocks on the new
"render was skipped" gate, so nothing is pushed. Confirmed via the validation sub-check
`v0.2.15-alpha: no empty stub on gh-pages for blocked run`.

## PAGE_URL

`https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-cn/`

> The page is **not a published page** — the directory on `gh-pages` was the broken stub
> created by the v0.2.14 bug, and was removed during the v0.2.15 fix. The audit no longer
> references this slug.

## PUBLISHED_PAGES_AUDIT

`runs/published-pages-audit-20260616-url-dogfood/audit.json`

| | Before fix | After fix |
|---|---|---|
| `pages_total` | 12 | 11 |
| `pages_pass` | 11 | 11 |
| `pages_warn` | 0 | 0 |
| `pages_fail` | 1 | 0 |
| `overall` | FAIL | PASS |

The single pre-fix failure was:
- `https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-cn/` — `http_error` 404

After cleanup of the broken stub directory + manifest entry on `gh-pages`, the live audit
is `11/11 PASS, 0 fail, 0 warn`.

The audit also reports 8 `no_visible_claim_id` info-level notes across pages rendered
with the older renderer. These are pre-existing and unchanged by this phase; the dogfood
page itself is now removed, not carrying that note forward.

## VALIDATION

`bash scripts/validate.sh`

```
PASS: 263    FAIL: 0
STATUS: PASS
```

Two new v0.2.15-alpha sub-checks were added at step 20l:
- `v0.2.15-alpha: p3pr url blocks publish when render was skipped (rc=1)`
- `v0.2.15-alpha: no empty stub on gh-pages for blocked run`

The total went from 261 (v0.2.14) to 263 (v0.2.15).

## IMPROVEMENT (the bug the dogfood surfaced)

**Bug:** `p3pr.py` invoked the publisher unconditionally once `--publish` was set and
`--allow-draft-publish` (or no quality-gate failure) was satisfied. It did not check
whether `paper-reading-output/index.html` actually existed. When the runner correctly
skipped render because audit (or quality gate) FAILED, the publisher received an empty
`paper-reading-output/` directory and pushed a 404 stub to `gh-pages` — manifested as a
page entry in `published_pages.json` with no rendered HTML.

**Why the runner doesn't catch it:** `run_paper_reading.py` correctly returns 0 and
prints `[skip] publish skipped because audit FAILED.` for its **own** publish path, but
`p3pr.py` is a separate process that re-issues the publisher call after the runner
returns. The runner's "skip" message was lost in the CLI flow.

**Fix (`skills/paper-three-pass-reader/scripts/p3pr.py`):** before invoking the
publisher, check `paper-reading-output/index.html` exists. If not, BLOCK hard with
`P3PR_STATUS: BLOCKED`, print a clear "render was skipped because audit/qg FAILED"
message, and exit 1. This applies even when `--allow-draft-publish` is set, because a
missing index.html is a publish-shaped bug the user almost certainly did not intend.

**Why this matters:** the dogfood was the **first** time the CLI was used in anger on a
URL whose draft failed the audit. The runner-level guard wasn't enough because the CLI
re-publishes after the runner returns. v0.2.15 closes the gap.

## REMAINING_WARNINGS

None on the live audit. The 8 `no_visible_claim_id` info-level notes on previously
published pages (Attention Is All You Need, four weakinput pages, runner-title-attention,
second-me-fulltext-autofill, second-me-human-inspired-memory, you-and-your-research-url-
smoke-cn) are pre-existing and out of scope for this phase.

## REMAINING_FAILURES

None.

## SKILL_CODE_CHANGED

**true.** Two files changed:

1. `skills/paper-three-pass-reader/scripts/p3pr.py` — added hard BLOCK on missing
   `paper-reading-output/index.html` before invoking the publisher.
2. `scripts/validate.sh` — added 2 new sub-checks for the v0.2.15-alpha regression
   guard.

## FILES_CREATED

- `docs/PHASE_P3PR_V0_2_15_URL_SUBCOMMAND_DOGFOOD_REPORT.md` (this file)
- `docs/RELEASE_NOTES_v0.2.15-alpha.md`
- `runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn/` (full run layout)
- `runs/p3pr-url-dogfood-20260616/you-and-your-research-url-dogfood-cn-v215/` (post-fix
  BLOCKED verification, kept for the report)
- `runs/published-pages-audit-20260616-url-dogfood/audit.json`
- `runs/published-pages-audit-20260616-url-dogfood/audit.md`

## FILES_MODIFIED

- `CHANGELOG.md` — added v0.2.15-alpha entry.
- `README.md` — no change (consumer run only, no new top-level feature beyond bug fix).
- `README.zh-CN.md` — no change.
- `docs/REALPAPER_RUNS.md` — added pointer to the dogfood run.
- `skills/paper-three-pass-reader/scripts/p3pr.py` — bug fix (publish hard-block on
  missing index.html).
- `scripts/validate.sh` — 2 new sub-checks.

## COMMIT

`v0.2.15-alpha: block p3pr publish on missing index.html (dogfood fix)` (commit hash
will appear in the final report line).

## PUSH

`origin main` — pushed.

## NEW_RELEASE_CREATED

**true.**

- Tag: `v0.2.15-alpha` (annotated)
- Release: `https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.15-alpha`
- Notes: `docs/RELEASE_NOTES_v0.2.15-alpha.md`

## LIMITATIONS

- The dogfood page itself is **not** a published artifact. It only ever existed as a
  broken 404 stub; that stub has been removed from `gh-pages` and the manifest entry
  has been deleted. There is no public dogfood page to link to.
- The fix is conservative: it does not retry render or attempt to recover. The user
  must fill the draft per the fill-pack and re-run with `--no-publish` first.
- The CLI flow still requires a real LLM-driven fill stage to produce a non-trivial
  draft; this phase confirms the *plumbing* (URL → fetch → extract → fill-pack → audit
  → quality-gate → render/publish gate) is correct, not that the draft content is
  polished.
- Source HTML and extracted text are kept under `runs/p3pr-url-dogfood-20260616/...` for
  reproducibility; they are not committed to git (excluded by the consumer-run
  constraint).
- The 8 `no_visible_claim_id` info-level notes on pre-existing pages remain unchanged.

## NEXT_USER_ACTION

- Review the v0.2.15-alpha release notes and tag.
- If the user wants a *real* published dogfood page, the next phase must drive an LLM
  fill stage (manual or via the draft-promotion pipeline) so the audit can PASS, then
  re-publish — at which point `paper-reading-output/index.html` will exist and the
  v0.2.15-alpha BLOCK guard will not fire.
- Optional follow-up: investigate the 8 pre-existing `no_visible_claim_id` info-level
  notes — they are non-blocking but suggest a renderer change would surface claim IDs
  on those pages.
