# paper-three-pass-reader v0.3.0-alpha

## Summary

This is the first **stable-readiness release candidate** for
`paper-three-pass-reader`. It is `v0.3.0-alpha`, not `v0.3.0` stable. The
project is feature-complete enough to cut a stable line after v0.2.x; the
remaining gap is operational — a few more real paper runs and one more
audit cycle.

## What is included

- **One-line input commands** — `p3pr url` / `arxiv` / `pdf` / `title` /
  `abstract` / `screenshot` / `repo`. Each turns a single source into a
  filled run directory.
- **Two-stage workflow with `p3pr finalize`** — stage 1: any of the input
  commands above to draft + fill-pack. Stage 2: `p3pr finalize <run-dir>
  --publish` to audit + zh-CN quality gate + render + publish + published-
  pages audit. Auto-infers `site-path` and `page-title` from
  `paper_reading.json` (explicit flags still override).
- **zh-CN-first reading pages** — `target_language=zh-CN` is the default.
  English-source papers get long-English-blob warnings that surface in the
  finalize summary; `--allow-warnings` is the documented opt-in.
- **fill-pack workflow** — every draft ships with `fill-pack/` containing
  stage-specific instructions adapted to the current `reading_mode`.
- **Audit and zh-CN quality gate** — `audit_paper_reading.py` checks
  structural completeness; `quality_gate_zh_cn.py` checks bilingual
  discipline. Both block finalize when they FAILED; both surface as
  non-blocking WARN when quality is acceptable-but-shallow.
- **Structured source resolution** — top-level `source_resolution` object
  shared by renderer, audit, fill-pack, and quality gate. Legacy
  `intake_quality.source_resolution` list still supported via on-the-fly
  upgrade (v0.2.8).
- **GitHub Pages publishing** — `publish_output_to_github.sh` pushes
  rendered output to `gh-pages`, regenerates `published_pages.json`, and
  adds the manifest link to the root index `<head>` (v0.2.13).
- **Published-pages audit** — `audit_published_pages.py` reads the
  manifest, fetches every page, checks for template leak / raw dict / old
  footer / missing resolver trail / missing claims / missing glossary /
  essay-mode practice plan.
- **`p3pr status` and `p3pr doctor` (v0.2.19)** — read-only observability.
  `status` scans `runs/` and reads `published_pages.json`. `doctor` runs
  7 health-check groups and prints `P3PR_DOCTOR_*` summary.
- **URL / arXiv / PDF / title / abstract / screenshot / repo input coverage** —
  7 input modes sharing one runner. `p3pr url` was added in v0.2.14 with
  stdlib-only HTML extraction.

## Stable-readiness checks (this run)

- `bash scripts/validate.sh` — **305 / 0 PASS**
- `./p3pr doctor --offline` — 24 PASS / 1 WARN (dirty tree) / 0 FAIL
- `./p3pr doctor --quick` — 24 PASS / 1 WARN (dirty tree) / 0 FAIL
- `./p3pr doctor --full` — 24 PASS / 1 WARN (dirty tree) / 0 FAIL
- `./p3pr status` — 2 local runs (1 published, 1 rendered), 13 manifest pages
- live `audit_published_pages.py` — **14 / 14 PASS, 0 warn, 0 fail**
- URL dry-run smoke — `P3PR_SOURCE_URL` printed, no side effects
- finalize dry-run smoke — `inferred_site_path` + `P3PR_SITE_PATH` printed, no side effects
- **No old tags moved, no force pushes, no published pages removed.**

## Compatibility

- Existing v0.2.x run directories remain compatible.
- Existing Pages remain published.
- Existing tags are not moved.
- v0.2.15 publish-gate (BLOCK on missing `index.html`) preserved.
- v0.2.17 finalize guards preserved.
- v0.2.18 finalize UX (auto-inference + richer summary) preserved.
- v0.2.19 status / doctor preserved.

## Not yet stable

This is still `v0.3.0-alpha`, not `v0.3.0` stable. The next stable release
should follow after:

1. At least a few more real paper runs through the two-stage flow
2. One more round of `audit_published_pages.py` after the new runs land
3. A final `p3pr doctor --full` pass on a clean working tree

## How to use it

```bash
# Stage 1 — input
./p3pr url https://www.cs.virginia.edu/~robins/YouAndYourResearch.html \
    --zh --full --no-publish

# Fill per the fill-pack (edit work/paper_reading.json)

# Stage 2 — finalize + publish
./p3pr finalize runs/<run-dir> --publish

# Manage
./p3pr status
./p3pr doctor --offline
./p3pr doctor --full

# Site audit
python3 skills/paper-three-pass-reader/scripts/audit_published_pages.py \
    --manifest-url https://conanxin.github.io/paper-reading-pages/published_pages.json \
    --site-root https://conanxin.github.io/paper-reading-pages \
    --include-root --warn-only
```
