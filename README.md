# paper-three-pass-reader

A local-first **three-pass paper reading skill** for Hermes / OpenClaw agents and humans.
It implements S. Keshav's *How to Read a Paper* method (2007) as a reproducible, evidence-disciplined workflow that ends in an interactive HTML page you can read offline or publish to GitHub Pages.

> Read once, read the right way, and walk away with a page that proves you understood the paper.

---

## What this skill is

A single-skill package that takes **any of the things that hint at a paper** — a PDF, an arXiv URL, a DOI, a title, a screenshot of the title page, an abstract, a social media post, a GitHub repo, or just a topic — and produces:

1. A canonical **paper identity** (Stage 0: Intake & Resolution)
2. A **first-pass triage** with the Five Cs (Stage 1)
3. A **second-pass understanding** with a Claims → Evidence map (Stage 2)
4. A **third-pass reconstruction** with critique and reproduction plan (Stage 3)
5. A **self-contained interactive HTML page** that holds all of it

The skill is **local-only**, **static**, and **no backend**. The HTML page works straight from `file://`.

---

## When to use it

Use `paper-three-pass-reader` when:

- You have a paper (or a strong hint at one) and want to **understand it rigorously**, not just summarise it.
- You're preparing for a reading group, a literature review, a thesis chapter, or a project that depends on a specific paper.
- You want a durable artifact (HTML page + JSON + Markdown reports) you can re-read, share, or publish.
- You're an AI agent and want a paper-reading workflow with explicit **evidence labels** instead of vibes-based summarisation.

Do **not** use it when you only need a quick "what's this paper about?" blurb — that's `pdf-to-markdown-pipeline` or a single LLM call.

---

## Supported inputs

Stage 0 normalises any of these into a canonical paper:

| Input type | Examples |
|---|---|
| `complete_paper` | PDF file, full text, LaTeX source, HTML paper |
| `paper_url` | arXiv, DOI, publisher (ACM/IEEE/Springer/Nature/ScienceDirect), OpenReview, PubMed/bioRxiv/medRxiv |
| `paper_identifier` | arXiv ID, DOI, OpenReview ID |
| `paper_title` | "How to Read a Paper" |
| `paper_metadata` | title + author(s) + year + venue |
| `paper_excerpt` | abstract, introduction, conclusion, BibTeX, citation |
| `paper_image` / `paper_screenshot` | photo of a printed page, slide screenshot, poster |
| `paper_topic` | method/model/dataset/benchmark/author/conference clue |
| `project_or_repo` | GitHub repo or project page that accompanies a paper |
| `ambiguous_clue` | a social-media post or screenshot mentioning a paper |

The intake step always outputs an `intake_quality.json` and a `reading_mode` so you know whether the skill is operating on **full text**, **partial text**, **abstract only**, or **screenshot only**.

---

## The three-pass method

This skill faithfully implements Keshav (2007), *How to Read a Paper*:

### Pass 1 — Bird's-eye view (5–10 minutes)

- Read the **title, abstract, introduction, section headings, conclusions, references**.
- Glance at the figures and skim the math.
- Try to answer the **Five Cs**:
  - **Category** — what type of paper is this?
  - **Context** — what other papers does it relate to?
  - **Correctness** — do the assumptions and method seem valid?
  - **Contributions** — what are the paper's main contributions?
  - **Clarity** — is the paper well-written?
- Decide whether to read further. The skill records this decision explicitly.

### Pass 2 — Understand the content (≈1 hour)

- Read the paper with greater care, but **skip the proofs**.
- Identify the **main ideas, claims, evidence, and figures/tables**.
- Build a **Claims → Evidence map**: every load-bearing claim is paired with the figure/table/section that supports it (or flagged as "needs verification").

### Pass 3 — Reconstruct the paper (1–4 hours, for the deep dive)

- Re-read the paper **as if you were the author**: identify the implicit assumptions, the hidden decisions, the failure modes.
- Build a **method reconstruction**: if you had to re-implement this paper from scratch, what would you build?
- Write a **critical review**: limitations, scope, threat to validity, and the **reproduction plan** that would let you (or someone else) re-run the key experiment.

---

## Output directory

Every run creates a `paper-reading-output/` directory:

