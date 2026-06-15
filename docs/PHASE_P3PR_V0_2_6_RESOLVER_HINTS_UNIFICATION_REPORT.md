# Phase Report — v0.2.6 Resolver Hints Unification

| Field | Value |
|---|---|
| **STATUS** | PASS |
| **PROJECT_DIR** | `/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill` |
| **BASE_VERSION** | v0.2.5-alpha |
| **TARGET_VERSION** | v0.2.6-alpha |

---

## PROBLEM

Resolver hints for paper / repo / arXiv resolution were duplicated in two places:

1. `p3pr.py` carried a private `HINTS` dict (used for dry-run resolution and slug derivation).
2. `run_paper_reading.py` carried a private `RESOLVER_HINTS` dict (used for canonical metadata when building a draft).

Adding a new paper required editing two files and remembering to keep them in sync. The two resolvers used slightly different matching rules, and neither could cleanly tell you whether a match was high confidence, low confidence, ambiguous, or not found.

## CLI_SUMMARY

v0.2.6 introduces one shared resolver. All hint data lives in `skills/paper-three-pass-reader/data/resolver_hints.json`. The resolver is a small stdlib-only module (`scripts/resolver_hints.py`) and a tiny CLI (`scripts/resolve_paper_hint.py`). Both `p3pr.py` and `run_paper_reading.py` delegate to it.

## SUPPORTED_COMMANDS

`p3pr` itself is unchanged from v0.2.5 — same six subcommands. New behavior:

- All subcommands now show resolver diagnostics in the run summary.
- Title / repo / arXiv subcommands auto-derive canonical title, arXiv id, paper URL, and slug from the shared resolver when a match is found.
- Abstract / screenshot subcommands run the resolver against the first 400 chars of the input file. If a known paper appears in the transcript, the CLI auto-derives canonical metadata without pretending the input is a full paper.
- Unknown input never fails the CLI. It logs `P3PR_RESOLVER_STATUS: not_found` and continues with the weak-mode default.

New standalone resolver CLI:

- `python3 scripts/resolve_paper_hint.py {title|arxiv|repo|any} <value>`

## DEFAULTS

Same as v0.2.5:

- `language = zh-CN`
- `fill_pack = true`
- `audit = true`
- `quality_gate = true` (only when `language == zh-CN`)
- `render = true`
- `publish = false`
- `repo = conanxin/paper-reading-pages`
- `branch = gh-pages`

## BOUNDARIES

- Resolver is **curated, not learned**. No network search. No LLM.
- Resolver is **structural**. It does not validate that a paper actually exists. It trusts the JSON.
- Resolver is **not** a fuzzy embedder. Exact substring only. Add an alias for fuzzy match.
- Resolver is **not** auto-expanded. To add a paper, edit the JSON.

## SMOKE_RUNS

Re-ran all v0.2.5 smoke runs against the new resolver:

- `./p3pr arxiv 2503.08102 --zh --full --publish --dry-run` — resolver_status=matched, match_type=arxiv, canonical_title="AI-native Memory 2.0: Second Me", arxiv_id=2503.08102.
- `./p3pr title "Attention Is All You Need" --zh --full --publish --dry-run` — resolver_status=matched, match_type=title, arxiv_id=1706.03762, slug=arxiv-1706.03762.
- `./p3pr repo https://github.com/google-research/bert --zh --full --publish --dry-run` — resolver_status=matched, match_type=repo, arxiv_id=1810.04805.
- `./p3pr title "completely unknown paper"` — resolver_status=not_found, no failure, weak mode preserved.
- `./p3pr screenshot runs/p3pr-cli-smoke-20260615/input/screenshot.md --zh --screenshot-only --no-publish` — resolver auto-detected Second Me from the transcript and derived arxiv_id=2503.08102. reading_mode remained screenshot_only.
- `./p3pr abstract runs/p3pr-cli-smoke-20260615/input/abstract.md --zh --abstract-only --no-publish` — resolver did not find a known paper in this text, but the run completed without failure.

## VALIDATION

