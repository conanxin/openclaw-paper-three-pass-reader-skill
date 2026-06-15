# PHASE_P3PR_0_1_1_REALPAPER_HARDENING_REPORT.md

| Field | Value |
|---|---|
| **STATUS** | PASS |
| **PROJECT_DIR** | `/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill` |
| **BASE_VERSION** | v0.1.0-alpha |
| **TARGET_VERSION** | v0.1.1-alpha |
| **PHASE** | P3PR-0.1.1-REALPAPER-HARDENING |
| **TRIGGER** | Real-paper run (`P3PR-REALPAPER-1`) exposed renderer fragility + need for multi-page publishing |
| **DATE** | 2026-06-15 |

---

## TL;DR

The skill was hardened in response to the first real-paper run. The renderer now tolerates loose JSON (plain strings, missing fields, invalid enums). The publish script gained a multi-page mode (`--site-path` + `--page-title`) that pushes each paper into its own subdirectory and maintains a small root index. The Attention page was re-rendered and re-published to a slug URL. Validation grew from 63 to 68 checks; all pass. Tag `v0.1.1-alpha` is pushed and the release is created. The `v0.1.0-alpha` tag and release are kept untouched.

---

## FIXES_APPLIED

| # | Symptom | Fix |
|---|---|---|
| 1 | `render_page.py` crashes when `figures_tables` contains a plain string | New `normalize_figure_table()` coerces strings into safe dicts |
| 2 | `render_page.py` crashes on bad `evidence_label` values | New `_safe_label()` downgrades invalid labels to `[Uncertain]` |
| 3 | `render_page.py` crashes on missing `claim`/`figure_table`/`glossary`/`checklist` fields | New `normalize_*()` helpers fill missing fields with safe defaults |
| 4 | `data/` mirrors did not include `glossary.json` / `final_checklist.json` | `write_data_mirrors()` now writes them too |
| 5 | `pass2_figures_tables.md` / `pass2_claims_evidence_map.md` reports crashed on string entries | The two f-string joins now coerce on the fly |
| 6 | `pass1.decision` could contain anything | Now validated against the four legal values |
| 7 | `paper_metadata.reading_mode` / `intake_quality.reading_mode` could contain anything | Now validated against the four legal modes |
| 8 | Publish script had no multi-page mode | New `--site-path` + `--page-title` arguments |
| 9 | Publish script's URL echo was broken (sed mess) | Replaced with bash parameter expansion |
| 10 | Pages repo root held stale `data/`/`reports/` from the legacy single-page deploy | Multi-page index mode now normalises the branch root |
| 11 | No `published_pages.json` manifest existed | Index mode now writes a manifest with one entry per published page |

---

## RENDERER_HARDENING

### New helpers (in `skills/paper-three-pass-reader/scripts/render_page.py`)

| Helper | Purpose |
|---|---|
| `VALID_EVIDENCE_LABELS` | The six legal evidence labels, as a set |
| `VALID_CONFIDENCE` | The three legal confidence values |
| `VALID_DECISION` | The four legal `pass1.decision` values |
| `_safe_label(label)` | Returns `label` if legal, else `[Uncertain]` |
| `_safe_confidence(c)` | Returns `c` if legal, else `"low"` |
| `_safe_decision(d)` | Returns `d` if legal, else `"CONTINUE_FULL"` |
| `normalize_claim(c)` | Coerces a string / scalar / dict into a safe claim dict |
| `normalize_figure_table(f, idx)` | Coerces a string / scalar / dict into a safe figure/table dict |
| `normalize_glossary(g)` | Coerces a string / scalar / dict into a safe glossary dict |
| `normalize_checklist_item(c)` | Coerces a string / scalar / dict into a safe checklist item dict |
| `normalize_reading(data)` | Top-level dispatcher — runs all four normalizers plus mode/decision validation |

### Where `normalize_reading` is called

Inside `main()` in `render_page.py`, **immediately after `load_json`** and **before** any `copy_assets` / `write_data_mirrors` / `write_reports` / `render_index` / `write_readme` call. This ensures all downstream code sees a fully-normalised `data` dict.

### Synthetic stress test (run inside `scripts/validate.sh`)

A synthetic `paper_reading.json` is built containing:

