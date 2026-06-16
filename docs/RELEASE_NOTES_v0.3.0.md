# paper-three-pass-reader v0.3.0

## Summary

This is the first **stable** release of `paper-three-pass-reader`.
No new features — this release freezes the v0.3 workflow after cleanroom
validation. `v0.3.0-alpha` is the immediately-preceding release; the
delta from `v0.3.0-alpha` is a single housekeeping commit (committing
the historical backlog + `.gitignore` entries for untracked run
artifacts) plus the cleanroom re-run.

## What is stable

- **One-line input commands:** `url`, `arxiv`, `pdf`, `title`, `abstract`,
  `screenshot`, `repo`. Each turns a single source into a filled run
  directory.
- **Two-stage workflow** with `p3pr finalize`. Stage 1: any of the input
  commands above to draft + fill-pack. Stage 2: `p3pr finalize
  <run-dir> --publish` to audit + zh-CN quality gate + render +
  publish + published-pages audit. Auto-infers `site-path` and
  `page-title` from `paper_reading.json` (explicit flags still override).
- **zh-CN-first reading pages.** `target_language=zh-CN` is the default.
  English-source papers get long-English-blob warnings that surface in
  the finalize summary; `--allow-warnings` is the documented opt-in.
- **fill-pack workflow** — every draft ships with `fill-pack/`
  containing stage-specific instructions adapted to the current
  `reading_mode`.
- **Audit and zh-CN quality gate** — `audit_paper_reading.py` checks
  structural completeness; `quality_gate_zh_cn.py` checks bilingual
  discipline. Both block finalize when they FAILED; both surface as
  non-blocking WARN when quality is acceptable-but-shallow.
- **Structured source resolution** — top-level `source_resolution`
  object shared by renderer, audit, fill-pack, and quality gate.
  Legacy `intake_quality.source_resolution` list still supported via
  on-the-fly upgrade (v0.2.8).
- **GitHub Pages publishing** — `publish_output_to_github.sh` pushes
  rendered output to `gh-pages`, regenerates `published_pages.json`,
  and adds the manifest link to the root index `<head>` (v0.2.13).
- **Published-pages audit** — `audit_published_pages.py` reads the
  manifest, fetches every page, checks for template leak / raw dict /
  old footer / missing resolver trail / missing claims / missing
  glossary / essay-mode practice plan.
- **`p3pr status` and `p3pr doctor` (v0.2.19)** — read-only
  observability. `status` scans `runs/` and reads
  `published_pages.json`. `doctor` runs 7 health-check groups and
  prints a `P3PR_DOCTOR_*` summary.
- **site root index and manifest discovery** — the v0.2.13 manifest
  link in `<head>`, the v0.2.12 page-type classification
  (`site_index` / `paper_page` / `manifest` / `unknown`), and the
  v0.2.18 site-path / page-title auto-inference.

## Stable cleanroom checks (this release)

- `bash scripts/validate.sh` — **305 / 0 PASS**
- `./p3pr doctor --offline` — 25 PASS / 0 WARN / 0 FAIL
- `./p3pr doctor --quick` — 25 PASS / 0 WARN / 0 FAIL
- `./p3pr doctor --full` — 25 PASS / 0 WARN / 0 FAIL (also runs `validate.sh` → 305/0 PASS)
- `./p3pr status --runs --site` — PASS, 2 local runs, 13 manifest pages
- live `audit_published_pages.py` — **14 / 14 PASS, 0 warn, 0 fail**
- URL dry-run smoke — `P3PR_SOURCE_URL` printed, no side effects
- arXiv dry-run smoke — `P3PR_RUN_DIR` printed, no `work/` JSON written
- finalize dry-run smoke — `P3PR_FINALIZE_DRY_RUN: true`,
  `P3PR_SITE_PATH: you-and-your-research`, `P3PR_PAGE_TITLE: You and
  Your Research`
- `gh auth status OK`
- Working tree: **clean**
- No old tags moved
- No force pushes
- No published pages removed

## Compatibility

- Existing v0.2.x and v0.3.0-alpha run directories remain compatible.
- Existing Pages remain published.
- Existing tags (v0.2.0-alpha through v0.3.0-alpha) are not moved.
- All v0.2.15 / v0.2.17 / v0.2.18 / v0.2.19 publish guards and finalize
  UX are preserved (verified by validation steps 20l, 22e, 22, 23).

## Notes

This stable release does not add new features beyond v0.3.0-alpha. It
marks the current workflow as the first stable release after a
cleanroom re-run on a clean working tree.

The housekeeping delta from `v0.3.0-alpha` to `v0.3.0`:

- `.gitignore` gained a section for historical P3PR local run artifacts
  that are kept on disk for reproducibility but not committed. 21
  untracked run dirs from prior phases (v0.2.5 / v0.2.16 / v0.2.18 /
  v0.3.0-alpha) are now ignored.
- 4 tracked-modified files from prior phases (v0.2.10 post-release doc
  polish, v0.2.18 finalize smoke refresh, v0.2.15 fill-pack snapshot
  re-saves) are committed as historical artifacts.
- `docs/PHASE_P3PR_V0_3_0_CLEANROOM_HOUSEKEEPING_REPORT.md` is the
  full record of the housekeeping delta.
- `p3pr doctor` summary counter bug fix from `v0.3.0-alpha` is
  preserved.

The 5 phases from `v0.2.14` through `v0.3.0-alpha` are documented in
their respective `docs/PHASE_P3PR_V0_2_14_*` /
`docs/PHASE_P3PR_V0_2_15_*` / … / `docs/PHASE_P3PR_V0_3_0_*.md` phase
reports.