```
paper-reading-output/
├── README.md
├── index.html                 # interactive reading page
├── assets/
│   ├── style.css
│   └── app.js
├── data/
│   ├── intake_quality.json
│   ├── candidate_papers.json
│   ├── source_resolution.json
│   ├── paper_metadata.json
│   ├── paper_outline.json
│   ├── paper_reading.json
│   ├── claims_evidence_map.json
│   └── figures_tables.json
└── reports/
    ├── stage0_intake_report.md
    ├── pass1_first_pass.md
    ├── pass1_five_cs.md
    ├── pass1_reading_decision.md
    ├── pass2_main_ideas.md
    ├── pass2_figures_tables.md
    ├── pass2_claims_evidence_map.md
    ├── pass2_key_references.md
    ├── pass3_reconstruction.md
    ├── pass3_critical_review.md
    ├── pass3_reproduction_plan.md
    └── final_reading_report.md
```

`index.html` is a single-file artifact with:

- Hero Summary, Paper Metadata, Intake Status
- 1-sentence / 3-sentence / 10-sentence summary
- Paper Map, Five Cs dashboard
- Pass 1 / Pass 2 / Pass 3 tabs
- Claims-Evidence Map (filterable)
- Figures & Tables, Glossary
- Method Reconstruction, Limitations, Related Work
- Reproduction Plan, Open Questions
- "Do I understand this paper?" checklist

---

## Quick start

### Render a sample page (no network needed)

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input skills/paper-three-pass-reader/examples/sample_paper_reading.json \
  --output paper-reading-output
```

Then open `paper-reading-output/index.html` in any browser.

### Create an empty skeleton for a new paper

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
  --output paper-reading-output \
  --title "Attention Is All You Need"
```

### Publish the page to GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish reading page for XYZ"
```

The script refuses to **create** a new repo silently — if `conanxin/paper-reading-pages` does not exist it prints the exact `gh repo create` command and stops.

### Run validation

```bash
bash scripts/validate.sh
```

This is a **smoke check**, not a test suite. It verifies files exist, JSON is valid, the sample render works, and the page contains the expected sections.

---

## Design rationale (short version)

- **Why intake first?** Because guessing the paper is the most common failure mode. Two papers can share a name, a DOI can resolve to the wrong thing, and a screenshot might show only a figure, not the title.
- **Why three passes?** Because the same paper is a different artifact at 5 minutes, 1 hour, and 4 hours. The skill records what mode each section was written in.
- **Why Five Cs?** Because Keshav's framework survives when everything else changes — it's the cheapest way to keep yourself honest on Pass 1.
- **Why a Claims-Evidence map?** Because "the paper says X" is meaningless without the figure, table, or section that proves X.
- **Why an HTML page?** Because reading is interactive. Tabs, accordions, and a confidence filter let the same page serve a 5-minute skim and a 4-hour reconstruction.
- **Why distinguish full text / partial / abstract / screenshot?** Because pretending you read the paper when you only saw the abstract is the failure mode this skill exists to prevent.

The full rationale is in [`skills/paper-three-pass-reader/docs/DESIGN_RATIONALE.md`](skills/paper-three-pass-reader/docs/DESIGN_RATIONALE.md).

---

## Evidence discipline

Every interpretive statement in the page and reports carries a label:

- `[Paper evidence]` — direct quote or paraphrase from the paper text
- `[Figure/Table evidence]` — grounded in a specific figure/table
- `[Author claim]` — claim attributed to the authors, not yet independently checked
- `[Agent inference]` — the agent's interpretation, not in the paper itself
- `[Uncertain]` — confidence is low, evidence is thin
- `[Needs verification]` — flagged for follow-up

If you see a load-bearing claim without a label, treat it as `[Needs verification]`.

---

## Limitations (v0.1.1-alpha)

- Sample data uses S. Keshav's *How to Read a Paper* itself — a meta choice. The full pipeline works on any paper, but only the Keshav sample is pre-built into the repo.
- Stage 0 is **input-driven** — it does not fetch the paper itself. You provide the paper (or the strong hint) and the skill normalises it.
- The HTML page is **static**. There is no annotation persistence, no notes sync, no shared state.
- No PDF parsing, OCR, or web scraping is included. Bring your own text or URL.
- `publish_output_to_github.sh` is intentionally minimal — it will not roll back, retry, or reconcile. If a push fails, read the error.

## Multi-page publishing (v0.1.1+)

To publish several papers into one GitHub Pages repo, use the slug mode:

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output runs/attention-is-all-you-need-20260615/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --site-path attention-is-all-you-need \
  --page-title "Attention Is All You Need"
```