- A `claims_evidence_map` entry that is a plain string.
- A `claims_evidence_map` entry that is a dict with `evidence_label: "[NotALegalLabel]"` and `confidence: "ultra-high"`.
- A `claims_evidence_map` entry that is an integer (12345).
- A `figures_tables` entry that is a plain string.
- A `glossary` entry that is a plain string.
- A `final_checklist` entry that is a plain string.

The renderer must:

- Exit 0.
- Produce an `index.html`.
- Embed at least one `[Uncertain]` label (from the auto-coerced entries).

Result: **PASS**.

### Behaviour summary

| Input shape | Old behaviour | New behaviour |
|---|---|---|
| `figures_tables: ["plain string"]` | crash on `f.get(...)` | rendered as a note-style entry with `[Uncertain]` label |
| `claims_evidence_map: ["plain string"]` | crash on `c.get(...)` | rendered as a low-confidence `[Uncertain]` row |
| `claims_evidence_map: [{"evidence_label": "[NotALegal]"}]` | label printed literally; filter UI failed to match | label coerced to `[Uncertain]`; filter UI works |
| `claims_evidence_map: [{"confidence": "ultra-high"}]` | unknown value rendered literally | coerced to `"low"` |
| `glossary: ["plain string"]` | crash on `g.get(...)` | rendered as `{term: <string>, definition: ""}` |
| `final_checklist: ["plain string"]` | crash on `c.get(...)` | rendered as `{question: <string>, answerable: true}` |
| `pass1.decision: "MAYBE"` | rendered literally | coerced to `"CONTINUE_FULL"` |
| `paper_metadata.reading_mode: "n/a"` | rendered literally | coerced to `"full_text"` |

### Preserved behaviour

- Existing v0.1.0 sample (`sample_paper_reading.json`) re-renders identically (27 962 bytes, all 9 spec sections present).
- Attention run re-renders cleanly (44 439 bytes, all 9 spec sections present, all 6 evidence labels used).

---

## PUBLISH_SCRIPT_HARDENING

### New CLI surface (`skills/paper-three-pass-reader/scripts/publish_output_to_github.sh`)

```
Usage:
  $0 --output DIR --repo OWNER/REPO [--branch NAME] [--message MSG] \
     [--site-path SLUG] [--page-title "Title"]
  $0 --check
```

### Single-page mode (legacy / default)

Behaviour unchanged: replaces the entire `gh-pages` branch contents with the output dir.

### Multi-page mode (when `--site-path` is set)

1. Validates `--site-path` against `[A-Za-z0-9._-]+` — anything else rejected with exit code 6.
2. Copies the output dir into `<branch>/<site-path>/` (preserving sibling page subdirs).
3. Adds a per-page `.nojekyll` so the page's `assets/` is served verbatim.
4. When `--page-title` is also given:
   - Normalises the branch root to `.nojekyll`, `assets/`, `index.html`, `published_pages.json`, and per-page subdirs (removes any stray top-level `data/`, `reports/`, `README.md`, etc.).
   - Upserts the manifest entry for `<site-path>` (does not duplicate).
   - Sorts the manifest by `published_at`.
   - Regenerates the root `index.html` from the manifest (tiny static HTML, no external JS/CSS).

### `--check` mode

Now reports both `--site-path` and `--page-title` support.

### URL echo

Was previously a `sed` chain that produced URLs like `https://conanxin.github.io.paper-reading-pages/...` (missing `.github.io`). Now uses bash parameter expansion to compute `https://<owner>.github.io/<repo>/<site-path>/` correctly.

### Resulting gh-pages layout (after the Attention run)

```
gh-pages/
├── .nojekyll
├── assets/
│   └── index.css
├── index.html                          (1044 bytes — root index)
├── published_pages.json                (237 bytes — manifest)
└── attention-is-all-you-need/
    ├── .nojekyll
    ├── README.md
    ├── index.html                      (44 439 bytes — the reading page)
    ├── assets/{style.css, app.js}
    ├── data/{paper_reading.json, ... 10 mirrors}
    └── reports/{12 markdown files}
```

### Safety properties preserved

- Never silently creates the target repo — exits with the exact `gh repo create` command if missing.
- Never prints tokens / secrets.
- Never force-pushes.
- Never deletes other pages' subdirs in multi-page mode.

