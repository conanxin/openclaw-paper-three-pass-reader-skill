# Changelog

All notable changes to `paper-three-pass-reader` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [v0.2.14-alpha] — 2026-06-16

### Added

- **`p3pr url <url>` subcommand.** New one-line CLI handler that fetches an HTML page (or PDF) from a user-supplied URL, runs a stdlib-only `html.parser` extraction to plain text, and feeds the result to the existing runner / fill-pack / audit / quality-gate / render / publish pipeline as `input_kind=paper_url`. The CLI does NOT call external LLM APIs; it just orchestrates the existing scripts. Supports `--zh / --en / --language`, `--full / --partial / --abstract-only / --screenshot-only`, `--slug`, `--output-root`, `--title`, `--authors`, `--year`, `--fill-pack / --no-fill-pack`, `--audit / --no-audit`, `--quality-gate / --no-quality-gate`, `--render / --no-render`, `--publish / --no-publish`, `--repo`, `--branch`, `--page-title`, `--audit-warn-only`, `--allow-draft-publish`, `--dry-run`. New `P3PR_SOURCE_URL:` line in the standard summary.
- **HTML fetch + stdlib extraction.** New `_HTMLTextExtractor` and `_fetch_url()` helpers in `p3pr.py` (stdlib-only — no `requests`, no `BeautifulSoup`). Drops `<script>` and `<style>`. Preserves block-level separators (`p`, `div`, `section`, headings, lists, `br`, `pre`). Captures `<title>`. Auto-detects PDFs by URL suffix / `Content-Type` / `%PDF-` magic bytes. The runner receives the extracted text via `--input-file` plus the URL via `--paper-url`; the draft's `paper_metadata.identifiers.url` records the user-supplied URL and `source_kind` is set to `paper_url`.
- **Runner accepts `--input` and `--input-file` together.** v0.2.14-alpha relaxes the runner's old "only one of --input / --input-file" check. `--input` is the audit-trail / hint-lookup string; `--input-file` is the body that gets captured into `input/input.md`. This makes the `url` subcommand's workflow idiomatic and supports other "I have a URL and a pre-extracted body" callers.
- **Reading-mode discipline for URL input.** If HTML extraction produces >= 800 chars of text, the CLI sets `reading_mode = full_text`; otherwise `partial_text`. PDFs without extracted body stay at `partial_text` (we do NOT pretend a PDF without text is `full_text`). User `--full / --partial / --abstract-only / --screenshot-only` always override.
- **`scripts/validate.sh` step 20.** 17 new sub-checks: `p3pr url --help` runs; `p3pr --help` lists the url subcommand; URL dry-run emits `P3PR_INPUT_KIND: paper_url` / `P3PR_READING_MODE: full_text` / `P3PR_SOURCE_URL: ...`; URL smoke run produces `input/source_pointer.txt`, `source/source.html`, `extracted/page.txt` (>800 chars), `work/paper_reading.json` with `paper_url` + `source_resolution`, and a rendered `paper-reading-output/index.html` with Chinese UI; all 6 existing subcommands (`arxiv / title / abstract / screenshot / repo / pdf`) still answer `--help`. Validation is now 261/0 PASS (was 242/0 PASS at v0.2.13-alpha).
- **Real-URL smoke run.** `runs/p3pr-url-smoke-20260616/you-and-your-research-cn-url-smoke/` — fetched Hamming's *You and Your Research* (https://www.cs.virginia.edu/~robins/YouAndYourResearch.html), extracted 78,593 chars of text via stdlib HTML parser, ran the full pipeline.
- **Live URL smoke page published.** A separate slug `you-and-your-research-url-smoke-cn` was published to `conanxin.github.io/paper-reading-pages/you-and-your-research-url-smoke-cn/` (does NOT overwrite the formal `you-and-your-research-cn` page). Live audit after the publish reports `overall=PASS pages=11 pass=11 warn=0 fail=0` with `page_type_counts: {site_index: 1, paper_page: 10, manifest: 0, unknown: 0}`. Audit artifacts at `runs/published-pages-audit-20260615-url-smoke/audit.{json,md}`.
- **`docs/RELEASE_NOTES_v0.2.14-alpha.md`** and **`docs/PHASE_P3PR_V0_2_14_URL_SUBCOMMAND_REPORT.md`** — release notes + final phase report.

### Compatibility

- Existing pages remain readable. The only consumer page newly published is the URL smoke page (`you-and-your-research-url-smoke-cn`).
- Existing subcommands (`arxiv / title / abstract / screenshot / repo / pdf`) are unchanged.
- The runner's old "only one of --input / --input-file" check is removed in favour of allowing both; downstream callers that passed exactly one continue to work.
- No old tags moved. v0.2.10-alpha / v0.2.12-alpha / v0.2.13-alpha stay at their original commits.

## [v0.2.13-alpha] — 2026-06-16

### Added

- **Manifest link in generated root index.** `publish_output_to_github.sh` now emits both `<link rel="alternate" type="application/json" href="published_pages.json" title="Published pages manifest" />` in the `<head>` and a visible `<a href="published_pages.json">` link in the About section (with English + Chinese labels: "Machine-readable manifest: ... · 页面清单 JSON"). Users see the manifest link directly on the index; tools can discover the JSON via `<link rel="alternate">`.
- **Audit recognizes the manifest link.** `_check_site_index()` in `audit_published_pages.py` now accepts either a visible `<a href="published_pages.json">` link OR a `<link rel="alternate" type="application/json" href="published_pages.json">` machine-readable discovery tag. A root index emitted by the current publisher no longer triggers the info-level `index_no_manifest_link` finding.
- **`scripts/validate.sh` step 19.** Six new sub-checks: publisher-generated index contains `published_pages.json`; generated index contains the manifest link in either form; fake root index with manifest link does not trigger `index_no_manifest_link`; fake root index without manifest link still triggers it (info-level); audit JSON classifies `site_index` AND has no paper-level warnings on the root; live site audit root index no longer triggers `index_no_manifest_link`. Validation is now 242/0 PASS (was 236/0 PASS at v0.2.12-alpha).
- **One new selftest fixture** (`fake-site-index-no-manifest`): a root index with no link to `published_pages.json`, must still trigger `index_no_manifest_link` at info level.
- **Live audit landed clean.** Live run against `conanxin.github.io/paper-reading-pages` now reports `[audit] overall=PASS pages=10 pass=10 warn=0 fail=0` with `issues_by_severity: {error: 0, warning: 0, info: 8}` (was 9 info — one fewer `index_no_manifest_link`). Recorded under `runs/published-pages-audit-20260615-root-index-manifest-link/`.
- **`docs/RELEASE_NOTES_v0.2.13-alpha.md`** and **`docs/PHASE_P3PR_V0_2_13_ROOT_INDEX_MANIFEST_LINK_REPORT.md`** — release notes + final phase report.

