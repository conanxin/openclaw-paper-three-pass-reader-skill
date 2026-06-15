# PHASE_P3PR_0_1_2_FIX_RELEASE_REPORT.md

| Field | Value |
|---|---|
| **STATUS** | PASS |
| **PROJECT_DIR** | `/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill` |
| **BASE_VERSION** | v0.1.1-alpha (immutable, tag → commit `00ba84f`) |
| **TARGET_VERSION** | v0.1.2-alpha (annotated tag → commit `ffa3fd4`) |
| **DECISION** | Release fix as v0.1.2-alpha; do NOT move v0.1.1-alpha |
| **DATE** | 2026-06-15 |

---

## TL;DR

The publish-script fix that landed on `main` after `v0.1.1-alpha` is now formally released as `v0.1.2-alpha`. The previously published `v0.1.1-alpha` tag is untouched (still points at `00ba84f`). No force push, no history rewrite, no release deletion. Validation remains 68 PASS / 0 FAIL. GitHub Pages root index, slug page, and manifest all return HTTP 200.

---

## WHY_NOT_FORCE_MOVE_V0_1_1

`v0.1.1-alpha` was already a published release with an annotated tag. Force-moving the tag (or force-pushing it) would:

- Invalidate the published GitHub Release that references the old SHA.
- Break any external consumer that pinned the tag.
- Violate the project rule "no force push, no history rewrite" stated in earlier phase reports.

Instead, the fix is released as a new tag `v0.1.2-alpha`. The old tag stays as a stable historical reference.

## MAIN_HEAD

`ffa3fd4a8ddee458690e6ad4b526d76beb43a3de` — "Fix publish script to preserve sibling page directories"

## FIX_COMMIT

`ffa3fd4a8ddee458690e6ad4b526d76beb43a3de` — the publish-script fix described in `docs/PHASE_P3PR_0_1_1_REALPAPER_HARDENING_REPORT.md`'s post-publish corrective step.

Pre-fix: the multi-page index mode cleanup used `find … -exec rm` on root-level entries excluding `.git`, `.nojekyll`, `assets`, `index.html`, `published_pages.json` — which **also excluded nothing else**, so it wiped the `attention-is-all-you-need/` sibling subdirectory on re-publish.

Post-fix: an explicit stale-file list (`README.md`, `data`, `reports`, `index.html.bak`, `README.zh-CN.md`) is the only thing removed. Unknown directories are left alone.

## VALIDATION

```
[1] Required files        — 18/18 ok
[2] JSON parseability     — 3/3 ok
[3] Sample render         — 22/22 ok
[4] Mandatory page sections — 9/9 ok
[5] Interactive bits      — 8/8 ok
[6] SKILL.md substance    — 1/1 ok
[7] v0.1.1 hardening       — 5/5 ok

=================================================
 PASS: 68    FAIL: 0
=================================================
STATUS: PASS
```

No validation-suite changes for v0.1.2-alpha — the fix is a single-file change to `publish_output_to_github.sh` that the existing 68-check suite already exercises (via the `--check` mode path).

## PAGES_ROOT_STATUS

```
$ curl -I https://conanxin.github.io/paper-reading-pages/
HTTP/2 200
content-type: text/html; charset=utf-8
```

Title: `Paper Reading Pages — index`. Size: 1044 bytes.

## PAGES_SLUG_STATUS

```
$ curl -I https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/
HTTP/2 200
content-type: text/html; charset=utf-8
```

Title: `Attention Is All You Need — Three-Pass Reading`. Size: 44 439 bytes. Reading-mode badge: `full_text`, confidence `high`.

## PAGES_MANIFEST_STATUS

```
$ curl -I https://conanxin.github.io/paper-reading-pages/published_pages.json
HTTP/2 200
content-type: application/json
```

Size: 237 bytes. Single entry for `attention-is-all-you-need`.

## FILES_MODIFIED

- `CHANGELOG.md` — new `v0.1.2-alpha` section above `v0.1.1-alpha`.
- `README.md` — version footer bumped to v0.1.2-alpha; new "Version history" table; v0.1.2 note in the multi-page publishing section.
- `README.zh-CN.md` — same as `README.md`, in Chinese.
- `docs/REALPAPER_RUNS.md` — new "v0.1.2-alpha release note" subsection.
- `docs/RELEASE_NOTES_v0.1.2-alpha.md` — new release notes file (used by `gh release create --notes-file`).
- `docs/PHASE_P3PR_0_1_2_FIX_RELEASE_REPORT.md` — this file.

**No code files were modified.** The fix commit `ffa3fd4` already lives on `main`; v0.1.2-alpha just formalises it via a new annotated tag + release.

## COMMIT

```
7687862 Release v0.1.2-alpha with publish-script fix
```

Commit message: `Release v0.1.2-alpha with publish-script fix`.

## PUSH

`git push origin main` after the local commit. No force.

## TAG

- Name: `v0.1.2-alpha`
- Type: annotated
- Tag message: `v0.1.2-alpha`
- Target: `main` HEAD (`ffa3fd4`)
- Push: `git push origin v0.1.2-alpha` (no force)

`v0.1.1-alpha` is **not** touched. Verified via `git tag -l v0.1.1-alpha` → `00ba84f5978e5855b91b6444ea13e4e3747ee35e` (unchanged).

## RELEASE

- URL: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.1.2-alpha
- Title: `paper-three-pass-reader v0.1.2-alpha`
- Notes source: `docs/RELEASE_NOTES_v0.1.2-alpha.md`
- Created via: `gh release create v0.1.2-alpha --title "paper-three-pass-reader v0.1.2-alpha" --notes-file docs/RELEASE_NOTES_v0.1.2-alpha.md`

The previous release `v0.1.1-alpha` remains on the GitHub Releases page, untouched.

## LIMITATIONS

- The publish-script fix is purely a single-file change to `skills/paper-three-pass-reader/scripts/publish_output_to_github.sh`. If a future fix needs to touch the renderer or the schema, it would be a different commit and would still follow the same "release as new tag, never move old tags" rule.
- The root `index.html` is still hand-built inside the publish script (no real template). A future v0.1.3 could template it.
- `published_pages.json` still has no JSON Schema. Optional v0.1.3.
- The Attention page is still the only published page on `conanxin/paper-reading-pages`. Adding a second paper will exercise the now-safer multi-page upsert path.

## NEXT_USER_ACTION

1. Verify the new release: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.1.2-alpha
2. Confirm `v0.1.1-alpha` still points at the original commit (it does — not moved).
3. Try publishing a second paper under a different `--site-path` to exercise the sibling-preservation fix.
4. Optional: open a v0.1.3 issue if the root index needs templating or if `published_pages.json` needs a schema.

No manual GitHub commands are required — tag, release, and Pages deployment were all completed in this run.

---

## Final two lines (per spec)

```
HERMES_STATUS: REPORT_WRITTEN
HERMES_REPORT_PATH: /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/docs/PHASE_P3PR_0_1_2_FIX_RELEASE_REPORT.md
```
