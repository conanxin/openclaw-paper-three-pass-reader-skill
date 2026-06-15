# Agent Fill Pack — paper-three-pass-reader

> This directory (`fill-pack/`) is an auto-generated **task pack** from
> `run_paper_reading.py --fill-pack`. It is NOT the reading itself.
> Its goal is to help an agent (or human) replace the `[DRAFT]` placeholders in
> `work/paper_reading.json` with real content.

## Current run status

| Field | Value |
| --- | --- |
| slug | `runs` |
| paper_reading.json path | `runs/source-resolution-consumers-smoke-20260615/matched-paper_reading.json` |
| input_kind | `paper_title` |
| reading_mode | `full_text` |
| confidence | `high` |
| needs_confirmation | `False` |
| agent profile | `default` |
| max_claims | `8` |
| max_figures | `6` |

## What's already doable

- Stage 0 intake/resolution: runner already wrote `paper_metadata`, `intake_quality`, `source_resolution`.
- One / three / ten sentence summaries: can draft from abstract but must keep `[Author claim]` / `[Needs verification]`.
- Pass 1 (Five Cs): can write a skeleton from metadata + abstract.

## What's NOT doable

- Pass 2 main ideas / method summary / Pass 3 reconstruction: only fillable when `reading_mode == full_text`.
- Claims-Evidence Map: every weak-mode claim must carry `[Author claim]` / `[Uncertain]` / `[Needs verification]`.
- Reproduction plan: weak mode can only say "TBD".

## Source Resolution summary (v0.2.8)

This section is the resolver trail that the runner has already computed.
During Stage 0 the agent must **prefer the top-level `source_resolution`
structured block** over the legacy `intake_quality.source_resolution` list.

- **Hint input**: `Attention Is All You Need`
- **Resolver status**: `matched`
- **Match type**: `title`
- **Confidence**: `high`
- **Matched paper**: `Attention Is All You Need`
- **Matched arXiv ID**: `1706.03762`
- **Matched repo**: `(none)`
- **Resolver source**: `skills/paper-three-pass-reader/data/resolver_hints.json`
- **Source resolution step**: `cli overlay via p3pr paper_title subcommand`
- **Candidate count**: `1`
- **Structured trail**: `True`
- **Legacy fallback**: `False`

Top candidates:
  - Attention Is All You Need (confidence: high)


## Source Resolution Checklist (v0.2.8)

Before Stage 0 is closed, the agent must verify each item:

- [ ] Read `source_resolution` (the **top-level structured block is canonical**,
  not `intake_quality.source_resolution`).
- [ ] Keep the legacy `intake_quality.source_resolution` list alive for v0.2.5
  historical samples; do not delete it.
- [ ] Surface `confidence` (high / medium / low or a 0.0–1.0 number).
- [ ] Surface `matched_paper_id` and `matched_arxiv_id` (when `resolver_status=matched`).
- [ ] If `resolver_status` is `ambiguous_clue` or `error` /
  `degraded = ambiguous_clue`, record it in `intake_quality.ambiguities` and ask
  the user to confirm the paper identity.
- [ ] If `resolver_status = error`, confirm `source_resolution.degraded` is set
  and `intake_quality.warnings` is non-empty.

Debug with:
`python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "<hint>"`.


## How to fill `work/paper_reading.json` step by step

Open each numbered markdown file below in order. After each step, edit the corresponding field in `work/paper_reading.json`.

1. `01_stage0_intake_resolution.md`
2. `02_pass1_five_cs.md`
3. `03_pass2_main_ideas.md`
4. `04_claims_evidence_map.md`
5. `05_figures_tables.md`
6. `06_pass3_reconstruction.md`
7. `07_critical_review.md`
8. `08_reproduction_plan.md`
9. `09_finalize_json.md`
10. `10_quality_gate.md`

## Re-render

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input runs/source-resolution-consumers-smoke-20260615/matched-paper_reading.json \
  --output runs/paper-reading-output
```

## Re-audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input runs/source-resolution-consumers-smoke-20260615/matched-paper_reading.json --json-output runs/source-resolution-consumers-smoke-20260615/audit_result.json
```

## Publish to GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output runs/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish runs"
```

> Don't publish before you've actually read the paper. Weak input can be published,
> but the page's reading mode badge must show `full_text` honestly.

## What NOT to do

- Don't relabel `[Author claim]` / `[Uncertain]` to `[Paper evidence]` — the audit will catch it.
- Don't write sentences like "Pass 3 reconstruction was performed" when you have no body.
- Don't expand this into a SaaS / automatic paper summarizer / external LLM API.
