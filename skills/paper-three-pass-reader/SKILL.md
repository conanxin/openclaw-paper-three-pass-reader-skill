---
name: paper-three-pass-reader
version: 0.1.0-alpha
description: |
  Local-first three-pass paper reading skill implementing S. Keshav's
  "How to Read a Paper" (2007). Normalises any paper-shaped input
  (PDF, URL, DOI, arXiv ID, title, abstract, screenshot, topic clue,
  GitHub repo) into a canonical paper record, runs three disciplined
  reading passes with explicit evidence labels, and produces an
  interactive offline HTML reading page plus JSON / Markdown reports.
license: MIT
---

# paper-three-pass-reader

> Read once, read the right way, and walk away with a page that proves you understood the paper.

This skill is a **workflow + artifact generator**, not a paper-reading model in itself. The model (you, the agent, or a human) supplies the interpretive work; the skill supplies the **discipline, the structure, the evidence labels, and the page**.

---

## Purpose

A single, reproducible procedure for understanding a paper well enough to:

1. Explain it to someone else in one sentence, three sentences, and ten sentences.
2. Identify the main contributions, the evidence behind each, and the limitations.
3. Reconstruct the method without re-reading the paper.
4. Plan a reproduction.
5. Publish the result as a self-contained HTML page (offline + GitHub Pages friendly).

The skill is **evidence-disciplined**: every interpretive statement carries one of six labels so the reader can tell what is paper-grounded and what is agent-inferred.

---

## When to Use

Use this skill when:

- You have a paper (or a strong hint at one) and want to **understand it rigorously**, not just summarise it.
- You're preparing for a reading group, literature review, thesis chapter, or a project that depends on a specific paper.
- You want a durable artifact (HTML page + JSON + Markdown reports) you can re-read, share, or publish.
- You're an AI agent and want a paper-reading workflow with explicit **evidence labels** instead of vibes-based summarisation.

Do **not** use when:

- You only need a quick "what's this paper about?" blurb — use `pdf-to-markdown-pipeline` or a single LLM call instead.
- You need to extract the text of a scanned PDF — handle OCR / text extraction upstream, then feed the extracted text into this skill.
- You're indexing hundreds of papers — this skill is for **one paper at a time**, read deeply.

---

## Inputs

Stage 0 accepts any of these input kinds and normalises them into a canonical paper record.

### Complete paper inputs

| Kind | What it means | Examples |
|---|---|---|
| `complete_paper` | You have the paper text / file | PDF, local PDF path, full text, LaTeX source, HTML paper page |
| `paper_url` | A URL that should resolve to the paper | arXiv URL, DOI URL, publisher URL (ACM / IEEE / Springer / Nature / ScienceDirect), OpenReview URL, PubMed / bioRxiv / medRxiv URL |
| `paper_identifier` | A direct ID | arXiv ID (`2301.12345` or `cs.CL/0102034`), DOI, OpenReview ID |

### Partial paper inputs

| Kind | What it means | Examples |
|---|---|---|
| `paper_title` | Just a title string | "How to Read a Paper" |
| `paper_metadata` | Title + author(s) + year + venue | `{ "title": "...", "authors": [...], "year": 2023, "venue": "NeurIPS" }` |
| `paper_excerpt` | A piece of the paper | abstract, introduction paragraph, conclusion paragraph, BibTeX entry, citation text |
| `paper_image` / `paper_screenshot` | An image of the paper | photo of a printed page, screenshot of a title page, screenshot of an abstract, screenshot of a figure or table, slide screenshot, poster image |

### Topic / intent inputs

| Kind | What it means | Examples |
|---|---|---|
| `paper_topic` | A method/model/dataset/benchmark/author/conference clue | "the paper that introduced FlashAttention" |
| `project_or_repo` | A GitHub repo or project page that accompanies a paper | `github.com/HazyResearch/safari` (and the user hints there is a paper) |
| `ambiguous_clue` | A noisy hint | a tweet, a chat snippet, a forum post mentioning a paper |

The intake stage never silently guesses. If the input is ambiguous, it produces a `candidate_papers.json` with a ranked shortlist and asks the caller (human or upstream agent) to confirm.

---

## Reading Modes

