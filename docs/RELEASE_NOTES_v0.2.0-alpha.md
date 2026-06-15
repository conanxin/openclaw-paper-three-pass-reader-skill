# Release Notes — paper-three-pass-reader v0.2.0-alpha

**Date:** 2026-06-15
**License:** MIT
**Tag:** `v0.2.0-alpha`
**Repo:** https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
**Previous:** [v0.1.2-alpha](https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.1.2-alpha) (immutable)

---

## What this release is

A workflow-scaffold release: the new `run_paper_reading.py` script turns a paper-shaped input into a standard run directory + draft `paper_reading.json` + (optional) rendered HTML page + (optional) published GitHub Page. This is the v0.2 first step — a repeatable command, not a paper-reading agent.

The runner does **not** read the paper for you. It produces a DRAFT with explicit `[DRAFT]` placeholders that the operator (human or agent) fills in. It enforces intake discipline and reading-mode honesty, and it preserves the workflow that v0.1.x already supports.

---

## Highlights

### New script — `run_paper_reading.py`

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug runner-title-attention \
  --output-root runs/runner-smoke-20260615 \
  --render --publish \
  --repo conanxin/paper-reading-pages \
  --page-title "Runner Smoke: Attention Is All You Need"
```

Supported arguments:

- `--input <string>` or `--input-file <path>` — the raw input.
- `--input-kind <kind>` — required, one of the 11 input kinds.
- `--slug <slug>` — required, `[A-Za-z0-9._-]+`.
- `--output-root <path>` — required.
- `--title`, `--authors`, `--year`, `--arxiv-id`, `--paper-url` — overrides.
- `--reading-mode <mode>` — override.
- `--render` — render the page after writing the draft.
- `--publish` — push to GitHub Pages (requires `--render` and `--repo`).
- `--repo`, `--branch`, `--site-path`, `--page-title` — publish options.

### Standard run layout

```
<output-root>/<slug>/
├── input/
│   └── input.md               # captured raw input (audit trail)
├── source/                    # empty — operator drops PDFs here
├── extracted/                 # empty — operator drops pdftotext output here
├── work/
│   └── paper_reading.json     # the DRAFT (operator fills in [DRAFT] placeholders)
└── paper-reading-output/       # populated only if --render
    ├── index.html
    ├── assets/{style.css, app.js}
    ├── data/  (8 JSON mirrors)
    └── reports/ (12 markdown files)
```

### Reading-mode discipline

| `--input-kind` | Forced `reading_mode` |
|---|---|
| `paper_excerpt` | `abstract_only` |
| `paper_screenshot` | `screenshot_only` |
| other kinds | derived from hint or `partial_text` |

For partial modes:

- Pass 2 / Pass 3 are explicitly marked `[DRAFT — unavailable until body is available]`.
- Claims are labelled `[Needs verification]` until the operator upgrades to `full_text`.
- `intake_quality.missing_fields` lists `full_body_text`, `full_references`, `full_figures`, `full_tables`.

### Built-in resolver hints

A small, hand-curated hint table for smoke testing and for known canonical papers. **No network search.**

| Input | Hint |
|---|---|
| `Attention Is All You Need` | arXiv 1706.03762 |
| `How to Read a Paper` | S. Keshav, SIGCOMM CCR 2007 |
| `BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding` | arXiv 1810.04805 |
| `https://github.com/google-research/bert` | → BERT paper |
| `https://github.com/conanxin/openclaw-paper-three-pass-reader-skill` | → this repo |

Unknown inputs become `ambiguous_clue` drafts with `needs_confirmation = true` and `confidence = low`.

### Validation — 74 PASS / 0 FAIL

`scripts/validate.sh` grew a new 8th step ("v0.2 runner") with 6 new smoke checks:

1. Runner script exists and is executable.
2. `runner --help` exits 0.
3. title-only smoke run produces `work/paper_reading.json`.
4. abstract_only smoke page contains `abstract_only`.
5. screenshot_only smoke page contains `screenshot_only`.
6. sample render still passes.

---

## Smoke runs (this release)

The runner was smoke-tested with three local runs under `runs/runner-smoke-20260615/`:

| Slug | Input kind | Resolved `reading_mode` | Page size |
|---|---|---|---|
| `runner-title-attention` | `paper_title` | `full_text` | 12 497 bytes |
| `runner-abstract-keshav` | `paper_excerpt` | `abstract_only` | 12 569 bytes |
| `runner-screenshot-keshav` | `paper_screenshot` | `screenshot_only` | 12 562 bytes |

`runner-title-attention` was also published to https://conanxin.github.io/paper-reading-pages/runner-title-attention/ as part of validation; verified HTTP 200 at release time.

---

## Install / upgrade

```bash
git clone https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
cd openclaw-paper-three-pass-reader-skill
git checkout v0.2.0-alpha

bash scripts/validate.sh        # expect: 74 PASS / 0 FAIL

# Try the runner:
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug my-first-run \
  --output-root runs \
  --render
```

---

## Compatibility

- **No schema-breaking changes.** The draft JSON conforms to the same `paper_reading.schema.json`.
- **No page-template breaking changes.** Drafts render through the same `render_page.py`.
- **No changes to the three-pass reading workflow.**
- **No changes to the publish script** beyond what v0.1.2 already shipped.
- **`v0.1.0-alpha`, `v0.1.1-alpha`, `v0.1.2-alpha` remain immutable** — not moved, not rewritten.

---

## Known limitations (carried forward)

- The runner does **not** read the paper. The draft is a scaffold; the operator fills it in.
- The runner does **not** search the web. Inputs not in the hint table become `ambiguous_clue` drafts.
- The runner does **not** include an LLM-driven filler. (Planned for v0.3.)
- The runner writes to `paper-reading-output/` only if `--render` is passed. Without `--render`, only `work/paper_reading.json` exists.

---

## Next steps

- v0.2.x — bug fixes and ergonomics from early use of the runner.
- v0.3 — LLM-driven filler that takes the available text + the input kind and emits the JSON automatically.
- v0.4 — pipeline that combines runner + LLM filler + re-render + re-publish into one agentic command.

---

## Credits

Same as v0.1.x. Built by Conan Xin. Inspired by S. Keshav's *How to Read a Paper* (SIGCOMM CCR, 2007).
