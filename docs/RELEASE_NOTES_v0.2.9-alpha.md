# paper-three-pass-reader v0.2.9-alpha

## Summary

This release improves rendering quality for HTML **essay / talk style** inputs, using Richard Hamming's *You and Your Research* Chinese page as the real-world smoke test.

The previous releases treated every input as a typical experimental paper. Essays and talks (Hamming-style lectures, conference keynotes, opinion pieces, blog distillations of a paper) have **no real figures or reproduction plan**, and the v0.2.8 renderer either showed empty sections, leaked raw Python dict reprs, or left behind unfinished `{% else %}` template tags. v0.2.9 fixes all of those and makes the page feel like a real reading page, not a debug dump.

## Included

- **Five Cs object rendering fix** — each of `category / context / correctness / contributions / clarity` is now normalised into `{label, value, evidence_label, note}` and rendered as a card; the raw `{'label': ...}` dict repr no longer leaks into the page.
- **Template `else` branch fix** — the mini-template engine now understands `{% if … %} … {% else %} … {% endif %}` and no longer leaks `{% else %}` (or any other unclosed `{% %}` / `{{ }}`) into the rendered HTML.
- **Essay / talk `Figures & Tables` handling** — when the input has no real figures, the section now shows `原文无传统图表` plus a list of **conceptual notes** (e.g. Hamming's most-quoted frameworks) instead of an empty table.
- **Essay / talk `Practical Plan` handling** — the `Reproduction Plan` section is renamed `实践计划 / Practical Plan` for essay-mode inputs and exposes `7 天 / 30 天 / 90 天 / 成功标准 / 风险与反例` blocks derived from the source's own practical advice.
- **Related-work fallback** — when the input is an essay / talk with no formal related-work section, the page now shows `相关脉络` with a clean fallback note rather than a blank list.
- **Claim ID display fix** — the Claims-Evidence table now shows real `C01` / `C02` / `…` IDs and not empty `<code></code>` cells.
- **Glossary definition display** — glossary chips now show term + Chinese term + Chinese definition in an explicit body block (previously the definition was only reachable through a tooltip).
- **Generator version update** — the page footer now reads `paper-three-pass-reader v0.2.9-alpha` (no stale `v0.1.0-alpha` carryover).
- **Re-published Chinese *You and Your Research* page** — the live page at <https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/> reflects all of the above.
- **Validation step 5 update** — `class="accordion"` legacy assertion replaced with a robust check that accepts either `class="accordion"` or native `<details>` markup; the new template uses the latter.

## Compatibility

- Existing JSON files remain readable; legacy `paper_reading.json` shapes still render (with essay-mode gracefully degrading when fields are missing).
- Existing published pages remain published. No old tags are moved and no old releases are deleted.
- `audit_paper_reading.py` and `quality_gate_zh_cn.py` interfaces are unchanged. Audit still PASSes; the embedded Newton / Pasteur quote in the YAYR `claims_evidence_map[0].comment` triggers a `WARN` from the zh-CN quality gate as expected and is documented in the phase report.

## Known minor warnings

- `quality_gate_zh_cn` reports a single `long_en_blobs` warning pointing at `claims_evidence_map[0].comment` — this is the intentional English direct quote ("If you do not work on an important problem, it's unlikely you'll do important work.") and is preserved as a Hamming original.