Stage 0 also assigns a `reading_mode` based on what is actually available:

| Mode | Trigger | Effect |
|---|---|---|
| `full_text` | You provided the full text or successfully parsed a PDF | All three passes can be deep; claims can be quoted directly |
| `partial_text` | You provided several sections but not the full text | Pass 1 and Pass 2 partial; Pass 3 must say "reconstruction limited by available text" |
| `abstract_only` | Only the abstract (or a similarly short excerpt) is available | Pass 1 OK; Pass 2 must explicitly mark every claim `[Author claim]`; Pass 3 degrades to "speculative reconstruction" |
| `screenshot_only` | Only an image | OCR or visual inspection is the caller's job; the skill records what is visible and marks everything else `[Needs verification]` |

The mode is shown as a **badge** in the HTML page and stored in `intake_quality.json`. The skill **never** pretends to have read more than it has.

---

## Stage 0 — Paper Intake and Resolution

Goal: turn the messy input into a **canonical paper record** with a confidence score.

### Procedure

1. **Classify the input kind** (one of the input kinds above).
2. **Extract candidate identifiers**:
   - For `paper_url` / `paper_identifier`: parse the URL or ID directly. Map `arxiv.org/abs/XXXX.YYYYY` → arXiv ID; `doi.org/...` → DOI; `openreview.net/forum?id=...` → OpenReview ID; etc.
   - For `paper_title` / `paper_metadata`: search the title. Do **not** auto-download; produce a `candidate_papers.json` shortlist and request confirmation.
   - For `paper_image` / `paper_screenshot`: rely on whatever OCR / VLM result the caller supplied. If none was supplied, ask for one. Do not invent the paper from the image alone.
   - For `paper_topic` / `project_or_repo` / `ambiguous_clue`: produce a ranked shortlist and request confirmation.
3. **Confirm the canonical paper**: combine the strongest identifier(s) into one canonical record:
   ```json
   {
     "title": "...",
     "authors": ["..."],
     "year": 2007,
     "venue": "SIGCOMM CCR",
     "identifiers": { "arxiv_id": null, "doi": "...", "openreview_id": null, "url": "..." },
     "source_kind": "complete_paper | paper_url | ...",
     "reading_mode": "full_text | partial_text | abstract_only | screenshot_only"
   }
   ```
4. **Write `intake_quality.json`** with:
   - `input_kind`
   - `reading_mode`
   - `confidence` (low / medium / high)
   - `needs_confirmation` (bool + list of what is missing)
   - `warnings` (e.g. "title-only, no abstract", "ambiguous arXiv ID")
5. **Write `source_resolution.json`** with the trail of decisions: input → parsed → candidate → confirmed.

### Output of Stage 0

- `data/intake_quality.json`
- `data/candidate_papers.json` (may be empty if input was a direct ID)
- `data/source_resolution.json`
- `data/paper_metadata.json` (canonical record)
- `reports/stage0_intake_report.md`

### Stop conditions for Stage 0

- Two candidate papers are equally plausible and the input does not disambiguate them → request confirmation, do **not** guess.
- A screenshot shows only a figure with no title or DOI → mark `screenshot_only`, flag `[Needs verification]` for everything.
- A URL 404s or DOI does not resolve → record the failure, do **not** invent a paper.

---

## Stage 1 — First Pass

Goal: 5–10 minute bird's-eye view that produces a *continue-or-stop* decision.

### Procedure

1. **Read** the title, abstract, introduction, section headings, conclusion, references.
2. **Glance** at figures and skim the math.
3. **Fill the Five Cs** (see below).
4. **Decide**: continue to Pass 2 / Pass 3, or stop.

### Five Cs

| C | Question | Where to find the answer |
|---|---|---|
| **Category** | What type of paper is this? (measurement, systems, theory, application, survey, position, methods) | Title, abstract, intro |
| **Context** | What other papers / systems / debates does it relate to? | Intro related-work, citations, references |
| **Correctness** | Do the assumptions and method seem valid? | Skim the method, look for sanity checks, threat-to-validity |
| **Contributions** | What are the paper's main contributions (≤ 3 bullets)? | Abstract, intro, conclusion |
| **Clarity** | Is the paper well-written? | Throughout — note unclear sections |

