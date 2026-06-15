# Release Notes — paper-three-pass-reader v0.2.6-alpha

**Date:** 2026-06-15
**Tag:** v0.2.6-alpha
**Previous:** v0.2.5-alpha

## What changed

v0.2.6 is a **resolver-hints unification** release. The `p3pr` CLI and the runner no longer carry their own private `HINTS` / `RESOLVER_HINTS` dicts. All paper / repo / arXiv hints now live in one JSON file (`data/resolver_hints.json`), are loaded by one helper module (`scripts/resolver_hints.py`), and are exposed via a small CLI (`scripts/resolve_paper_hint.py`).

The CLI can now:

- Auto-resolve canonical title / arXiv id / paper URL / default slug from a recognizable input.
- Distinguish `matched` (high confidence) from `ambiguous` (low confidence) from `not_found`.
- Show resolver diagnostics in the run summary.
- Auto-derive the slug prefix (`arxiv-` vs `screenshot-` vs `title-` vs `repo-` vs `abstract-`) from the resolver's match type.
- Stay calm on unknown input — `P3PR_RESOLVER_STATUS: not_found` is a soft signal, not a failure.

The runner is fully backwards compatible. `run_paper_reading.RESOLVER_HINTS` is still there (auto-built from the shared JSON) and any historical code path that imports it works unchanged.

## What's in the box

- `skills/paper-three-pass-reader/data/resolver_hints.json` — single source of truth. 5 anchor papers + 3 repo hints.
- `skills/paper-three-pass-reader/scripts/resolver_hints.py` — stdlib-only helper module. Public API: `load_hints`, `resolve_title`, `resolve_arxiv`, `resolve_repo`, `resolve_any`, `paper_to_runner_overrides`.
- `skills/paper-three-pass-reader/scripts/resolve_paper_hint.py` — CLI for humans and tests.
- `skills/paper-three-pass-reader/docs/RESOLVER_HINTS.md` — full design + API doc.
- Updated `p3pr.py` and `run_paper_reading.py` to use the shared resolver.
- Updated `scripts/validate.sh` (179/0 PASS as of v0.2.6).

## How to use

### Quick test

```bash
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "Attention Is All You Need"
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py repo https://github.com/google-research/bert
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py arxiv 2503.08102
```

### CLI dry-run now shows resolver

```
P3PR_STATUS: DRY_RUN
P3PR_INPUT_KIND: paper_identifier
P3PR_READING_MODE: full_text
P3PR_RUN_DIR: runs/p3pr-cli-20260615/arxiv-2503.08102
P3PR_RESOLVER_STATUS: matched
P3PR_RESOLVER_MATCH_TYPE: arxiv
P3PR_CANONICAL_TITLE: AI-native Memory 2.0: Second Me
P3PR_ARXIV_ID: 2503.08102
P3PR_DEFAULT_SLUG: arxiv-2503.08102
```

### Auto-derivation: title → arXiv

```bash
./p3pr title "Attention Is All You Need" --zh --full --publish --dry-run
# P3PR_RESOLVER_MATCH_TYPE: title
# P3PR_ARXIV_ID: 1706.03762
# P3PR_DEFAULT_SLUG: arxiv-1706.03762
```

### Screenshot transcript with known paper in it

```bash
./p3pr screenshot path/to/transcript.md --zh --screenshot-only --no-publish
# Resolver auto-finds the paper inside the transcript and fills title/arxiv_id.
# reading_mode stays screenshot_only — the CLI does NOT pretend full_text.
```

## Migration notes

- v0.2.5 CLI commands are unchanged. Only the dry-run summary lines and internal hint data have moved.
- If you import `run_paper_reading.RESOLVER_HINTS` directly, you get the same dict shape as before (keyed by lowercased canonical title, alias, or repo URL). 26 keys ship by default.
- Adding a new paper: edit `data/resolver_hints.json`. Both `p3pr` and the runner pick it up on the next call.

## Known limitations

- The resolver is curated, not learned. It cannot tell you about a paper it has never seen.
- The shared resolver is structural — it does not validate that the paper actually exists or that the arXiv id is real. It trusts the JSON.
- No fuzzy embedding search. If you type `"attn is all you need"` you will not match (exact substring only). Add an alias if you need a fuzzy match.

## What's next

Potential v0.2.7 / v0.2.8 ideas:

- Optional fuzzy matching for typos (Levenshtein over aliases).
- Optional local SQLite cache of past reads.
- Per-user resolver hints override.
- GitHub Pages render that embeds resolver diagnostics as a sidebar.

Nothing is committed yet. This release stands on its own.
