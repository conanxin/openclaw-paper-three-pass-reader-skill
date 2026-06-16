# PUBLISHED_PAGES_AUDIT — paper-three-pass-reader (v0.2.12-alpha)

`audit_published_pages.py` is the published-pages regression audit for `paper-three-pass-reader`. It reads `published_pages.json` (live URL or local file), fetches every page, and produces a structured regression report.

This document is the canonical reference for the audit tool: what it checks, how to run it, how to read the output, and what the three overall statuses (PASS / WARN / FAIL) mean.

v0.2.12-alpha adds **page-type classification** (`site_index` / `paper_page` / `manifest` / `unknown`) so the root index / manifest is no longer falsely flagged with `missing_resolver_trail` / `missing_claims_section` / `missing_glossary`. See [Page-type classification (v0.2.12-alpha)](#page-type-classification-v0212-alpha).

## Why this tool exists

By v0.2.9 we had already published nine pages to `conanxin/paper-reading-pages`. The first eight were rendered by older versions of the renderer (v0.2.5–v0.2.7) and still carry legacy-render artefacts:

- `{% else %}` / `{{ … }}` template-tag leaks.
- Raw Python dict repr (`{'label': …}`) in the Five Cs cards.
- Stale `v0.1.0-alpha` in the page footer.
- Missing Resolver Trail / 解析状态 block (only added in v0.2.8).
- Missing glossary definitions (added in v0.2.9).
- Missing essay-mode markers (added in v0.2.9).

We don't want to silently rewrite the live site every time the renderer improves — old pages should stay immutable, and the next re-render should be a deliberate decision. This tool gives us a single command that produces an evidence-based inventory of which live pages have which regressions, and a recommendation list for what to republish in the next cycle.

It also doubles as a self-test for the renderer itself: every new renderer release should keep the audit result of its own canonical sample at PASS.

## What it checks

| Group | Code | Severity | What it means |
|---|---|---|---|
| A | `http_error` | error | Page returned non-200. |
| A | `empty_body` | error | Page returned 200 but the body is empty or <200 bytes. |
| B | `template_leak` | error | Body contains `{% %}` / `{{ }}` / `{# #}` / `{% else %}` / `No key references recorded`. |
| C | `old_footer` | error | Body still shows `v0.1.0-alpha` (any variant). |
| C | `raw_dict` | error | Body contains `{'label': …` raw Python dict repr. |
| D | `zh_cn_markers_weak` | warning | zh-CN page (slug has `-cn` or title has CJK) has fewer than 5 of the 6 zh-CN UI markers. |
| E | `missing_resolver_trail` | warning | Body has neither English Resolver Trail nor zh-CN 解析状态 / 置信度. |
| F | `missing_claims_section` | warning | Body has no Claims / Evidence / 主张 / 证据. |
| F | `empty_claim_id` | warning | Body contains `<code></code>` empty cells. |
| F | `no_visible_claim_id` | info | Body has no `>C\d{2,}<` claim ID. |
| F | `no_evidence_label` | info | Body has none of the 6 evidence labels. |
| G | `missing_glossary` | warning | Body has no Glossary / 关键术语. |
| G | `glossary_no_explicit_definition` | info | Glossary chips have no `chip-body` definition block. |
| H | `essay_missing_markers` | warning | Essay/talk page (slug or title matches `you-and-your-research / essay / talk / lecture / keynote`) is missing 实践计划 / 结构说明 / 相关脉络. |
| I | `audit_crashed` | error | Audit script itself crashed on this page. |

## Overall status

| Status | Condition |
|---|---|
| `PASS` | Manifest is readable. Every page returns 200. No `error`-level issues. |
| `WARN` | Every page returns 200. No `error`-level issues. At least one page has `warning` or `info` issues. |
| `FAIL` | Manifest not parseable, or at least one page returned non-200 / has `template_leak` / `raw_dict` / `old_footer` / `audit_crashed`. |

Pass `--strict` to promote WARN to FAIL (useful for CI gates).

## Usage

### Live audit (the canonical mode)

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --json-output runs/published-pages-audit-20260615/audit.json \
  --markdown-output runs/published-pages-audit-20260615/audit.md \
  --include-root \
  --warn-only
```

- `--include-root` also audits the site root `index.html` (in addition to the per-page manifests).
- `--warn-only` makes the exit code 0 even if the audit returns WARN/FAIL — useful when you only want the report.
- `--timeout 20` is the default HTTP timeout per page.
- `--max-pages N` caps how many manifest entries to audit (handy for quick smoke tests).
- `--manifest-file <path>` lets you audit a local manifest instead of the live URL.

### Selftest (used by `scripts/validate.sh` step 17)

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --selftest-dir /tmp/p3pr-selftest \
  --json-output /tmp/selftest-audit.json \
  --markdown-output /tmp/selftest-audit.md
```

The selftest mode runs six synthetic pages through the same checks and asserts that:

- A page with `{% else %}` + `No key references recorded` → `template_leak` is detected.
- A page with `{'label': …}` → `raw_dict` is detected.
- A page with `v0.1.0-alpha` in the footer → `old_footer` is detected.
- A page whose slug is `fake-essay` and which lacks `实践计划 / 结构说明 / 相关脉络` → `essay_missing_markers` is detected.
- A page whose title contains CJK and which lacks 5+ zh-CN UI markers → `zh_cn_markers_weak` is detected.
- A page with all required sections and a `v0.2.9-alpha` footer → `PASS`.

The selftest does not require network access.

## Output format

### JSON

```json
{
  "schema_version": "0.1.0",
  "generated_at": "2026-06-15T…Z",
  "status": "PASS|WARN|FAIL",
  "site_root": "…",
  "manifest_url": "…",
  "manifest_ok": true,
  "pages_total": 9,
  "pages_checked": 9,
  "pages_pass": 1,
  "pages_warn": 1,
  "pages_fail": 7,
  "issues_by_severity": {"error": 14, "warning": 11, "info": 6},
  "pages": [
    {
      "url": "…",
      "slug": "you-and-your-research-cn",
      "title": "…",
      "http_status": 200,
      "fetched_bytes": 37717,
      "issues": [
        {"severity": "warning", "code": "…", "message": "…", "recommendation": "…"}
      ],
      "status": "PASS|WARN|FAIL"
    }
  ],
  "recommendations": ["…"]
}
```

### Markdown

The Markdown report contains:

- A header with overall status, counts, and issue totals.
- A `## Summary` block (PASS / WARN / FAIL semantics).
- A `## Pages` table (one row per page with status, HTTP code, title, and issue codes).
- A `## Detailed issues` section (one `###` block per page that has any issues).
- A `## Recommendations` block (sorted, deduplicated, derived from the issue codes).

## Reading the result

A typical first run produces something like:

| Page | Status | Why |
|---|---|---|
| `you-and-your-research-cn` | PASS | Re-rendered in v0.2.9. |
| `second-me-human-inspired-memory-cn` | FAIL | Rendered in v0.2.7; still has `template_leak` + `old_footer`. |
| `attention-is-all-you-need` | FAIL | Rendered in v0.2.5; has `template_leak` + `old_footer` + `missing_resolver_trail`. |
| 5 more English-language pages | FAIL | Same pattern. |

That output maps directly to the `recommendations` block: a v0.2.11 cycle should re-render and republish the 8 failing pages with the v0.2.9+ renderer.

## When to run

| Trigger | Reason |
|---|---|
| Before any new release | Make sure the previous release's "PASS page" is still passing after the renderer template was edited. |
| After bumping the renderer version | Catch any new regressions introduced by the template edit. |
| Monthly | Spot-check the live site is still healthy. |
| Before deciding to republish a batch of pages | Confirm which pages actually need republishing. |

The audit is a **read-only** tool. It never writes back to the manifest, never touches `gh-pages`, and never triggers re-renders. The decision to republish is a separate step that uses the audit's recommendations.

## Compatibility

- `audit_published_pages.py` is stdlib-only. No `requests`, no `beautifulsoup4`, no `playwright`. Just `urllib`, `json`, `re`, `argparse`.
- Works against any host that serves `published_pages.json` + per-page `index.html`. Tested against GitHub Pages.
- Backwards compatible with the v0.1 manifest schema (`schema_version: "0.1"`).

## Page-type classification (v0.2.12-alpha)

v0.2.10/v0.2.11 audits ran every page in the manifest through the same paper-level
check set. This was correct for paper pages, but it produced three false-positive
warnings on the **root index**:

- `missing_resolver_trail` — the root index never had a Resolver Trail block, by
  design. It's a manifest, not a paper page.
- `missing_claims_section` — same.
- `missing_glossary` — same.

The root index legitimately has none of those sections: it lists links to paper
pages. Flagging it for "missing Claims / Glossary / Resolver Trail" is a
**misclassification**, not a regression.

Starting with v0.2.12-alpha, every audited page is classified into one of four
`page_type` values, and check selection is driven by that classification.

| `page_type` | Meaning | Paper-level checks (Claims / Glossary / Resolver / Essay / zh-CN) | Severe checks (template_leak / raw_dict / old_footer) | Index / manifest checks |
|---|---|---|---|---|
| `site_index` | The site root (`<site_root>/`). A manifest of all published pages. | **Skipped by design** | **Run** (template leak / old footer / raw dict on the index are still real regressions) | **Run** — title present, ≥1 published-page link, link count roughly matches manifest, manifest reference present |
| `paper_page` | A normal paper reading page produced by `render_page.py`. | **Run** (full paper-level check set) | **Run** | n/a |
| `manifest` | The `published_pages.json` JSON itself (when `--include-manifest` is set). | **Skipped** | **Skipped** | **Run** — JSON valid, `pages` list present, every entry has `slug` + `title` + `path`, no duplicate slugs / paths |
| `unknown` | Fallback for unclassified URLs. | Treated as `paper_page` (safe default) | Run | n/a |

### Where classification happens

`_classify_page_type()` in `audit_published_pages.py` uses these rules:

1. If the body parses as JSON containing `pages: [...]` and at least one
   `slug`, the page is `manifest`.
2. If the URL is the requested site root (`--include-root` flag or URL matches
   `<site_root>` with empty path), the page is `site_index`.
3. If the URL has an empty path and the body contains manifest signals
   (`published_pages.json`, `Paper Reading Pages`, `Published pages`, or links
   to `/<slug>/` paths), the page is `site_index`.
4. Otherwise the page is `paper_page`.

### Audit JSON schema additions (v0.2.12-alpha)

Top-level:

- `schema_version`: bumped from `0.1.0` to `0.2.0`.
- `page_type_counts`: object with counts per `page_type` (`site_index`,
  `paper_page`, `manifest`, `unknown`).

Per-page:

- `page_type`: one of `site_index` / `paper_page` / `manifest` / `unknown`.

The Markdown report gains a `## Page Type Summary` table and a per-page
`Page type:` line in the Detailed Issues section. For `site_index` pages, the
section also notes `Paper-level checks: skipped by design` and
`Index checks: ran`.

### Live audit example

```bash
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
  --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
  --site-root https://conanxin.github.io/paper-reading-pages \
  --include-root --warn-only
```

Before v0.2.12-alpha: `[audit] overall=WARN pages=10 pass=9 warn=1 fail=0`
(root index has 3 paper-level warnings).

After v0.2.12-alpha: `[audit] overall=PASS pages=10 pass=10 warn=0 fail=0`
with `page_type_counts: {site_index: 1, paper_page: 9, manifest: 0, unknown: 0}`.

The recommendations block in the JSON report surfaces the rule with
`Root index is treated as site_index and exempted from paper-page checks (...)`.

### Selftest additions

`audit_published_pages.py --selftest-dir <dir>` runs eight synthetic pages:

- `fake-essay`, `fake-zhcn`, `fake-pass`, `fake-template-leak`, `fake-raw-dict`,
  `fake-old-footer` (the original six).
- `fake-site-index` — a clean root index; expected codes: `[ ]`. Must be
  classified as `site_index` and must NOT trigger `missing_resolver_trail`,
  `missing_claims_section`, or `missing_glossary`.
- `fake-site-index-leak` — a root index that contains `{% else %}` in the body.
  Expected codes: `[template_leak]`. Must be classified as `site_index` and
  must FAIL on the severe check.

`scripts/validate.sh` step 18 verifies both new fixtures plus the live audit
shape end-to-end.

## v0.2.13-alpha: manifest link detection

v0.2.12-alpha left a single info-level finding on the root index:
`index_no_manifest_link` ("site_index 页面未引用 published_pages.json").
v0.2.13-alpha addresses this by:

1. **Publisher emits the manifest link in two forms**:
   - `<head>` carries `<link rel="alternate" type="application/json"
     href="published_pages.json" title="Published pages manifest" />`
     (machine-readable manifest discovery).
   - The About section carries a visible `<a href="published_pages.json">`
     link with English + Chinese labels
     ("Machine-readable manifest: ... · 页面清单 JSON").
2. **`_check_site_index()` accepts both forms.** The new check looks for a
   visible `<a href="published_pages.json">` link OR a
   `<link rel="alternate" type="application/json" href="published_pages.json">`
   tag. Either form is enough to suppress `index_no_manifest_link`.
3. **The audit no longer emits `index_no_manifest_link`** on root indexes
   generated by the current publisher. A root index without any manifest
   link (older or hand-written) will still emit the finding at info level,
   so the check is not silently disabled.

The user-visible effect is that the root index now explicitly points
visitors at the JSON manifest, and the published-pages audit's last
advisory info finding is gone for live sites.

`scripts/validate.sh` step 19 verifies end-to-end:
- The publisher-generated index contains `published_pages.json`.
- The generated index has the manifest link in either form.
- A fake `site_index` fixture with the manifest link does not trigger
  `index_no_manifest_link`.
- A new `fake-site-index-no-manifest` fixture still triggers it (info-level).
- The audit JSON classifies `site_index` AND has no paper-level warnings
  on the root.
- The live site audit's root index no longer triggers
  `index_no_manifest_link`.

Validation is now **242/0 PASS** (was 236/0 PASS at v0.2.12-alpha).
