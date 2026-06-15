# Release Notes — paper-three-pass-reader v0.1.0-alpha

**Date:** 2026-06-15
**License:** MIT
**Tag:** `v0.1.0-alpha`
**Repo:** https://github.com/conanxin/openclaw-paper-three-pass-reader-skill

---

## What this is

The first public release of `paper-three-pass-reader`, a local-first three-pass paper reading skill for Hermes / OpenClaw agents and humans.

It implements S. Keshav's *How to Read a Paper* (2007) as a reproducible, evidence-disciplined workflow that turns any paper-shaped input into a self-contained interactive HTML page.

---

## Highlights

- **Stage 0 — Paper Intake and Resolution.** Normalises any of: complete paper (PDF / text / LaTeX / HTML), paper URL (arXiv, DOI, OpenReview, ACM/IEEE/Springer/Nature/ScienceDirect, PubMed/bioRxiv/medRxiv), paper identifier (arXiv ID, DOI), paper title, paper metadata, paper excerpt, paper image / screenshot, paper topic clue, GitHub repo, project page, and ambiguous social-media clue into a canonical paper record.
- **Explicit reading modes.** Every run is tagged `full_text`, `partial_text`, `abstract_only`, or `screenshot_only` — the skill never pretends to have read more than it has.
- **Stage 1 — First Pass with Five Cs.** Category, Context, Correctness, Contributions, Clarity, plus an explicit continue-or-stop decision.
- **Stage 2 — Second Pass.** Main ideas, figures & tables, key references, and a Claims → Evidence map.
- **Stage 3 — Third Pass.** Method reconstruction, critical review, and a reproduction plan.
- **Interactive HTML page.** Hero summary, paper metadata, intake status, 1/3/10-sentence summaries, paper map, Five Cs dashboard, Pass 1/2/3 tabs, Claims-Evidence map (filterable), Figures & Tables, Glossary, Method Reconstruction, Limitations, Related Work, Reproduction Plan, Open Questions, "Do I understand this paper?" checklist. Tabs, accordions, claim filter, confidence labels, reading-mode badge, evidence labels, progress timeline, glossary chips. **Local-only, no backend, no external assets.**
- **Evidence discipline.** Six explicit labels: `[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`.
- **Three scripts.** `render_page.py`, `create_output_skeleton.py`, `publish_output_to_github.sh` — all stdlib (Python) or POSIX bash, no extra deps.
- **Sample data.** Built from S. Keshav's *How to Read a Paper* — works offline, no network fetch.
- **Validation.** `scripts/validate.sh` — smoke check: file presence, JSON validity, sample render, page-section presence.

---

## Install / quick start

```bash
git clone https://github.com/conanxin/openclaw-paper-three-pass-reader-skill
cd openclaw-paper-three-pass-reader-skill

# Render the sample
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input skills/paper-three-pass-reader/examples/sample_paper_reading.json \
  --output paper-reading-output

# Open paper-reading-output/index.html

# Validate
bash scripts/validate.sh
```

See `README.md` for the full quick start, `skills/paper-three-pass-reader/docs/USAGE.md` for input-by-input examples, and `skills/paper-three-pass-reader/docs/DESIGN_RATIONALE.md` for the design story.

---

## Known limitations (alpha)

- Sample data uses S. Keshav's *How to Read a Paper* itself — a meta choice. The pipeline works on any paper, but only the Keshav sample is pre-built into the repo.
- Stage 0 is **input-driven** — it does not fetch the paper itself. You provide the paper (or the strong hint) and the skill normalises it.
- The HTML page is **static**. No annotation persistence beyond `localStorage`, no notes sync, no shared state.
- No PDF parsing, OCR, or web scraping is included. Bring your own text or URL.
- `publish_output_to_github.sh` is intentionally minimal — it will not roll back, retry, or reconcile. If a push fails, read the error.

---

## Breaking changes from previous versions

None. This is the first tagged release.

---

## Next steps

- v0.1.1 — bug fixes from early feedback; expand sample data.
- v0.2 — add an optional sixth C (Reproducibility); consider a built-in PDF-to-text shim.
- v0.3 — agent integration: a one-shot command that takes a paper input, runs all three passes with an LLM, and emits the page.

---

## Credits

Inspired by S. Keshav's *How to Read a Paper* (SIGCOMM CCR, 2007). The skill is an independent implementation; Keshav is not affiliated.

Built by Conan Xin.
