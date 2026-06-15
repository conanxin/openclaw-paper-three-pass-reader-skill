# Phase Report — v0.2.7 Resolver Round-2 Release

## STATUS

PASS

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.2.6-alpha (tag at `0fdeedb`)

## TARGET_VERSION

v0.2.7-alpha (annotated tag, new release)

## DECISION

Release the v0.2.6 round-2 hardening as **v0.2.7-alpha**, not as a move
of v0.2.6-alpha. v0.2.6-alpha is preserved unchanged at `0fdeedb`.

## WHY_NOT_MOVE_V0_2_6

The repository treats published tags as immutable. v0.2.6-alpha is
already published (tag → `0fdeedb`, GitHub release at
`https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.6-alpha`).
Re-pointing the tag would:

- Break any downstream consumer pinning `v0.2.6-alpha`.
- Rewrite release history.
- Contradict the project policy "published-tag-immutability" that
  v0.2.0-alpha onwards has followed.

The clean alternative is a new minor version `v0.2.7-alpha` that
carries the round-2 work. v0.2.6-alpha stays where it is.

## ROUND2_CONTENT

| area | what landed |
| --- | --- |
| `source_resolution` | flat list → structured top-level dict with 14 keys |
| CLI overlay | `p3pr` writes `work/resolver_source.json`; runner reads it via `--resolver-source` |
| runner | `_resolve_hint` returns `(hint, key, resolver_result)`; helper call is wrapped in `try/except` |
| degradation | `resolver_status=error` + `degraded=ambiguous_clue` + warning + rc=0 |
| validation | step 14 with 14 new checks (hostile / overlay / structured-trail) |

Round-2 code landed in commit `e7a7f1e`. This release adds the
documentation pass, version-table updates, release notes, and this
report on top of that commit.

## STRUCTURED_SOURCE_RESOLUTION

Top-level `source_resolution` block on every draft. Keys:

| key | type | meaning |
| --- | --- | --- |
| `steps` | list | ordered resolver attempts |
| `hint_input` | str | the original user hint text |
| `resolver_source` | str | which call produced the final match |
| `resolver_helper` | str | module path of the helper that ran |
| `resolver_status` | str | `matched \| weak \| ambiguous_clue \| error` |
| `resolver_match_type` | str | `title \| alias \| repo \| arxiv \| abstract \| overlay` |
| `confidence` | float | 0.0–1.0 |
| `matched_paper_id` | str | canonical paper id from the shared JSON |
| `matched_canonical_title` | str | canonical title |
| `matched_arxiv_id` | str | arXiv id, if known |
| `matched_alias` | str | the alias that matched, if any |
| `matched_repo` | str | the repo url that matched, if any |
| `candidates` | list | alternative candidates considered |
| `source_resolution_step` | str | which step produced the final result |
| `degraded` | str | `ambiguous_clue` on resolver error |
| `fallback_legacy` | bool | true if back-compat dict was used |

The legacy flat `intake_quality.source_resolution` list is preserved
for back-compat with v0.2.5 smokes.

## DEGRADATION_BEHAVIOR

The runner's resolver helper call is wrapped in `try/except`. On any
exception the runner:

1. Records `resolver_status=error` in `source_resolution`.
2. Sets `degraded=ambiguous_clue` in `source_resolution`.
3. Appends a warning to `intake_quality.warnings`.
4. Continues with rc=0 and still writes `paper_reading.json`.

A hostile-resolver test in `scripts/validate.sh` step 14 forces the
helper to raise on every call and asserts all four behaviours. The
test passes.

## VALIDATION

```
$ bash scripts/validate.sh
...
=================================================
 PASS: 195    FAIL: 0
=================================================
STATUS: PASS
```

Breakdown of the 195 checks:

- 167 from the v0.2.5 baseline.
- 28 from `step 13` (round-1 resolver unit checks).
- 14 from `step 14` (round-2 hostile / overlay / structured-trail
  checks).

