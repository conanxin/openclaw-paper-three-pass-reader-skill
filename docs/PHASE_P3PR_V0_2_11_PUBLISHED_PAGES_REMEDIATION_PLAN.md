# P3PR v0.2.11 — Published Pages Remediation Plan

**STATUS:** PLAN_READY
**PROJECT_DIR:** /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill
**BASE_VERSION:** v0.2.10-alpha
**INPUT_AUDIT_JSON:** runs/published-pages-audit-20260615/audit.json
**INPUT_AUDIT_MD:**   runs/published-pages-audit-20260615/audit.md
**GENERATED_AT:** 2026-06-16

---

## 1. Audit summary (before)

- pages_total: 10
- pages_checked: 10
- pages_pass: 1
- pages_warn: 1
- pages_fail: 8
- issues: error=16, warning=10, info=15

## 2. Issue code classification

| Issue code            | Count (across pages) | Severity | Root cause                                | Auto-fixable? |
|-----------------------|----------------------|----------|-------------------------------------------|---------------|
| template_leak         | 8                    | error    | Old renderer (pre v0.2.9) did not handle `{% else %}` | YES (re-render) |
| old_footer            | 8                    | error    | Old renderer wrote `v0.1.0-alpha` literal  | YES (re-render) |
| missing_resolver_trail| 8                    | warning  | Old renderer pre-dates Resolver Trail block (v0.2.8) | YES (re-render) |
| missing_claims_section| 1 (index)            | warning  | Index page is a static manifest page, not a paper page | NO (out of scope, design intent) |
| missing_glossary      | 1 (index)            | warning  | Same as above                              | NO (out of scope) |
| no_visible_claim_id   | 7 (info)             | info     | Weak inputs + old renderer                 | YES (re-render fixes most; weakinput note is info) |
| glossary_no_explicit_definition | 6 (info)  | info     | Old renderer (pre v0.2.9) wrote chips only | YES (re-render) |

## 3. Pages list and remediation

| # | URL | Slug | Status | Local run | Reading mode (intake) | Action |
|---|-----|------|--------|-----------|-----------------------|--------|
| 1 | / | (index) | WARN | n/a | n/a | **No action** — index page is a manifest page; Resolver Trail / Claims / Glossary are not expected on it. Document in remaining_warnings. |
| 2 | /attention-is-all-you-need/ | attention-is-all-you-need | FAIL | runs/attention-is-all-you-need-20260615 | full_text | **Re-render + re-publish** |
| 3 | /weakinput-title-attention-is-all-you-need/ | weakinput-title-attention-is-all-you-need | FAIL | runs/weakinput-20260615/case-title-attention | full_text (paper_title) | **Re-render + re-publish** |
| 4 | /weakinput-abstract-how-to-read-a-paper/ | weakinput-abstract-how-to-read-a-paper | FAIL | runs/weakinput-20260615/case-abstract-keshav | abstract_only | **Re-render + re-publish** (keep abstract_only) |
| 5 | /weakinput-screenshot-how-to-read-a-paper/ | weakinput-screenshot-how-to-read-a-paper | FAIL | runs/weakinput-20260615/case-screenshot-keshav | screenshot_only | **Re-render + re-publish** (keep screenshot_only) |
| 6 | /weakinput-repo-bert/ | weakinput-repo-bert | FAIL | runs/weakinput-20260615/case-repo-bert | full_text (project_or_repo) | **Re-render + re-publish** |
| 7 | /runner-title-attention/ | runner-title-attention | FAIL | runs/runner-smoke-20260615/runner-title-attention | partial_text (paper_title) | **Re-render + re-publish** |
| 8 | /second-me-fulltext-autofill/ | second-me-fulltext-autofill | FAIL | runs/v022-fulltext-autofill-secondme-20260615/second-me-fulltext-autofill | full_text | **Re-render + re-publish** |
| 9 | /second-me-human-inspired-memory-cn/ | second-me-human-inspired-memory-cn | FAIL | runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn | zh-CN | **Re-render + re-publish** (keep zh-CN) |
| 10 | /you-and-your-research-cn/ | you-and-your-research-cn | PASS | runs/you-and-your-research-20260615 | zh-CN | **No action** — already passes. |

## 4. What "auto-fix" means here

- **Re-render** the local run's `paper_reading.json` with the v0.2.9 renderer (currently
  shipping in this repo, GENERATOR_VERSION = v0.2.9-alpha). This single step resolves:
  - `template_leak` (engine now recognises `{% else %}`)
  - `old_footer` (footer uses `{{ generator_version }}`)
  - `missing_resolver_trail` (template block "2b. Resolver Trail" is present)
  - `glossary_no_explicit_definition` (info) (glossary chip-body block)
- **Do not** modify `paper_reading.json` content (no claim fabrication, no glossary
  fabrication). The fix is purely a re-render of the existing fill-pack.

## 5. What is **not** auto-fixed

- Index page (`/`) WARN — by design, the index lists pages, not paper content.
  Document in the report as "remaining warning — design intent, not a bug."
- Weakinput info-level `no_visible_claim_id` — kept as info, not a regression. Some
  weak input pages legitimately do not produce claim IDs.

## 6. Steps

1. Re-render each of the 8 failing pages into a fresh `paper-reading-output/`.
2. Re-publish each to its existing slug via `publish_output_to_github.sh --site-path`.
3. Re-run `audit_published_pages.py` against the live site.
4. Compare before/after and write the report.
5. Commit remediation plan, remediation report, before/after audit outputs,
   modified run artifacts. **Do not** create a new release tag.

## 7. Out of scope

- Skill code changes (none required; renderer is already v0.2.9+).
- Tag / release v0.2.11-alpha (only if we change skill code, which we are not).
- Any page outside this list of 8.
- Modifying the published-pages index/manifest beyond what `publish_output_to_github.sh`
  does automatically when invoked with `--site-path`.
