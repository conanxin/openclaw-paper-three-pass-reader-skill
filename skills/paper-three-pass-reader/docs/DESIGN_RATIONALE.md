# Design Rationale

Why this skill is the way it is.

---

## Why start with Intake and Resolution?

Because guessing the paper is the most common failure mode in paper reading. Two papers can share a title, a DOI can resolve to the wrong thing because of an OCR mistake, and a screenshot might show only a figure, not the title page.

Stage 0 forces the agent (or human) to:

1. Classify the input — is this a complete paper, a URL, a title, a screenshot, a topic clue?
2. Extract the strongest identifiers.
3. Produce a canonical record with a confidence score and a reading mode.

If Stage 0 cannot confidently identify a single paper, it returns `needs_confirmation: true` and a ranked `candidate_papers.json` shortlist. It **does not** guess. The rest of the skill is honest about what it knows.

This matters because every downstream artifact (Five Cs, claims map, reproduction plan) is grounded in the paper identity. A wrong identity means everything downstream is wrong, but in a way that's hard to spot because it all looks consistent.

---

## Why not just summarise the paper directly?

Three reasons:

1. **A summary hides the evidence.** "The paper says X" is meaningless unless you also know which figure, table, or section proves X. The Claims → Evidence map forces every claim to be grounded.
2. **A summary is the same artifact at every time budget.** Keshav's insight — that a paper is a different thing at 5 min, 1 h, and 4 h — is lost when you collapse everything into one paragraph.
3. **A summary is non-interactive.** A reading page with tabs, accordions, and a confidence filter serves both the 5-minute skim and the 4-hour reconstruction. A summary serves neither.

---

## Why three passes?

Because the same paper demands different things from you depending on what you want from it:

- **Pass 1** (5–10 min) → triage. Decide whether the paper is worth your time.
- **Pass 2** (~1 h) → understand. Know the main ideas, the claims, the evidence.
- **Pass 3** (1–4 h) → reconstruct. Be able to re-implement it; be able to critique it.

Most paper-reading advice collapses these into "read the paper and take notes". Keshav's contribution is to give them explicit, defensible time budgets and explicit per-pass artifacts.

The skill records which passes were actually run. If you only did Pass 1, the page says so. If you tried to do Pass 3 with `abstract_only` mode, the page marks the reconstruction as *speculative*. Pretending you did all three passes when you only did one is a failure mode the skill exists to prevent.

---

## Why Five Cs?

Because Keshav's framework survives when everything else changes.

- It's **portable** — works on theory, systems, application, methods, survey, position papers.
- It's **fast** — five short answers is a 5-minute task.
- It's **comparable** — two papers' Five Cs sit next to each other in a literature review.
- It's **honest** — the "Correctness" C forces you to actually look at the method, not just skim the abstract.

Modern additions to consider (Reproducibility, Societal Impact, Open Science) are deliberately **not** in the Five Cs in v0.1.0-alpha. The skill's stance is: don't bloat the framework until the additions are time-tested. A future v0.2 may add a sixth C; that's a one-line JSON change.

---

## Why a Claims → Evidence map?

Because the most common failure mode in paper reading is *confabulation* — saying "the paper claims X" when in fact you inferred X from the abstract. A Claims → Evidence map forces every claim to be paired with:

- The exact text section, figure, or table that grounds it (`evidence_location`).
- The kind of evidence (`evidence_kind`: paper_text, figure, table, external).
- A confidence rating.
- An evidence label that signals provenance (`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`).

The HTML page's filter surfaces every `[Needs verification]` row by default. If the filter is empty, you have a clean reading. If it's not, you know what to chase down.

This is the single most important artifact of Pass 2. Without it, Pass 3's "reconstruction" is just an essay.

---

## Why an interactive HTML page?

Because reading is interactive. The same artifact needs to serve:

- The 5-minute skim (Hero Summary + Five Cs + 1-sentence summary).
- The 1-hour understanding pass (Pass 2 tab + Claims → Evidence map + Figures).
- The 4-hour reconstruction (Pass 3 tab + Method Reconstruction + Reproduction Plan).

A flat Markdown document cannot do all three. The HTML page uses **tabs** for passes, **accordions** for figures and glossary, **claim filtering** for the evidence map, **confidence labels** everywhere, and a **progress timeline** that shows which passes are done.

The page is **local-only**. No CDN, no fetch, no backend. It opens from `file://`. That means it works on a plane, in a country with no internet, and in ten years when the CDN has shut down.

---

## Why distinguish full_text / partial_text / abstract_only / screenshot_only?

Because the most insidious failure mode in paper reading is **pretending you read the paper when you didn't**.

- `full_text` — you have the whole thing. Claims can be quoted.
- `partial_text` — you have several sections but not all. Pass 3 must say "limited by available text".
- `abstract_only` — you have a paragraph. Every claim is `[Author claim]` until you verify.
- `screenshot_only` — you have an image. Everything is `[Needs verification]` until OCR or VLM runs.

The reading mode badge in the page hero makes the limitation visible at a glance. A reader who sees `screenshot_only` knows to take every claim with a grain of salt.

This is also why Stage 0 refuses to silently "promote" a screenshot to a paper: the OCR result (when it exists) is the caller's responsibility to provide, not the skill's responsibility to invent.

---

## Why a static page, not a SaaS?

Because:

- A SaaS would need authentication, storage, and a backend. That's a maintenance burden and a privacy risk.
- A static page can be served from `file://`, GitHub Pages, S3, or any static host.
- A static page survives the death of the company that wrote it.
- The page is the **artifact**, not the service. The service is a renderer (`render_page.py`) that produces the artifact.

If you want a SaaS, you can host the page yourself. If you don't, you can read it offline. Either way, the artifact is yours.

---

## Why an agent workflow?

Because the bottleneck in paper reading is not "what does this paper say?" — that's what the paper itself is for. The bottleneck is **enforcement of discipline**:

- Did you actually do the Five Cs, or did you skip to the abstract?
- Did you actually find the figure that grounds claim C-007, or did you assume it?
- Did you actually virtualise the system in Pass 3, or did you write a generic critique?

An agent can be told to fill `paper_reading.json` stage by stage and refuse to skip steps. The evidence labels and the reading mode make the agent's work auditable. A human reviews the JSON between passes, then the page is rendered.

This is also why the schema is deliberately verbose — every field is a forcing function. You cannot finish Stage 0 without naming the paper. You cannot finish Pass 1 without choosing a decision. You cannot finish Pass 3 without writing a reproduction plan.

---

## Why MIT?

Because the workflow is more useful if everyone uses it. If the skill helps you read a paper better, it should help your collaborator read a paper better too, with the same structure.

---

## What this skill is not

- It is not a paper-extraction pipeline. Bring your own PDF / HTML / text.
- It is not a literature-review generator. It produces one reading at a time.
- It is not a knowledge graph. The artifact is a single page.
- It is not an LLM. The skill assumes a human or an agent supplies the interpretive work.

The skill is the **discipline and the artifact**. The reading is yours.