The page is copied into `gh-pages/attention-is-all-you-need/` and the repo root becomes a tiny index (`index.html` + `published_pages.json`) that lists every published page. Each call adds (or updates) one entry; other pages are preserved. The script validates the slug and refuses anything outside `[A-Za-z0-9._-]+`.

> **v0.1.2-alpha note:** the multi-page cleanup step was hardened so that re-publishing one paper never deletes another paper's subdirectory on `gh-pages`. Already-published pages survive intact.

---

## One-command runner (v0.2.0-alpha)

`skills/paper-three-pass-reader/scripts/run_paper_reading.py` turns a paper-shaped input (title, abstract, OCR transcript, repo URL, …) into a standard run directory + draft `paper_reading.json` + (optional) rendered page + (optional) published GitHub Page.

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

The runner does **not** read the paper for you — it produces a DRAFT with `[DRAFT]` placeholders that you (or an agent) fill in. It enforces reading-mode discipline, writes the standard run layout, and keeps the workflow repeatable. See [`skills/paper-three-pass-reader/docs/RUNNER.md`](skills/paper-three-pass-reader/docs/RUNNER.md) for the full interface, examples, and boundaries.

---

## Agent fill pack + audit (v0.2.1-alpha)

The runner now supports `--fill-pack` and `--audit`. They are designed to make the runner output directly usable by another agent (or a human) for follow-up reading work.

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug myrun \
  --output-root runs/ \
  --reading-mode partial_text \
  --fill-pack --audit --audit-warn-only --render
```

What gets written:

- `runs/myrun/work/paper_reading.json` — the draft.
- `runs/myrun/work/audit_result.json` — full audit JSON (status, errors, warnings, recommendations).
- `runs/myrun/reports/audit_summary.md` — markdown summary.
- `runs/myrun/fill-pack/` — 11 markdown files (`00_README.md` … `10_quality_gate.md`) + `prompts.json` + `field_checklist.json` + `draft_status.json`.
- `runs/myrun/paper-reading-output/index.html` — rendered page (only if audit does not FAIL).

Key behaviors:

- `--audit` blocks `--render` and `--publish` if audit status = FAIL (use `--audit-warn-only` to relax).
- `--fill-pack` writes per-stage step instructions adapted to the current reading mode (weak modes carry explicit "weak-input" caveats).
- `audit_paper_reading.py` can be used standalone for any `paper_reading.json`:
  ```bash
  python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
    --input runs/myrun/work/paper_reading.json \
    --json-output runs/myrun/work/audit_result.json
  ```

The audit is **structural + reading-mode discipline** only. It does not judge whether the paper is correct.

See [`skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md`](skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md) and [`skills/paper-three-pass-reader/docs/AUDIT.md`](skills/paper-three-pass-reader/docs/AUDIT.md).

---

## Version history

| Tag | Status | Purpose |
|---|---|---|
| `v0.1.0-alpha` | immutable | Initial release. |
| `v0.1.1-alpha` | immutable | Renderer hardening (loose-JSON tolerance) + multi-page publishing script. |
| `v0.1.2-alpha` | immutable | Publish-script fix that preserves sibling page subdirectories on re-publish. |
| `v0.2.0-alpha` | immutable | One-command runner for turning weak/complete inputs into a standard run layout + draft JSON + (optional) rendered/published page. |
| `v0.2.1-alpha` | current | Agent Fill Pack + structural audit. Runner gained `--fill-pack`, `--audit`, `--agent-profile`, `--language`, `--max-claims`, `--max-figures`. |

This project treats published tags as immutable: never force-moves an existing tag, never rewrites history.

---

## License

MIT — see [`LICENSE`](LICENSE).

Version: **v0.2.1-alpha**.