### Changed

- `skills/paper-three-pass-reader/scripts/publish_output_to_github.sh` — root index generator now emits the manifest link (two forms) on every publish.
- `skills/paper-three-pass-reader/scripts/audit_published_pages.py` — `_check_site_index` now accepts the `<link rel="alternate">` form; old text-only fallback (`"published_pages.json" not in body`) replaced with a structured regex pair.
- `scripts/validate.sh` — step 17 selftest fixture list bumped from 8 to 9 (added `fake-site-index-no-manifest`); step 19 adds 6 new sub-checks; the existing fake-site-index fixture now carries the manifest link in both forms.

### Compatibility

- Existing pages remain readable. The only consumer page republished by this release is `you-and-your-research-cn` (used as the trigger to refresh the root index).
- `published_pages.json` schema is unchanged.
- No old tags moved. v0.2.10-alpha / v0.2.12-alpha stay at their original commits.
- The audit JSON's `index_no_manifest_link` finding still appears in legacy reports / older runs that don't have the new manifest link; new reports from this release will no longer show it on the live site.

## [v0.2.12-alpha] — 2026-06-16

### Added

- **Page-type classification** in `audit_published_pages.py`. Every audited page is now classified as one of `site_index` / `paper_page` / `manifest` / `unknown`. The classification is recorded as a new `page_type` field on every `pages[*]` entry, and a top-level `page_type_counts` object summarises the audit's page-type distribution.
- **Root-index audit exemption.** Pages classified as `site_index` (the `<site_root>/` manifest) are now exempt from the paper-level check set: `missing_resolver_trail` / `missing_claims_section` / `missing_glossary` / `no_visible_claim_id` / `no_evidence_label` / `glossary_no_explicit_definition` / `essay_missing_markers` / `zh_cn_markers_weak` / `empty_claim_id` no longer fire on the root index. The three severe checks (`template_leak` / `raw_dict` / `old_footer`) **still** fire on the root index — those would still be real regressions.
- **Index-specific checks** (`_check_site_index`): title present, ≥1 published-page link, manifest reference present, link-vs-manifest delta within tolerance. Surfaced as `index_missing_title` / `index_no_page_links` / `index_links_mismatch` / `index_no_manifest_link`.
- **Manifest-specific checks** (`_check_manifest_pages`): pages list present, every entry has `slug` + `title` + `path`, no duplicate slugs / paths. Surfaced as `manifest_pages_not_list` / `manifest_empty` / `manifest_incomplete_entries` / `manifest_duplicate_slugs` / `manifest_duplicate_paths`. The manifest check is always emitted; with `--include-manifest` the manifest JSON itself is fetched and audited too.
- **`--include-manifest` CLI flag.** Default off; opt-in audit of the `published_pages.json` JSON itself (classified as `manifest`).
- **`## Page Type Summary` section** in the Markdown audit report (one row per `page_type`).
- **Live audit landed at PASS.** Live run against `conanxin.github.io/paper-reading-pages` now reports `[audit] overall=PASS pages=10 pass=10 warn=0 fail=0` (was `WARN/1/0/0`). Recorded under `runs/published-pages-audit-20260615-root-index-exemption/`.
- **`scripts/validate.sh` step 18.** Adds 11 sub-checks for the page-type classifier and the exemption. Two new selftest fixtures (`fake-site-index` clean, `fake-site-index-leak` with `{% else %}`). One new live-site smoke sub-check that asserts `page_type_counts.site_index >= 1`. Validation is now 236/0 PASS (was 225/0 PASS at v0.2.10).
- **`docs/RELEASE_NOTES_v0.2.12-alpha.md`** and **`docs/PHASE_P3PR_V0_2_12_ROOT_INDEX_AUDIT_EXEMPTION_REPORT.md`** — release notes + final phase report.

### Changed

- `audit_published_pages.py` `schema_version` bumped from `0.1.0` to `0.2.0` to reflect the new top-level `page_type_counts` and per-page `page_type`.
- The recommendations builder now distinguishes paper-level issue codes from site-index-specific issue codes; site-index exemption is surfaced as `Root index is treated as site_index and exempted from paper-page checks (...)` whenever the root index passes.
- The Markdown report's `## Detailed issues` section now records each page's `page_type` and, for `site_index` pages, the line `Paper-level checks: skipped by design`.

### Compatibility

- Existing pages remain unchanged. The v0.2.11 remediation commit stays valid; no consumer pages are re-rendered by this release.
- Existing audit output (downstream consumers that only read `pages_pass` / `pages_warn` / `pages_fail` / `issues_by_severity` / `pages[*].issues`) remains readable; new fields are additive.
- No old tags moved. v0.2.10-alpha is immutable and stays at the v0.2.10 remediation commit.

## [v0.2.10-alpha] — 2026-06-15

### Added