---

## PAGES_INDEX

The root `index.html` is a small static page (no external JS/CSS, just a `link` to `assets/index.css`):

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Paper Reading Pages — index</title>
  <link rel="stylesheet" href="assets/index.css" />
</head>
<body>
  <header>
    <h1>Paper Reading Pages</h1>
    <p class="kicker">Published paper reading pages (paper-three-pass-reader)</p>
  </header>
  <main>
    <section>
      <h2>Published pages (1)</h2>
      <ul class="pages">
      <li><a href="/attention-is-all-you-need/">Attention Is All You Need</a> <span class="slug">[attention-is-all-you-need]</span> <span class="time">2026-06-15T02:39:03Z</span></li>
      </ul>
    </section>
    ...
  </main>
</body>
</html>
```

The `published_pages.json` manifest:

```json
{
  "schema_version": "0.1",
  "pages": [
    {
      "slug": "attention-is-all-you-need",
      "title": "Attention Is All You Need",
      "path": "/attention-is-all-you-need/",
      "published_at": "2026-06-15T02:39:03Z"
    }
  ]
}
```

---

## ATTENTION_PAGE_REPUBLISH

The Attention page was re-rendered and re-published under the `attention-is-all-you-need` slug:

| Step | Command | Result |
|---|---|---|
| Re-render | `python3 skills/paper-three-pass-reader/scripts/render_page.py --input runs/attention-is-all-you-need-20260615/work/paper_reading.json --output runs/attention-is-all-you-need-20260615/paper-reading-output` | OK — `index.html` 44 439 bytes |
| Publish (slug mode) | `./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh --output runs/.../paper-reading-output --repo conanxin/paper-reading-pages --branch gh-pages --site-path attention-is-all-you-need --page-title "Attention Is All You Need"` | OK — pushed to `gh-pages` |
| Live check (root) | `curl -I https://conanxin.github.io/paper-reading-pages/` | HTTP 200, 1044 bytes |
| Live check (slug) | `curl -I https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/` | HTTP 200, 44 439 bytes |

---

## VALIDATION

### `scripts/validate.sh` result

```
[1] Required files        — 18/18 ok
[2] JSON parseability     — 3/3 ok
[3] Sample render         — 22/22 ok
[4] Mandatory page sections — 9/9 ok
[5] Interactive bits      — 8/8 ok
[6] SKILL.md substance    — 1/1 ok
[7] v0.1.1 hardening       — 5/5 ok
                              render_page.py handles figures_tables string entry
                              publish script advertises --site-path
                              publish script advertises --page-title
                              publish script --check exits 0
                              Attention run re-renders OK

=================================================
 PASS: 68    FAIL: 0
=================================================
STATUS: PASS
```

(Up from 63 / 0 in v0.1.0-alpha.)

### Page-level smoke checks (Attention re-render)

| Check | Result |
|---|---|
| `index.html` exists | OK |
| `assets/style.css` exists | OK |
| `assets/app.js` exists | OK |
| `data/paper_reading.json` exists | OK |
| `data/glossary.json` exists | OK (new mirror) |
| `data/final_checklist.json` exists | OK (new mirror) |
| Title contains paper title | OK |
| Section "Intake Status" present | OK |
| Section "Five Cs" present | OK |
| Section "Pass 1" present | OK |
| Section "Pass 2" present | OK |
| Section "Pass 3" present | OK |
| Section "Claims" present | OK |
| Section "Evidence" present | OK |
| Section "Final" present | OK |
| Section "Checklist" present | OK |

---

## GITHUB_PAGES_ROOT

- URL: https://conanxin.github.io/paper-reading-pages/
- Verified `HTTP 200, 1044 bytes` at release time
- Title: `Paper Reading Pages — index`
- Lists one entry: `Attention Is All You Need` → `/attention-is-all-you-need/`

---

## GITHUB_PAGES_ATTENTION_URL

- URL: https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/
- Verified `HTTP 200, 44 439 bytes` at release time
- Title: `Attention Is All You Need — Three-Pass Reading`
- Reading mode badge: `full_text`, confidence `high`

---

## COMMIT

