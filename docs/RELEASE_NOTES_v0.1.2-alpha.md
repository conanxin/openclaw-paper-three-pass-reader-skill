# paper-three-pass-reader v0.1.2-alpha

**Date:** 2026-06-15
**License:** MIT
**Tag:** `v0.1.2-alpha` (annotated)
**Repo:** https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
**Previous:** [v0.1.1-alpha](https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.1.1-alpha) (immutable)

---

This release formally includes the publish-script fix that landed on `main` after `v0.1.1-alpha`.

## Why v0.1.2 instead of moving v0.1.1

`v0.1.1-alpha` was already published. The project treats published tags as immutable, so the fix is released as `v0.1.2-alpha` instead of force-moving the old tag.

- `v0.1.1-alpha` annotated tag stays at `00ba84f` ("Harden real-paper rendering and multi-page publishing").
- `v0.1.2-alpha` annotated tag points at the current `main` HEAD (`ffa3fd4`), which includes the publish-script fix.

No force push. No history rewrite. No deletion of old releases.

## Included

- The publish-script fix from `main` (commit `ffa3fd4`).
- Multi-page GitHub Pages publishing remains supported.
- The root index page remains supported and now uses an explicit stale-file cleanup list (`README.md`, `data/`, `reports/`, `index.html.bak`, `README.zh-CN.md`) so other published pages' subdirectories are **never** accidentally removed.
- Slug page publishing remains supported and now preserves sibling pages across re-publishes.
- Validation still PASSes (68 / 0).

## Compatibility

- **No schema-breaking changes.** `paper_reading.schema.json` is unchanged.
- **No page-template breaking changes.** All 19 sections render identically.
- **No changes to the three-pass reading workflow.** Stage 0 → Pass 1 → Pass 2 → Pass 3 → Final Page is untouched.
- **No changes to existing data files.** Both old releases' outputs continue to render correctly when fed through `render_page.py` from this version.

## Verified live after release

| URL | Result |
|---|---|
| `https://conanxin.github.io/paper-reading-pages/` (root index) | HTTP 200, 1044 bytes |
| `https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/` (slug page) | HTTP 200, 44 439 bytes |
| `https://conanxin.github.io/paper-reading-pages/published_pages.json` (manifest) | HTTP 200, 237 bytes |

## How to upgrade

```bash
git clone https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
cd openclaw-paper-three-pass-reader-skill
git checkout v0.1.2-alpha

bash scripts/validate.sh        # expect: 68 PASS / 0 FAIL
```

If you're on v0.1.1-alpha, the only behavioural change is that re-publishing one paper under `--site-path` will no longer delete any other paper's `gh-pages/<slug>/` subdirectory. Everything else is identical.

## Known limitations (unchanged from v0.1.1)

- No PDF parsing in the skill — bring your own.
- No annotation persistence beyond `localStorage`.
- The Attention page is still the only published page on `conanxin/paper-reading-pages`. New pages will exercise the now-safer multi-page upsert path.
- No DOI lookup yet at Stage 0.

## Credits

Same as v0.1.0-alpha and v0.1.1-alpha. Built by Conan Xin. Inspired by S. Keshav's *How to Read a Paper* (SIGCOMM CCR, 2007).
