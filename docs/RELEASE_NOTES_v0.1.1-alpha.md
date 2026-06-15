# Release Notes — paper-three-pass-reader v0.1.1-alpha

**Date:** 2026-06-15
**License:** MIT
**Tag:** `v0.1.1-alpha`
**Repo:** https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
**Previous:** [v0.1.0-alpha](https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.1.0-alpha)

---

## What this release is

A small hardening release driven by the first real-paper run (`P3PR-REALPAPER-1` — *Attention Is All You Need*). No new features, no design changes — only fixes for things that the real run exposed as fragile, plus the multi-page publishing mode that the user asked for.

---

## Highlights

### Renderer hardening

`render_page.py` now accepts loose JSON. Specifically:

- **`figures_tables` accepts plain strings.** Each string becomes `{kind: "note", evidence_label: "[Uncertain]", explanation: <string>}`. No more crashes.
- **`claims_evidence_map` accepts plain strings, dicts, or even other scalars.** Each entry is normalised to a safe dict with required fields. Invalid `evidence_label` values (anything not in the six legal labels) are coerced to `[Uncertain]`. Invalid `confidence` values become `low`. Missing fields are filled with safe defaults.
- **`glossary` and `final_checklist` accept plain strings.** Each string becomes `{term|question: <string>, definition|answerable: ...}`.
- **`pass1.decision`** is validated against the four legal values; anything else falls back to `CONTINUE_FULL`.
- **`paper_metadata.reading_mode` / `intake_quality.reading_mode`** are validated against the four legal modes; anything else falls back to `full_text`.
- **`data/` mirrors** now include `glossary.json` and `final_checklist.json` in addition to the previous seven files.

### Publish script: multi-page mode

`publish_output_to_github.sh` gained two optional arguments:

- `--site-path <slug>` — copy the output dir into `<branch>/<slug>/` instead of replacing the whole branch. Other page subdirs are preserved.
- `--page-title "Title"` — when combined with `--site-path`, regenerate the branch root `index.html` from a `published_pages.json` manifest (upsert by slug; sort by `published_at`).

In index mode, the branch root is normalised to hold only `.nojekyll`, `assets/`, `index.html`, `published_pages.json`, and per-page subdirs. Stray top-level `data/`, `reports/`, `README.md`, etc. (left over from a previous single-page deploy) are removed.

`--site-path` is validated against `[A-Za-z0-9._-]+` — anything else (including path separators) is rejected with exit code 6.

The `--check` mode now also reports that `--site-path` and `--page-title` are supported.

The URL echo in the publish script was broken in v0.1.0 (a `sed` chain produced wrong URLs). It now uses bash parameter expansion to compute `https://<owner>.github.io/<repo>/<site-path>/` correctly.

### Validation

`scripts/validate.sh` gained a 7th step ("v0.1.1 hardening") with five new smoke checks:

1. `render_page.py` handles `figures_tables` string entries without crashing.
2. Publish-script help advertises `--site-path`.
3. Publish-script help advertises `--page-title`.
4. Publish-script `--check` exits 0.
5. The Attention run re-renders cleanly.

Total: **68 PASS / 0 FAIL**.

### Docs

- `README.md` / `README.zh-CN.md`: bumped to v0.1.1-alpha, added a "Multi-page publishing" section.
- `skills/paper-three-pass-reader/docs/GITHUB_PAGES_PUBLISHING.md`: added "Multi-page mode (v0.1.1+)" with `--site-path` / `--page-title` examples, layout, URLs, and manifest format.
- `skills/paper-three-pass-reader/docs/USAGE.md`: split the publish section into 5a (single-page) and 5b (multi-page).
- `docs/REALPAPER_RUNS.md`: bumped the P3PR-REALPAPER-1 row to point at the new slug URL; added a "v0.1.1 multi-page layout" section.
- `CHANGELOG.md`: new v0.1.1-alpha section.

### Live

The Attention page is now published under the slug:

- Root index: https://conanxin.github.io/paper-reading-pages/
- Attention page: https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/

Both verified at release time: root `HTTP 200, 1044 bytes`; Attention `HTTP 200, 44 439 bytes`.

---

## Install / upgrade

```bash
git clone https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
cd openclaw-paper-three-pass-reader-skill
git checkout v0.1.1-alpha

bash scripts/validate.sh        # expect: 68 PASS / 0 FAIL
```

If you're upgrading from v0.1.0-alpha and you previously published a page to a Pages repo:

- Re-run `publish_output_to_github.sh` with `--site-path <slug> --page-title "Title"` to migrate from single-page mode to multi-page mode. The script will move your existing content into `<slug>/` and replace the branch root with the new index page.

---

## No changes to

- The three-pass reading design (Stage 0 → Pass 1 → Pass 2 → Pass 3 → Final Page).
- The page layout / 19 sections.
- The `paper_reading.schema.json` shape (additive only — new mirror files).
- The `v0.1.0-alpha` tag or release (kept untouched).
- The skill name, license (MIT), or project structure.

---

## Known limitations (carried over from v0.1.0)

- No PDF parsing in the skill — bring your own (`pdftotext`, an LLM, your own reader).
- No annotation persistence beyond `localStorage` (checklist state only).
- Single-pages repo (`conanxin/paper-reading-pages`) currently holds only one page (Attention). New pages will be added via the same `--site-path` workflow.
- The bundled sample is still S. Keshav's *How to Read a Paper* (intentional).

---

## Next steps

- v0.1.2 — bug fixes from real-world use of multi-page publishing.
- v0.2 — add an optional sixth C (Reproducibility); consider a one-shot LLM-driven `paper_reading.json` filler.
- v0.3 — agent integration: a single command that takes a paper input, runs all three passes with an LLM, and emits the page.

---

## Credits

Same as v0.1.0-alpha. Inspired by S. Keshav's *How to Read a Paper* (SIGCOMM CCR, 2007). Built by Conan Xin.