Every entry in the Five Cs is paired with an evidence label.

### Reading decision

The skill records an explicit decision in `pass1_reading_decision.md`:

- **CONTINUE_FULL** — go to Pass 2 and Pass 3.
- **CONTINUE_PARTIAL** — Pass 2 only (e.g. conference paper, not a foundational work).
- **STOP** — not worth deeper reading; record why.
- **SEEK_REFERENCES_FIRST** — go read the cited survey / foundational papers first.

### Output of Stage 1

- `reports/pass1_first_pass.md` — narrative summary of the bird's-eye read.
- `reports/pass1_five_cs.md` — the Five Cs table with evidence labels.
- `reports/pass1_reading_decision.md` — the decision and its rationale.
- A summary goes into `data/paper_reading.json` under `pass1`.

---

## Stage 2 — Second Pass

Goal: understand the content — main ideas, figures, tables, and the evidence behind each claim.

### Procedure

1. **Read** the paper with care, **skipping the proofs**.
2. **Identify main ideas** (typically 3–7) and write each as a paragraph in `pass2_main_ideas.md`.
3. **Document every figure and table** in `pass2_figures_tables.md` and `data/figures_tables.json`.
4. **List key references** in `pass2_key_references.md` — the 5–15 papers a reader of this paper must also know.
5. **Build the Claims → Evidence map** (see below).

### Claims → Evidence Map

Every load-bearing claim in the paper is recorded as one row in `data/claims_evidence_map.json`:

```json
{
  "claim_id": "C-001",
  "claim_text": "The transformer has lower inductive bias than RNNs.",
  "evidence_label": "[Author claim]",
  "evidence_location": "Section 1, paragraph 3",
  "evidence_kind": "paper_text | figure | table | external",
  "confidence": "high | medium | low",
  "notes": "...",
  "needs_verification": false
}
```

The HTML page renders this as a **filterable table** (by claim, by evidence kind, by confidence). The filter must make it trivial to find every `[Needs verification]` row.

### Output of Stage 2

- `reports/pass2_main_ideas.md`
- `reports/pass2_figures_tables.md`
- `reports/pass2_claims_evidence_map.md`
- `reports/pass2_key_references.md`
- `data/claims_evidence_map.json`
- `data/figures_tables.json`
- A summary goes into `data/paper_reading.json` under `pass2`.

---

## Stage 3 — Third Pass

Goal: reconstruct the paper as if you were its author.

### Procedure

1. **Re-read the paper as if you were the author.** Identify implicit assumptions, hidden design decisions, and failure modes.
2. **Method reconstruction**: if you had to re-implement this paper from scratch, what would you build? Write it step-by-step in `pass3_reconstruction.md`. Include enough detail that a competent engineer could start coding from it.
3. **Critical review**: write `pass3_critical_review.md` — limitations, scope, threat to validity, what is missing.
4. **Reproduction plan**: write `pass3_reproduction_plan.md` — concrete steps, dataset, hardware, expected runtime, sanity checks, success criteria.
5. **Update** the `paper_reading.json` summary under `pass3`.

### Output of Stage 3

- `reports/pass3_reconstruction.md`
- `reports/pass3_critical_review.md`
- `reports/pass3_reproduction_plan.md`
- A summary goes into `data/paper_reading.json` under `pass3`.

---

## Final Understanding Page

Goal: a single HTML page that consolidates everything into one re-readable artifact.

### Required sections (HTML)

1. **Hero Summary** — title, authors, year, venue, link to canonical record.
2. **Paper Metadata** — full canonical record.
3. **Intake Status** — `input_kind`, `reading_mode`, `confidence`, warnings.
4. **One-sentence Summary** — exactly one sentence.
5. **Three-sentence Summary** — exactly three sentences.
6. **Ten-sentence Summary** — exactly ten sentences (or close to it).
7. **Paper Map** — sections / subsections / figures / tables as a tree.
8. **Five Cs Dashboard** — the Five Cs as cards.
9. **Pass 1 / Pass 2 / Pass 3 Tabs** — narrative + decisions for each pass.
10. **Claims-Evidence Map** — filterable table (by claim / evidence kind / confidence).
11. **Figures and Tables Explanation** — one paragraph per figure/table.
12. **Key Terms Glossary** — chips with definitions.
13. **Method Reconstruction** — the re-implementation outline.
14. **Correctness and Limitations** — what is solid, what is not, what is missing.
15. **Related Work Map** — the key references, grouped.
16. **Practical Implications** — what this paper means in practice.
17. **Reproduction Plan** — concrete steps to reproduce.
18. **Open Questions** — what this paper does not answer.
19. **"Do I understand this paper?" Checklist** — final self-test.