```
00ba84f Harden real-paper rendering and multi-page publishing
```

14 files changed, 895 insertions, 98 deletions:

- `skills/paper-three-pass-reader/scripts/render_page.py` (renderer hardening)
- `skills/paper-three-pass-reader/scripts/publish_output_to_github.sh` (multi-page mode)
- `scripts/validate.sh` (4 new checks)
- `CHANGELOG.md` (new v0.1.1-alpha section)
- `README.md` (v0.1.1 footer + multi-page section)
- `README.zh-CN.md` (v0.1.1 footer + multi-page section)
- `skills/paper-three-pass-reader/docs/GITHUB_PAGES_PUBLISHING.md` (multi-page mode section)
- `skills/paper-three-pass-reader/docs/USAGE.md` (split 5a/5b)
- `docs/REALPAPER_RUNS.md` (slug URL + multi-page layout)
- `docs/RELEASE_NOTES_v0.1.1-alpha.md` (new)
- `runs/attention-is-all-you-need-20260615/work/paper_reading.json` (unchanged at JSON level; re-rendered outputs below)
- `runs/attention-is-all-you-need-20260615/paper-reading-output/index.html` (re-rendered)
- `runs/attention-is-all-you-need-20260615/paper-reading-output/data/paper_reading.json` (re-rendered)
- `runs/attention-is-all-you-need-20260615/paper-reading-output/data/claims_evidence_map.json` (re-rendered)
- `runs/attention-is-all-you-need-20260615/paper-reading-output/reports/pass2_claims_evidence_map.md` (re-rendered)

---

## PUSH

```
To https://github.com/conanxin/openclaw-paper-three-pass-reader-skill.git
   670de43..00ba84f  main -> main
```

---

## TAG

- Name: `v0.1.1-alpha`
- Type: annotated
- Message: `v0.1.1-alpha`
- Push status: pushed to `origin`

---

## RELEASE

- URL: https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.1.1-alpha
- Title: `paper-three-pass-reader v0.1.1-alpha`
- Notes source: `docs/RELEASE_NOTES_v0.1.1-alpha.md`
- Marked as Latest
- `v0.1.0-alpha` release retained (untouched)

---

## LIMITATIONS (carried into v0.1.1)

- Renderer hardening is **silent**: bad entries become `[Uncertain]` rows rather than crashing, but the agent/human operating the skill still needs to inspect the page or the data mirrors to find them. A future v0.2 could add a CLI warning when entries are auto-coerced.
- `published_pages.json` has no schema enforcement — it is whatever the publish script writes. A future v0.2 could ship a JSON Schema for it.
- Multi-page mode does **not** render the root `index.html` template through the renderer — it is a hand-built minimal HTML. A future v0.2 could add a real template and a small CSS file.
- The Attention page is still the only published page. Future pages will exercise the multi-page upsert path.
- The `pdftotext`-based text extraction is the only one tested in real-paper runs. `pypdf` / `PyPDF2` fallbacks are untested.
- No DOI lookup yet at Stage 0 (carried over from v0.1.0).

---

## NEXT_USER_ACTION

1. **Visit the live pages:**
   - Root index: https://conanxin.github.io/paper-reading-pages/
   - Attention page: https://conanxin.github.io/paper-reading-pages/attention-is-all-you-need/
2. **Try a second paper** — pick any paper you care about, run the same P3PR-REALPAPER-1 workflow, publish with `--site-path <slug> --page-title "Title"`. The root index will auto-grow to two entries.
3. **Inspect the data mirrors** in `runs/.../paper-reading-output/data/` — note the new `glossary.json` and `final_checklist.json` files alongside the seven from v0.1.0.
4. **Optional: try a deliberately malformed JSON** — e.g. `figures_tables: ["some string"]` — and confirm the page renders instead of crashing. This exercises the v0.1.1 hardening.
5. **Optional: open a v0.1.2 issue** if you find any remaining fragility.

No manual GitHub commands are required — tag, release, Pages push, and Pages root index were all completed in this run.

---

## Final two lines (per spec)

```
HERMES_STATUS: REPORT_WRITTEN
HERMES_REPORT_PATH: /home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill/docs/PHASE_P3PR_0_1_1_REALPAPER_HARDENING_REPORT.md
```
