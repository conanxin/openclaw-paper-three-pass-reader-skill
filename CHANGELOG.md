# Changelog

All notable changes to `paper-three-pass-reader` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