- **Published-pages regression audit** — new stdlib-only CLI `skills/paper-three-pass-reader/scripts/audit_published_pages.py`. Reads `published_pages.json` (live URL or local file), fetches every page, and produces a JSON + Markdown audit report covering HTTP errors, template-tag leaks, raw dict reprs, old footers, weak zh-CN UI markers, missing Resolver Trail, missing Claims / Glossary, and essay-mode regressions.
- **Selftest mode** — `audit_published_pages.py --selftest-dir <dir>` runs six synthetic pages through the same checks and reports which expected codes were detected. No network access required.
- **`scripts/validate.sh` step 17** — invokes the selftest mode and asserts the audit's JSON / Markdown outputs and per-fixture expectations. Validation is now 225/0 PASS (was 220/0 PASS at v0.2.9).
- **`skills/paper-three-pass-reader/docs/PUBLISHED_PAGES_AUDIT.md`** — canonical reference for the audit tool: check list, severity table, output format, PASS / WARN / FAIL semantics, when to run.
- **First live audit run** — `runs/published-pages-audit-20260615/audit.json` + `audit.md`. The audit found that 8 of 9 published pages (rendered before v0.2.9) still carry legacy-render artefacts; the v0.2.9-re-published `you-and-your-research-cn` page is the only PASS.

### Notes

- v0.2.9-alpha stays immutable; this release lands as v0.2.10-alpha.
- The audit is read-only. It never writes to `gh-pages`, never republishes anything, never triggers re-renders.
- No existing page is changed by this release.
- The first audit run reports `FAIL` overall — this is expected and is the audit's intended use: surface pages that need re-rendering in a future release.

## [v0.2.9-alpha] — 2026-06-15

### Added