### Required interactions

- **Tabs** for Pass 1 / Pass 2 / Pass 3.
- **Accordions** for long sections (figures, glossary, references).
- **Claim filter** on the Claims-Evidence Map.
- **Confidence labels** visible everywhere (high/medium/low).
- **Reading mode badge** in the hero (full_text / partial_text / abstract_only / screenshot_only).
- **Evidence labels** visible on every interpretive statement.
- **Progress timeline** showing Pass 1 → Pass 2 → Pass 3 with completion.
- **Glossary chips** clickable to expand definitions.
- **Local-only static HTML** — no fetch, no external CDN, no backend.

### Final reading report

A short Markdown summary that lives at `reports/final_reading_report.md` and is also rendered inside the HTML page. It answers:

1. What is this paper about (one sentence)?
2. Is it worth reading deeper? (Pass 1 decision + rationale)
3. What are the main contributions? (3 bullets)
4. Where is the evidence strongest / weakest? (Claims → Evidence summary)
5. What would I change if I were the author? (critical review highlights)
6. Can I reproduce it? (reproduction plan feasibility)
7. What remains open?

---

## Evidence Discipline

Every interpretive statement in the page and reports carries exactly one of these labels:

| Label | Meaning |
|---|---|
| `[Paper evidence]` | Direct quote or faithful paraphrase from the paper text |
| `[Figure/Table evidence]` | Grounded in a specific figure or table |
| `[Author claim]` | Claim attributed to the authors; not independently checked |
| `[Agent inference]` | The agent's interpretation, not in the paper |
| `[Uncertain]` | Confidence is low, evidence is thin |
| `[Needs verification]` | Flagged for follow-up |

The HTML page styles each label differently. The Claims-Evidence Map filter surfaces all `[Needs verification]` and `[Uncertain]` rows by default.

---

## Output Files

Every run creates `paper-reading-output/` with the standard structure (see README). The directory is fully self-contained:

```
paper-reading-output/
├── README.md
├── index.html
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

---

## Stop Conditions

Stop the skill run (do not silently continue) when:

- The input is too ambiguous to identify a single paper → return `intake_quality.json` with `needs_confirmation: true` and a ranked shortlist, then stop.
- The reading_mode is `screenshot_only` and no OCR / VLM text is supplied → stop after Stage 0 with a clear "I cannot read the paper yet" message.
- A required field of `paper_metadata.json` cannot be filled with confidence → mark the field `null` and surface it in the HTML Intake Status panel.
- The agent is asked to do a pass beyond what `reading_mode` supports (e.g. Pass 3 with `abstract_only`) → perform a *labeled speculative* pass and make the label visible at the top of every section.

---

## Quality Bar

A `paper-reading-output/` directory is considered complete when:

- `index.html` opens in a browser and renders all 19 sections.
- Every interpretive statement carries an evidence label.
- The Claims-Evidence map has at least one row for each contribution in Pass 1.
- The reproduction plan names a dataset, a baseline, and a sanity check.
- The "Do I understand this paper?" checklist has at least 8 questions.
- The reading mode badge matches the input kind.

A run is considered **PASS** when all of the above hold. Otherwise it is **PARTIAL**, and the HTML page must show which sections are missing.

---

## Completion Message

When the run finishes, return a short status block:

```
status: PASS | PARTIAL | BLOCKED
output_dir: <absolute path to paper-reading-output/>
reading_mode: full_text | partial_text | abstract_only | screenshot_only
five_cs_count: <n>
claims_count: <n>
open_questions_count: <n>
next_action: <one of: 'open index.html', 'review claims', 'add references', 're-run stage', 'manual confirmation needed'>
```

This block is what upstream agents (and humans) read to decide what to do next. Do not bury it in prose.

---

## License

MIT.