## FILES_CREATED

- `docs/RELEASE_NOTES_v0.2.7-alpha.md`
- `docs/PHASE_P3PR_V0_2_7_RESOLVER_ROUND2_RELEASE_REPORT.md` (this file)

## FILES_MODIFIED

- `CHANGELOG.md` — new v0.2.7-alpha entry at the top.
- `README.md` — version table updated, v0.2.5-alpha → immutable,
  v0.2.6-alpha row added, v0.2.7-alpha set as `current`. Footer version
  bumped to **v0.2.7-alpha**.
- `README.zh-CN.md` — version table filled in for v0.2.2 through
  v0.2.7; v0.2.7 set as `当前`. Footer version bumped to
  **v0.2.7-alpha**.
- `skills/paper-three-pass-reader/docs/RESOLVER_HINTS.md` — new
  "Structured `source_resolution` block (v0.2.7)" and "Resolver
  degradation behaviour (v0.2.7)" sections.
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — two new
  Q&A entries on the structured trail and the degradation behaviour,
  with deep links into `RESOLVER_HINTS.md`.

## COMMIT

Single commit on `main`:

```
Release v0.2.7-alpha resolver round-2 hardening
```

Files staged (per task's per-file `git add` rule):

```
git add CHANGELOG.md
git add README.md
git add README.zh-CN.md
git add skills/paper-three-pass-reader/docs/RESOLVER_HINTS.md
git add skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md
git add docs/RELEASE_NOTES_v0.2.7-alpha.md
git add docs/PHASE_P3PR_V0_2_7_RESOLVER_ROUND2_RELEASE_REPORT.md
```

The `runs/` untracked directories (smoke outputs) are intentionally
**not** staged. They are not part of this release.

## PUSH

`git push origin main` after the commit lands. The new commit sits
on top of round-2 commit `e7a7f1e`. No force-push, no rebase.

## TAG

Annotated tag:

```
git tag -a v0.2.7-alpha -m "v0.2.7-alpha"
git push origin v0.2.7-alpha
```

The tag is created **on top of the documentation/release commit**, not
on `0fdeedb` and not on `e7a7f1e`. The new tag points at the release
commit (the one that includes this report and the release notes).

## RELEASE

GitHub release created with:

```
gh release create v0.2.7-alpha \
  --title "paper-three-pass-reader v0.2.7-alpha" \
  --notes-file docs/RELEASE_NOTES_v0.2.7-alpha.md
```

URL:

```
https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.7-alpha
```

v0.2.6-alpha is **not** modified, **not** deleted, and **not** moved.
The two tags coexist:

- `v0.2.6-alpha` → `0fdeedb`
- `v0.2.7-alpha` → release commit on top of `e7a7f1e`

## LIMITATIONS

- The shared resolver is local and hint-based. It is not a network
  search engine and not a paper database. Papers not listed in
  `data/resolver_hints.json` still resolve to `ambiguous_clue`.
- The hostile-resolver degradation is best-effort: it covers a single
  resolver helper. A future round should also degrade
  `paper_metadata.json` and the citation parser.
- CLI overlay (`work/resolver_source.json`) is only honoured when the
  runner is invoked via the normal CLI path. Standalone
  `run_paper_reading.py` runs without the overlay and rely on the
  runner's auto-detect.
- The legacy flat `intake_quality.source_resolution` list is
  preserved for back-compat but is no longer the canonical trail.
  Future agents should read the structured top-level
  `source_resolution` block.

## NEXT_USER_ACTION

None required for v0.2.7. Optional follow-ups:

- Add more anchor papers to `data/resolver_hints.json`.
- Add a `validate_resolver_hints` step that fails CI if the JSON has
  duplicate `id` or `alias` fields.
- Consider a v0.2.8 release that brings the zh-CN quality gate, the
  fill-pack, and the audit onto the structured `source_resolution`
  block (they currently read the legacy flat list).
