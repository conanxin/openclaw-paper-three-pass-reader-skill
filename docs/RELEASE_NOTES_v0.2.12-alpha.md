# paper-three-pass-reader v0.2.12-alpha

## Summary

This release fixes the published-pages audit false positives on the root index
page. Pre-v0.2.12-alpha audits ran every page in the manifest through the same
paper-level check set, which produced three false-positive warnings on the root
index (`missing_resolver_trail`, `missing_claims_section`, `missing_glossary`)
because the root index is a manifest of all published pages, not a paper
reading page itself. v0.2.12-alpha introduces page-type classification so the
audit selects the right check set per page.

The live site audit (10 pages on `conanxin.github.io/paper-reading-pages`) now
reports `overall=PASS, pages=10 pass=10 warn=0 fail=0` (was
`WARN, 9 PASS / 1 WARN / 0 FAIL`).

## Included

- **Page type classification**: every audited page is classified as one of
  `site_index` / `paper_page` / `manifest` / `unknown`.
- **Root-index audit exemption**: pages classified as `site_index` skip the
  paper-level check set (`missing_resolver_trail`, `missing_claims_section`,
  `missing_glossary`, `no_visible_claim_id`, `no_evidence_label`,
  `glossary_no_explicit_definition`, `essay_missing_markers`,
  `zh_cn_markers_weak`, `empty_claim_id`).
- **Severe checks retained on root index**: `template_leak`, `raw_dict`, and
  `old_footer` still fire on the root index — those would still be real
  regressions if they appeared.
- **Index-specific checks**: title present, ≥1 published-page link, manifest
  reference, link-vs-manifest delta within tolerance.
- **Manifest-specific checks**: JSON valid, `pages` list present, every entry
  has `slug` + `title` + `path`, no duplicate slugs / paths. Always emitted;
  with `--include-manifest` the manifest JSON itself is fetched and audited.
- **`--include-manifest` CLI flag**: opt-in audit of the `published_pages.json`
  JSON itself.
- **`page_type` field on every page entry** + **`page_type_counts` top-level
  object** in the audit JSON.
- **`## Page Type Summary` section** in the Markdown audit report.
- **`scripts/validate.sh` step 18**: 11 new sub-checks covering the page-type
  classifier, the exemption, two new selftest fixtures (`fake-site-index` clean,
  `fake-site-index-leak` with `{% else %}`), and a live-site smoke sub-check.
  Validation is now **236/0 PASS** (was 225/0 PASS at v0.2.10).

## Compatibility

- **Existing pages remain unchanged.** No consumer pages are re-rendered by
  this release. The v0.2.11 remediation commit stays valid.
- **Existing audit output remains readable.** Downstream consumers that only
  read `pages_pass` / `pages_warn` / `pages_fail` / `issues_by_severity` /
  `pages[*].issues` continue to work. The new fields (`page_type`,
  `page_type_counts`, `schema_version=0.2.0`) are additive.
- **No old tags moved.** v0.2.10-alpha and earlier tags are immutable and stay
  at their original commits.
- **No published pages deleted or rewritten.**

## Files touched (this release)

| File | Purpose |
|---|---|
| `skills/paper-three-pass-reader/scripts/audit_published_pages.py` | Page-type classifier + site-index exemption + manifest checks + new output fields. |
| `scripts/validate.sh` | Step 18 with 11 sub-checks + 2 new selftest fixtures. |
| `skills/paper-three-pass-reader/docs/PUBLISHED_PAGES_AUDIT.md` | New "Page-type classification (v0.2.12-alpha)" section. |
| `skills/paper-three-pass-reader/docs/USAGE.md` | New "v0.2.12-alpha: page-type classification + root-index exemption" section. |
| `README.md`, `README.zh-CN.md` | New v0.2.12-alpha row in the version table. |
| `CHANGELOG.md` | New `v0.2.12-alpha` section. |
| `docs/RELEASE_NOTES_v0.2.12-alpha.md` | This file. |
| `docs/PHASE_P3PR_V0_2_12_ROOT_INDEX_AUDIT_EXEMPTION_REPORT.md` | Final phase report. |
| `runs/published-pages-audit-20260615-root-index-exemption/` | Live audit JSON + Markdown output (after-fix). |

## Upgrade notes

- Anyone running `audit_published_pages.py` against the live site: the WARN
  signal on the root index is now correctly suppressed. Any new WARN / FAIL
  after upgrading should come from a real regression on a paper page, the root
  index template / footer, or the manifest shape itself.
- Anyone parsing the audit JSON: check `schema_version`; consumers that
  hard-code `0.1.0` should be tolerant to `0.2.0` (new fields are additive).

## Rollback

v0.2.12-alpha only adds classifier logic + new fields; reverting to v0.2.10
restores the old audit behaviour. The live consumer pages are not touched.
