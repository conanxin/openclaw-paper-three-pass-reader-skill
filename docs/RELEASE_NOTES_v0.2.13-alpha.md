# paper-three-pass-reader v0.2.13-alpha

## Summary

This release adds a manifest link to the generated root index for
`paper-reading-pages`. Users see the manifest link directly on the index
page, and tools can discover `published_pages.json` via the standard
`<link rel="alternate" type="application/json">` convention. The
published-pages audit's last remaining info-level finding on the root
index (`index_no_manifest_link`) is now gone for any site that runs
through the current publisher.

## Included

- **Root index links to `published_pages.json`** in two forms:
  - `<head><link rel="alternate" type="application/json" href="published_pages.json" title="Published pages manifest" /></head>`
    (machine-readable manifest discovery)
  - A visible `<a href="published_pages.json">` link in the About section
    with English + Chinese labels
    ("Machine-readable manifest: ... · 页面清单 JSON")
- **Audit recognizes the manifest link.** `_check_site_index()` in
  `audit_published_pages.py` accepts either form. A root index emitted by
  the current publisher no longer triggers `index_no_manifest_link`.
- **Validation covers manifest-linked root index pages.**
  `scripts/validate.sh` step 19 verifies the publisher output, the
  audit's recognition, and the live site's behaviour end-to-end.
- **One new selftest fixture** (`fake-site-index-no-manifest`): a root
  index with no link to `published_pages.json`, must still trigger
  `index_no_manifest_link` at info level.

## Compatibility

- **Existing paper pages remain readable.** The only consumer page
  republished by this release is `you-and-your-research-cn`, used as
  the trigger to refresh the root index.
- **`published_pages.json` schema is unchanged.** Existing tooling that
  reads the manifest continues to work.
- **No old tags moved.** v0.2.10-alpha and v0.2.12-alpha stay at their
  original commits.

## Files touched (this release)

| File | Purpose |
|---|---|
| `skills/paper-three-pass-reader/scripts/publish_output_to_github.sh` | Root index generator now emits the manifest link in two forms on every publish. |
| `skills/paper-three-pass-reader/scripts/audit_published_pages.py` | `_check_site_index()` now accepts the `<link rel="alternate">` form. New selftest fixture. |
| `scripts/validate.sh` | Step 19 (6 sub-checks) + new selftest fixture + updated fake-site-index fixture. |
| `skills/paper-three-pass-reader/docs/PUBLISHED_PAGES_AUDIT.md` | New "v0.2.13-alpha: manifest link detection" section. |
| `skills/paper-three-pass-reader/docs/USAGE.md` | New "v0.2.13-alpha: root index links to the manifest" section. |
| `README.md`, `README.zh-CN.md` | New v0.2.13-alpha row in the version table. |
| `CHANGELOG.md` | New `v0.2.13-alpha` section. |
| `docs/RELEASE_NOTES_v0.2.13-alpha.md` | This file. |
| `docs/PHASE_P3PR_V0_2_13_ROOT_INDEX_MANIFEST_LINK_REPORT.md` | Final phase report. |
| `runs/published-pages-audit-20260615-root-index-manifest-link/` | Live audit JSON + Markdown output (after-fix). |

## Upgrade notes

- The publisher's manifest-link emission is unconditional — running
  `publish_output_to_github.sh --site-path ... --page-title ...`
  regenerates the root index with the manifest link in both forms.
- The audit's `index_no_manifest_link` finding is now suppressed on
  indexes that have the manifest link. Old audit output (before
  republishing) still contains the finding; re-run the audit after
  upgrading to see it cleared.
- This is an index-only improvement. Paper pages are untouched (except
  for the `you-and-your-research-cn` page used to refresh the index).

## Rollback

v0.2.13-alpha only touches the publisher's index template and the
audit's `index_no_manifest_link` check; reverting to v0.2.12-alpha
restores the old behaviour. Consumer pages are not affected.
