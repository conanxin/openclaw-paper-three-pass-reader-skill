# PUBLISHED_PAGES_AUDIT — paper-three-pass-reader (v0.2.10)

`audit_published_pages.py` is the published-pages regression audit for `paper-three-pass-reader`. It reads `published_pages.json` (live URL or local file), fetches every page, and produces a structured regression report.

This document is the canonical reference for the audit tool: what it checks, how to run it, how to read the output, and what the three overall statuses (PASS / WARN / FAIL) mean.

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