- **Generator version in rendered pages** — `templates/index.html` footer now reads `paper-three-pass-reader v0.2.9-alpha` (the value is exposed by the renderer as `data["generator_version"]`).
- **Essay / talk detection** — renderer classifies inputs as `essay / talk` when the paper category is one of `essay / talk / keynote / lecture / opinion / blog-distillation` and exposes `data["_is_essay_talk"]` to the template.
- **Essay-mode practical-plan block** — `Reproduction Plan` heading switches to `实践计划` for essay inputs; the body renders 7/30/90-day plans, success criteria, and risks derived from the source.
- **Essay-mode figures & tables** — empty state now reads `原文无传统图表` followed by conceptual notes (e.g. Hamming's 5 most-quoted frameworks) for essay-mode inputs.
- **Essay-mode related-work fallback** — `Related Work` is renamed `相关脉络` and shows a clean fallback note for essay-mode inputs that have no formal related-work section.
- **Glossary definition display** — glossary chips now show term + Chinese term + Chinese definition in an explicit body block.

### Fixed

- **Renderer raw-dict leak** — the Five Cs cards previously rendered `{'label': ...}` dict reprs. Each Five-C item is now normalised into `{label, value, evidence_label, note}` before rendering.
- **Renderer template-tag leak** — the mini-template engine now understands `{% if … %} … {% else %} … {% endif %}` and no longer leaks `{% else %}` (or any other unclosed `{% %}` / `{{ }}`) into the rendered HTML.
- **Claim ID display** — the Claims-Evidence table now shows real `C01` / `C02` / `…` IDs (the renderer derives `claim_id` from `id` when only the latter is present).
- **Stale footer version** — the page footer no longer says `v0.1.0-alpha`.
- **Validation step 5 brittle assertion** — the `class="accordion"` legacy CSS-class assertion is replaced with a robust `details / accordion` regex check that accepts the v0.2.9 template's native `<details>` markup.

### Re-published

- Chinese *You and Your Research* page → <https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/>.

### Notes

- v0.2.8-alpha stays immutable; this release lands as v0.2.9-alpha.
- Validation: 220/0 PASS (210 v0.2.8 baseline + 10 new step-16 essay / talk checks).
- `quality_gate_zh_cn` reports a single `long_en_blobs` warning on `claims_evidence_map[0].comment` (Hamming's intentional direct English quote) — preserved by design.

## [v0.2.8-alpha] — 2026-06-15

### Added

- **Source-resolution utility** — new `skills/paper-three-pass-reader/scripts/source_resolution_utils.py` is the single shared helper for consumers of the structured top-level `source_resolution` block. Exposes `is_structured_source_resolution`, `get_source_resolution`, `legacy_source_resolution_to_structured`, `summarize_source_resolution`, `validate_source_resolution`. stdlib-only.
- **Renderer Resolver Trail section** — `templates/index.html` adds a new `#resolver-trail` card. Renders Resolver status, Match type, Confidence, Matched paper / id, Matched arXiv ID, Matched repo, Resolver source, Source resolution step, Candidate count, Top 3 candidates, a "Degraded fallback" badge and an error callout. Fully localised for zh-CN.
- **Audit source-resolution validation** — `audit_paper_reading.audit` adds a `source_resolution` field to the OrderedDict result with `status / structured / legacy_fallback / warnings / errors / summary`. WARNs on legacy-only, WARNs on missing block (non-weak modes), WARNs on `matched` without identity, WARNs on missing confidence, FAILs on `error` with no degraded / warning marker.
- **Fill-pack source-resolution checklist** — `fill-pack/00_README.md` (zh-CN and en) embeds a Source Resolution 摘要 block plus a Source Resolution Checklist the agent must tick off before Stage 0 closes.
- **zh-CN quality gate source_resolution_check** — `quality_gate_zh_cn.run_quality_gate` adds a `source_resolution_check` field; warnings surface as recommendations and never fail the gate on their own.
- **Documentation** — new `skills/paper-three-pass-reader/docs/SOURCE_RESOLUTION.md` is the canonical reference for the structured block, its consumers, and the helper API.

### Notes

- The top-level structured `source_resolution` block is canonical. The legacy `intake_quality.source_resolution` list is **kept** for back-compat with v0.2.5 samples; the shared utility upgrades it on the fly.
- v0.2.7-alpha stays immutable; this release lands as v0.2.8-alpha.
- Validation: 210/0 PASS (167 v0.2.5 baseline + 28 step 13 + 15 step 14 + 15 step 15 new checks).

## [v0.2.7-alpha] — 2026-06-15

### Added

- **Structured `source_resolution` block** — every draft now writes a top-level `source_resolution` object that records the full resolver trail: `steps`, `hint_input`, `resolver_source`, `resolver_helper`, `resolver_status`, `resolver_match_type`, `confidence`, `matched_paper_id`, `matched_canonical_title`, `matched_arxiv_id`, `matched_alias`, `matched_repo`, `candidates`, `source_resolution_step`. Replaces the previous flat list and gives agents a single, queryable view of how a paper was resolved.
- **CLI → runner overlay** — `p3pr` writes `work/resolver_source.json` from its own resolver result. The runner reads it via `--resolver-source` and overlays it on top of its auto-detected match, so a CLI-resolved paper id beats whatever the runner's auto-detect would otherwise produce.
- **Runner `--resolver-source` support** — `run_paper_reading.py` accepts a JSON file path; the helper that file produces is applied to the draft's `source_resolution` block as the final step.
- **Resolver helper degradation behaviour** — the resolver helper call is wrapped in `try/except`. On any exception the runner records `resolver_status=error`, sets `degraded=ambiguous_clue`, appends a warning to `intake_quality.warnings`, and **continues with rc=0**. A broken helper cannot fail a run.
- **Hostile-resolver validation** — `scripts/validate.sh` step 14 includes a hostile test that forces the resolver helper to raise on every call and asserts (a) the runner exits 0, (b) `paper_reading.json` is written, (c) `source_resolution.resolver_status=error`, (d) `source_resolution.degraded=ambiguous_clue`. 14 new checks in step 14.
- **Documentation cross-link** — `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` Q&A "How do I add a new hint?" now points at `data/resolver_hints.json` and `docs/RESOLVER_HINTS.md`. New sections in `RESOLVER_HINTS.md` and `ONE_LINE_CLI.md` describe the structured `source_resolution` block and the degradation behaviour.

### Notes

- v0.2.6-alpha is **immutable**. The round-2 hardening is released as v0.2.7-alpha, not as a move of v0.2.6-alpha. Published tags are never re-pointed.
- The legacy flat `intake_quality.source_resolution` list is preserved for back-compat with v0.2.5 smokes and pre-v0.2.7 readers.
- Validation remains PASS at 195/0 (167 v0.2.5 baseline + 28 step 13 + 14 step 14).

## [v0.2.6-alpha] — 2026-06-15

### Added

- **Shared resolver hints data source** — new `skills/paper-three-pass-reader/data/resolver_hints.json` is now the single source of truth for paper / repo / arXiv resolution. Replaces the duplicate HINTS dict that used to live in `p3pr.py` and the duplicate `RESOLVER_HINTS` dict that used to live in `run_paper_reading.py`. New hints can be added in one place and the runner + CLI + tests + docs all pick them up.
- **Resolver helper module** — new `skills/paper-three-pass-reader/scripts/resolver_hints.py` (stdlib-only). Public API: `load_hints()`, `normalize_text()`, `resolve_title()`, `resolve_arxiv()`, `resolve_repo()`, `resolve_any()`, `paper_to_runner_overrides()`. Each resolver returns `{status, match_type, confidence, paper, candidates, source_resolution_step}` so callers can distinguish `matched` / `ambiguous` / `not_found`.
- **Standalone resolver CLI** — `skills/paper-three-pass-reader/scripts/resolve_paper_hint.py {title|arxiv|repo|any} <value>` prints the resolver's JSON output. Useful for tests, docs, and humans debugging a hint.
- **Unified anchor papers** — `resolver_hints.json` ships with 5 anchor papers: Attention Is All You Need (1706.03762), BERT (1810.04805), How to Read a Paper (Keshav, 2007), Second Me (2503.08102), and the paper-three-pass-reader-skill repo itself. Each paper has canonical title, aliases, authors, year, venue, arXiv id, paper URL, default slug, field, and notes. Aliases match case-insensitively (e.g. `transformers` → Attention, `second me` → Second Me).
- **Backwards-compatible runner API** — `run_paper_reading.RESOLVER_HINTS` is now auto-built from `resolver_hints.json` so any historical code path that imports the dict still works. The runner's `_resolve_hint()` now prefers the shared resolver and falls back to the legacy substring matcher.
- **CLI auto-resolution of canonical metadata** — when you pass a recognizable title / repo / arXiv id to `p3pr`, the CLI now auto-fills `title`, `arxiv_id`, `paper_url`, and `default_slug` from the shared resolver, and shows the resolver's diagnostic in the run summary:
  `P3PR_RESOLVER_STATUS` / `P3PR_RESOLVER_MATCH_TYPE` / `P3PR_CANONICAL_TITLE` / `P3PR_ARXIV_ID` / `P3PR_DEFAULT_SLUG`.
- **CLI screenshot/abstract smart auto-derivation** — `p3pr screenshot` and `p3pr abstract` now run the resolver against the first 400 chars of the input file. If the transcript contains a known paper (e.g. a Second Me screenshot transcript), the CLI auto-derives the arXiv id, switches the slug prefix from `screenshot-` to `arxiv-`, and pulls canonical title — without pretending the input is a full paper.
- **Unknown hint handling** — when no hint matches, the CLI does NOT fail. It logs `P3PR_RESOLVER_STATUS: not_found`, keeps the weak-mode default, and shows the user how to proceed (edit work/paper_reading.json, follow fill-pack, re-run).
- **Validation extended** — `scripts/validate.sh` now has 179 checks (was 151). New step 13 covers: resolver_hints.json exists + valid + has 5 anchor papers; resolver_hints.py loads; resolve_paper_hint CLI works for title / arxiv / repo / any; unknown input returns not_found; aliases work; p3pr.py no longer has local HINTS; p3pr.py + run_paper_reading.py import from resolver_hints; runner RESOLVER_HINTS back-compat dict has 26 keys; historical keys still resolve; p3pr dry-run shows resolver details; title and repo auto-resolve; screenshot smoke auto-detects arXiv from transcript.
- **Documentation** — new `skills/paper-three-pass-reader/docs/RESOLVER_HINTS.md` explains the single source of truth, the resolver API, and how to add new hints.

### Notes

- This is a refactor. No user-facing CLI behavior changes for v0.2.5 commands.
- `RESOLVER_HINTS` in the runner is now derived data, not authoritative. To add a new paper, edit `data/resolver_hints.json`.
- Aliases are case-insensitive. Whitespace and surrounding quotes / parens are stripped. arXiv id matching works inside arXiv URLs or bare ids. Repo matching handles GitHub URLs, owner/repo fragments, and case-insensitive URL substrings.

## [v0.2.3-alpha] — 2026-06-15

### Added

- **First-class Chinese (zh-CN) output support** — the runner, fill-pack, audit, and renderer all carry language fields. Pages are now fully bilingual-capable.
- **Runner language propagation** — `run_paper_reading.py` now writes `target_language` and `ui_language` to the draft JSON. Both default to whatever `--language` was passed (default `zh-CN`).
- **Renderer UI localization** — `render_page.py` reads `ui_language` and applies a deterministic English→Chinese UI label map. The map covers: section headings, key terms, evidence labels (preserved in English), tabs, accordions, all metadata labels.
- **Audit Chinese content check** — when `target_language` / `ui_language` = `zh-CN`, the audit scans 5 main interpretive fields (`summaries.one_sentence`, `pass2.main_ideas`, `pass3.method_reconstruction`, `pass3.critical_review`, `glossary.definitions`) and warns if fewer than 50% contain Chinese characters. Evidence labels, paper names, and method names in English do NOT trigger the warning.
- **Second Me Chinese full-text run** — new run directory `runs/second-me-zh-cn-20260615/second-me-human-inspired-memory-cn/` with 12 claims, 7 figure/table entries, 14 glossary terms, 12-item checklist. Audit: PASS, 0 errors / 0 warnings.
- **Chinese page published** — `https://conanxin.github.io/paper-reading-pages/second-me-human-inspired-memory-cn/` (HTTP 200).
- **Validation extended** — `scripts/validate.sh` now has 120 checks (was 108). New step 10 covers: runner `--language` flag, zh-CN draft `target_language` / `ui_language`, Chinese fill-pack content, Chinese UI label presence, audit Chinese-content warning, Second Me zh-CN real run audit, Second Me zh-CN page label check.

### Notes

- Evidence labels remain **fixed English enums** (`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`) regardless of UI language. They are intentionally untranslatable so the audit can match them.
- Paper titles, method names, benchmark names, and author names remain in their original form (English or Chinese as the author wrote them).
- Re-rendering an `en` draft still produces an English page; the locale only kicks in when the JSON explicitly says `ui_language = "zh-CN"`.

## [v0.2.4-alpha] — 2026-06-15

### Added

- **zh-CN quality gate** — new `skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py`. Goes beyond "does this draft have Chinese?" to "is the Chinese explanation actually a reading?". Catches: low CJK coverage, long English blobs (carryover from English draft), too-few glossary/claims/checklist items, full_text mode with no `[Paper evidence]` claims, missing Pass 2/3 in full_text mode.
- **Audit `--quality-gate` integration** — when `target_language` / `ui_language` is `zh-CN` and the flag is passed, the audit calls the quality gate after the structural audit and exits non-zero on quality-gate FAIL. Without the flag, the audit prints a hint to re-run with `--quality-gate`.
- **Runner `--quality-gate` integration** — `run_paper_reading.py --quality-gate` (only effective with `--language zh-CN`) runs the quality gate after the audit and writes `work/quality_gate_zh_cn.json` and `reports/quality_gate_zh_cn.md`. Quality-gate FAIL blocks `--render` and `--publish` unless `--audit-warn-only` is set.
- **Fill-pack `11_zh_cn_quality_gate.md`** — new step in the agent fill pack that explains what the quality gate checks, how to fix common WARN/FAIL patterns, why evidence labels stay in English, and why "has CJK chars" is not enough.
- **Bad zh-CN sample** — `runs/quality-gate-smoke-20260615/bad-zh-cn-draft/` for validation: declares `target_language = zh-CN` but contains English content + only 2 claims + empty glossary + 2-item checklist. Quality gate returns FAIL with 4 errors and 4 warnings. This guards against the quality gate becoming a rubber stamp.
- **Validation extended** — `scripts/validate.sh` now has 129 checks (was 120). New step 11 covers: quality-gate script help, executable, Second Me zh-CN PASS, bad sample FAIL, runner `--quality-gate` flag, audit `--quality-gate` flag, fill-pack `11_zh_cn_quality_gate.md` present, audit `--quality-gate` integration PASS, audit default hint on zh-CN run.
- **Documentation** — new `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md`. `RUNNER.md`, `AUDIT.md`, `AGENT_FILL_PACK.md`, `USAGE.md`, `README.md`, `CHANGELOG.md`, `docs/AUTOFILL_RUNS.md`, `docs/REALPAPER_RUNS.md` updated. Release notes and phase report.

### Design notes

- The quality gate is **structural + bilingual-discipline**, not LLM-truth-judging. It catches specific failure modes that "audit alone" misses but does not score translation quality subjectively.
- Evidence labels remain fixed English enums for audit compatibility. Explanatory text around them is Chinese.
- The default zh-CN thresholds (8 claims, 10 glossary, 8 checklist, 50% CJK ratio) are tuned for full_text real-paper readings, not weak-mode drafts. For weak-mode drafts, the quality gate should be run with `--warn-only`.

## [v0.2.5-alpha] — 2026-06-15

### Added

- **One-line CLI** — `p3pr` (shell shim at repo root) wraps `skills/paper-three-pass-reader/scripts/p3pr.py` (stdlib-only Python). The CLI orchestrates the existing runner / fill-pack / audit / zh-CN quality gate / renderer / publisher into a single command:
  - `./p3pr arxiv 2503.08102 --zh --full --publish`
  - `./p3pr title "Attention Is All You Need" --zh --full --publish`
  - `./p3pr abstract path/to/abstract.md --zh --publish`
  - `./p3pr screenshot path/to/transcript.md --zh --publish`
  - `./p3pr repo https://github.com/google-research/bert --zh --full --publish`
  - `./p3pr pdf path/to/paper.pdf --zh --full --publish`
- **Defaults**: `language = zh-CN`, `fill_pack = true`, `audit = true`, `quality_gate = true` (only when `language == zh-CN`), `render = true`, `publish = false`, `repo = conanxin/paper-reading-pages`, `branch = gh-pages`.
- **Boundaries enforced**: weak-mode drafts (screenshot_only / abstract_only) do NOT pretend full_text. `--publish` is BLOCKED on quality-gate FAIL unless `--allow-draft-publish` is set. `--dry-run` skips downloads / extraction.
- **Fixed-format summary** at end of every CLI run:
  `P3PR_STATUS` / `P3PR_INPUT_KIND` / `P3PR_READING_MODE` / `P3PR_RUN_DIR` / `P3PR_JSON` / `P3PR_FILL_PACK` / `P3PR_LOCAL_PAGE` / `P3PR_PAGE_URL` / `P3PR_NEXT_ACTION`.
- **CLI smoke runs** — `runs/p3pr-cli-smoke-20260615/` has 2 local smoke runs (screenshot + abstract) and 4 dry-runs (arxiv / title / repo / pdf). CLI smoke runs do not pretend full_text on weak inputs.
- **Validation extended** — `scripts/validate.sh` now has 151 checks (was 129). New step 12 covers: p3pr shim executable, p3pr help, all 6 subcommands, arxiv dry-run summary, title / repo dry-runs, screenshot smoke JSON + fill-pack, abstract smoke reading_mode, weak-input not pretending full_text.
- **Documentation** — new `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md`. `README.md`, `CHANGELOG.md`, `RUNNER.md`, `USAGE.md`, `ZH_CN_QUALITY_GATE.md` updated. Release notes and phase report.

### Design notes

- The CLI is a **thin wrapper**; it does NOT call external LLM APIs and does NOT do any deep reading. The reading is the fill-pack job.
- Subcommands share the same flag set (forwarded from parent argparse) so users can put flags before or after the subcommand.
- The CLI keeps its own copy of the resolver hints (`HINTS` dict) so dry-runs can resolve without invoking the runner.

### Changed

- `render_page.py` — `render_index` now reads `ui_language` and applies the UI map. Backward compatible: when `ui_language` is absent or `"en"`, behaviour is unchanged.
- `audit_paper_reading.py` — added step 8 (language check). Does not change PASS/WARN/FAIL semantics for `en` drafts.
- `run_paper_reading.py` — `make_draft` now writes `target_language` and `ui_language` at the top level (after `schema_version`).

### Notes

- Evidence labels remain **fixed English enums** (`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`) regardless of UI language. They are intentionally untranslatable so the audit can match them.
- Paper titles, method names, benchmark names, and author names remain in their original form (English or Chinese as the author wrote them).
- Re-rendering an `en` draft still produces an English page; the locale only kicks in when the JSON explicitly says `ui_language = "zh-CN"`.

## [v0.2.2-alpha] — 2026-06-15

### Added

- **Auto-fill smoke run** — `runs/v022-fulltext-autofill-secondme-20260615/second-me-fulltext-autofill/`. End-to-end PDF download + pdftotext extraction + runner draft + agent fill + audit + render + publish for arXiv:2503.08102 ("AI-native Memory 2.0: Second Me", Mindverse.ai).
- **Skill bug fixes** during the smoke:
  - `run_paper_reading.py` no longer `return rc` on audit FAIL when `--fill-pack` is requested (the fill-pack is the task list, must be written even when audit fails).
  - `render_page.py` now tolerates string entries in `pass2.key_references` (same pattern as `claims_evidence_map`).
- **Documentation** — `docs/AUTOFILL_RUNS.md`, `docs/PHASE_P3PR_V0_2_2_FULLTEXT_AUTO_FILL_SMOKE_REPORT.md`, `docs/RELEASE_NOTES_v0.2.2-alpha.md`.

### Notes

- No schema or page-template changes; only runner/render robustness.

## [v0.2.1-alpha] — 2026-06-15

### Added

- **Agent Fill Pack** — new `--fill-pack` flag on the runner. Generates 11 markdown files (`00_README.md` through `10_quality_gate.md`) plus `prompts.json`, `field_checklist.json`, and `draft_status.json` inside `<run_dir>/fill-pack/`. Step instructions adapt to the current reading mode (weak modes carry explicit "weak-input" caveats).
- **Structural audit** — new `skills/paper-three-pass-reader/scripts/audit_paper_reading.py`. Checks JSON shape, enum validity, reading-mode discipline (no over-claims in weak modes), claims-evidence whitelist, and final_checklist counts. Output is a JSON document + markdown summary.
- **Runner audit integration** — `--audit` flag invokes the audit after the draft is written. If audit status is FAIL, the runner refuses to render or publish (relax with `--audit-warn-only`).
- **Runner profile + language** — `--agent-profile` (default / strict / beginner / researcher / engineer), `--language` (zh-CN / en), `--max-claims`, `--max-figures`.
- **Docs** — `skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md`, `skills/paper-three-pass-reader/docs/AUDIT.md`. RUNNER.md / USAGE.md / OUTPUT_SCHEMA.md extended with v0.2.1 sections.
- **Validation** — `scripts/validate.sh` extended to 108 checks across 9 steps, covering the new flags, scripts, and 3 reading-mode smoke runs (title / abstract / screenshot).

### Notes

- The audit is **structural + reading-mode discipline** only. It does not judge whether the paper's content is correct.
- The fill pack is **task instructions**, not auto-filling. It does not call any external LLM API.

## [v0.2.0-alpha] — 2026-06-15

### Added

- **One-command runner** — `skills/paper-three-pass-reader/scripts/run_paper_reading.py`.
  - Turns any paper-shaped input (title, abstract, OCR transcript, repo URL, etc.) into a standard run directory + draft `paper_reading.json` + (optional) rendered page + (optional) published GitHub Page.
  - Stdlib only. No external LLM API.
  - Built-in resolver hints for a handful of well-known papers (Attention, BERT, How to Read a Paper, this repo) — for smoke testing and for the most common canonical inputs. No network search.
  - Strict reading-mode discipline: `paper_excerpt` always forces `abstract_only`; `paper_screenshot` always forces `screenshot_only`; the user's `--reading-mode` override wins over both the input-kind-forced mode and the hint default.
  - Unknown inputs become `ambiguous_clue` drafts with `needs_confirmation = true` and `confidence = low` — never silently guessed.
  - Drafts are explicitly marked with `[DRAFT]` placeholders so the operator knows what to fill in.
  - New docs: `skills/paper-three-pass-reader/docs/RUNNER.md`.

### Changed (validation)

- `scripts/validate.sh` gained an 8th step ("v0.2 runner") with 6 new smoke checks:
  1. Runner script exists and is executable.
  2. `runner --help` exits 0.
  3. title-only smoke run produces `work/paper_reading.json`.
  4. abstract_only smoke page contains `abstract_only`.
  5. screenshot_only smoke page contains `screenshot_only`.
  6. sample render still passes.
- Total: **74 PASS / 0 FAIL**.

### Changed (docs)

- `README.md` / `README.zh-CN.md`: added a "One-command runner" section and a v0.2.0-alpha row in the version history.
- `CHANGELOG.md`: new v0.2.0-alpha section.
- New `docs/RELEASE_NOTES_v0.2.0-alpha.md`.
- New `docs/PHASE_P3PR_V0_2_RUNNER_1_REPORT.md`.

### Smoke runs

The runner was smoke-tested with three local runs under `runs/runner-smoke-20260615/`:

- `runner-title-attention` (input kind: `paper_title` → `reading_mode = full_text`)
- `runner-abstract-keshav` (input kind: `paper_excerpt` → `reading_mode = abstract_only`)
- `runner-screenshot-keshav` (input kind: `paper_screenshot` → `reading_mode = screenshot_only`)

`runner-title-attention` was also published to https://conanxin.github.io/paper-reading-pages/runner-title-attention/ as part of validation.

### No changes to

- The three-pass reading design.
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape.
- The `v0.1.0-alpha` / `v0.1.1-alpha` / `v0.1.2-alpha` tags or releases (kept untouched).

## [v0.1.2-alpha] — 2026-06-15

### Fixed

- **`publish_output_to_github.sh` in multi-page index mode.** The cleanup step that runs when both `--site-path` and `--page-title` are passed previously used a `find … -exec rm` pattern that wiped **all** non-infrastructure root entries — including sibling per-page subdirectories. After this fix, the cleanup only removes known-stale files left over from prior single-page deploys (`README.md`, `data/`, `reports/`, `index.html.bak`, `README.zh-CN.md`). Other published-page subdirectories are preserved across re-publishes.

### Why a new release, not a tag rewrite

- `v0.1.1-alpha` was already published (annotated tag `f30f21b` → commit `00ba84f`). The fix commit (`ffa3fd4`) landed on `main` after that release.
- This project treats published tags as immutable: no force-move, no force-push, no history rewrite.
- The fix is therefore released as `v0.1.2-alpha` (annotated tag → current `main` HEAD). `v0.1.1-alpha` remains exactly where it was.

### No changes to

- The three-pass reading design.
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape.
- The `v0.1.0-alpha` tag or release.
- The `v0.1.1-alpha` tag or release (kept untouched).

### Verified live after release

- `https://conanxin.github.io/paper-reading-pages/` — root index, HTTP 200, 1044 bytes.
- `https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/` — slug page, HTTP 200, 44 439 bytes.
- `https://conanxin.github.io/paper-reading-pages/published_pages.json` — manifest, HTTP 200, 237 bytes.

### Validation

`scripts/validate.sh` still PASSes 68 / 0 (no change to validation suite for v0.1.2).

## [v0.1.1-alpha] — 2026-06-15

### Changed (hardening)

- **Renderer is now defensively normalised.** `render_page.py` accepts `claims_evidence_map`, `figures_tables`, `glossary`, and `final_checklist` entries that are plain strings, missing fields, or have invalid enum values. All are coerced into safe dicts with sensible defaults; invalid evidence labels are downgraded to `[Uncertain]`; invalid confidence values become `low`. The page never crashes on a malformed entry.
- **`figures_tables` no longer crashes on string entries.** Strings become `{kind: "note", evidence_label: "[Uncertain]", explanation: <original>}`. Empty titles get a placeholder.
- **`claims_evidence_map` accepts strings as claims.** Each string becomes a single-row claim with `confidence: low`, `needs_verification: true`, `evidence_label: [Uncertain]`.
- **`final_checklist` accepts strings as questions.** Each string becomes `{question: <string>, answerable: true}`.
- **`pass1.decision` is validated** against the four legal values; anything else falls back to `CONTINUE_FULL`.
- **`paper_metadata.reading_mode` and `intake_quality.reading_mode` are validated** against the four legal modes; anything else falls back to `full_text`.
- **`data/` mirrors now include `glossary.json` and `final_checklist.json`** in addition to the previous seven files.
- **`render_page.py` report generators** (`pass2_figures_tables.md`, `pass2_claims_evidence_map.md`) no longer crash on string entries — they coerce on the fly.

### Added (publish script)

- **`publish_output_to_github.sh` supports `--site-path` and `--page-title`** for multi-page publishing. In multi-page mode the output dir is copied into `<branch>/<site-path>/` and other published pages are preserved.
- **Root `index.html` regenerated** from a `published_pages.json` manifest when `--site-path` + `--page-title` are passed. Existing entries are upserted by slug; the manifest is sorted by `published_at`.
- **Root branch cleanup in index mode** automatically removes stale `data/`, `reports/`, top-level `README.md`, etc. (anything not in the allowed infrastructure set: `.nojekyll`, `assets/`, `index.html`, `published_pages.json`, per-page subdirs).
- **`--check` mode** now also reports that `--site-path` and `--page-title` are supported.
- **URL echo** is now computed correctly: `https://<owner>.github.io/<repo>/<site-path>/` (was previously a `sed` mess that produced broken URLs).

### Changed (validation)

- **`scripts/validate.sh` gained a 7th step** ("v0.1.1 hardening") with four new smoke checks:
  1. `render_page.py` handles `figures_tables` string entries without crashing.
  2. Publish-script help advertises `--site-path`.
  3. Publish-script help advertises `--page-title`.
  4. Publish-script `--check` exits 0.
  5. The Attention run re-renders cleanly.
- Existing 6 steps are unchanged. Total: 68 PASS / 0 FAIL.

### Changed (docs)

- `README.md` / `README.zh-CN.md`: added v0.1.1 to the version footer, added a short "Multi-page publishing" section.
- `skills/paper-three-pass-reader/docs/GITHUB_PAGES_PUBLISHING.md`: added "Multi-page mode" with `--site-path` / `--page-title` examples.
- `skills/paper-three-pass-reader/docs/USAGE.md`: added slug-publish example.
- `docs/REALPAPER_RUNS.md`: bumped `LOCAL_OUTPUT_PATH` and `GITHUB_PAGES` to reflect the slug URL.
- New `docs/RELEASE_NOTES_v0.1.1-alpha.md`.
- New `docs/PHASE_P3PR_0_1_1_REALPAPER_HARDENING_REPORT.md`.

### No changes to

- The three-pass reading design.
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape (additive only — the new fields are `glossary.json` and `final_checklist.json` mirrors).
- The `v0.1.0-alpha` tag and release.

## [v0.1.0-alpha] — 2026-06-15

### Added

- **Stage 0 — Paper Intake and Resolution.** Normalises any of: complete paper (PDF / text / LaTeX / HTML), paper URL (arXiv, DOI, OpenReview, ACM/IEEE/Springer/Nature/ScienceDirect, PubMed/bioRxiv/medRxiv), paper identifier (arXiv ID, DOI), paper title, paper metadata (title + author + year + venue), paper excerpt (abstract / intro / conclusion / BibTeX / citation), paper image / screenshot (title page / abstract / figure / table / slide / poster / photo), paper topic clue, GitHub repo, project page, and ambiguous social-media clue into a canonical paper record.
- **Reading modes.** Every run is explicitly tagged `full_text`, `partial_text`, `abstract_only`, or `screenshot_only` — the skill never pretends to have read more than it has.
- **Stage 1 — First Pass with Five Cs.** Category, Context, Correctness, Contributions, Clarity, plus an explicit *continue-or-stop* decision.
- **Stage 2 — Second Pass.** Main ideas, figures & tables, key references, and the **Claims → Evidence map**: every load-bearing claim paired with the figure/table/section that grounds it.
- **Stage 3 — Third Pass.** Method reconstruction, critical review, and a concrete **reproduction plan** an engineer could actually follow.
- **Interactive HTML reading page.** Hero summary, paper metadata, intake status, 1/3/10-sentence summaries, paper map, Five Cs dashboard, Pass 1/2/3 tabs, Claims-Evidence map (filterable), Figures & Tables, Glossary, Method Reconstruction, Limitations, Related Work, Reproduction Plan, Open Questions, and a "Do I understand this paper?" checklist. Tabs, accordions, claim filter, confidence labels, reading-mode badge, evidence labels, progress timeline, glossary chips. **Local-only, no backend, no external assets.**
- **Evidence discipline.** Every interpretive statement carries one of `[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`.
- **Three scripts.**
  - `render_page.py` — JSON → interactive HTML page (stdlib only).
  - `create_output_skeleton.py` — generate empty `paper-reading-output/` skeleton for a new paper.
  - `publish_output_to_github.sh` — push the page to a `gh-pages` branch of an existing GitHub repo; refuses to silently create a new repo.
- **Validation.** `scripts/validate.sh` runs a smoke check: file presence, JSON validity, sample render, page-section presence.
- **Sample data.** `examples/sample_paper_reading.json` and `examples/sample_intake_quality.json` built from S. Keshav's *How to Read a Paper* (2007) — works offline, no network fetch.
- **Docs.** `README.md` (EN), `README.zh-CN.md`, `LICENSE` (MIT), `CHANGELOG.md`, `USAGE.md`, `OUTPUT_SCHEMA.md`, `GITHUB_PAGES_PUBLISHING.md`, `DESIGN_RATIONALE.md`.

### Notes

- This is an **alpha**. Inputs are normalised but PDF/HTML parsing is the caller's responsibility. The skill provides the workflow, the page, and the evidence discipline — not the text extraction pipeline.
- The Keshav sample is meta by design (we use the reading-method paper as the worked example of reading it).
- Backwards-compatibility: this is the first tagged release; no migration needed.