`bash scripts/validate.sh` → **PASS: 179, FAIL: 0**

New step 13 (28 checks):

- 13a: resolver_hints.json exists + parses + has 5 anchor papers.
- 13b: resolver_hints.py loads via stdlib import.
- 13c: resolve_paper_hint.py CLI works for title / repo / arxiv / any.
- 13d: unknown input returns not_found cleanly.
- 13e: aliases work (`transformers` → Attention, case-insensitive).
- 13f: p3pr.py no longer has local HINTS dict.
- 13g: p3pr.py imports from resolver_hints.
- 13h: run_paper_reading.py imports from resolver_hints.
- 13i: runner RESOLVER_HINTS back-compat dict has 26 keys.
- 13j: historical keys still resolve correctly.
- 13k: p3pr dry-run shows resolver details.
- 13l: p3pr title dry-run auto-resolves to arXiv 1706.03762.
- 13m: p3pr repo dry-run auto-resolves BERT to arXiv 1810.04805.
- 13n: p3pr screenshot v0.2.6 smoke auto-detected arXiv 2503.08102.

All previous steps (1–12) still pass. No regression.

## FILES_CREATED

- `skills/paper-three-pass-reader/data/resolver_hints.json`
- `skills/paper-three-pass-reader/scripts/resolver_hints.py`
- `skills/paper-three-pass-reader/scripts/resolve_paper_hint.py`
- `skills/paper-three-pass-reader/docs/RESOLVER_HINTS.md`
- `docs/RELEASE_NOTES_v0.2.6-alpha.md`
- `docs/PHASE_P3PR_V0_2_6_RESOLVER_HINTS_UNIFICATION_REPORT.md` (this file)

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/p3pr.py` — local HINTS dict removed; imports + delegates to resolver_hints.py. All subcommands (arxiv / title / abstract / screenshot / repo / pdf) now call the shared resolver and show resolver diagnostics. Slug derivation now prefers the resolver's match type. _print_summary now prints resolver_status / resolver_match_type / canonical_title / arxiv_id / default_slug when present.
- `skills/paper-three-pass-reader/scripts/run_paper_reading.py` — local RESOLVER_HINTS dict replaced with `_build_legacy_resolver_hints()` that reads from `resolver_hints.json`. `_resolve_hint()` now prefers the shared resolver and falls back to the legacy substring matcher.
- `scripts/validate.sh` — added step 13 (28 new checks). 179/0 PASS.
- `CHANGELOG.md` — v0.2.6 entry added.
- `README.md` / `README.zh-CN.md` — version bump and feature pointer.

## COMMIT

Local commit on main: `release v0.2.6 — shared resolver hints unification`.

## PUSH

`git push origin main` — pushed to `conanxin/openclaw-paper-three-pass-reader-skill` @ `main`.

## TAG

Annotated tag `v0.2.6-alpha` created locally and pushed to `origin`.

## RELEASE

`gh release create v0.2.6-alpha --title "paper-three-pass-reader v0.2.6-alpha" --notes-file docs/RELEASE_NOTES_v0.2.6-alpha.md` — release created on GitHub.

URL: `https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.6-alpha`

## LIMITATIONS

- Curated, not learned. To add a paper, edit the JSON.
- No fuzzy matching. Exact substring + alias only. Add aliases for fuzzy.
- No network. The resolver cannot fetch arXiv metadata; the runner does the actual download.
- The shared resolver is structural. It does not score paper reading quality — that is still the job of the fill-pack + audit + zh-CN quality gate pipeline.

## NEXT_USER_ACTION

1. Pull `v0.2.6-alpha` and run `bash scripts/validate.sh` → expect 179/0 PASS.
2. To add a new paper: edit `data/resolver_hints.json` and run the standalone CLI to verify.
3. To debug a hint mismatch: run `python3 scripts/resolve_paper_hint.py title "<your title>"` — JSON output is self-explanatory.
4. Optional: replace the curated hints with a local paper-database cache in a future release. v0.2.6 deliberately keeps it small and reproducible.
