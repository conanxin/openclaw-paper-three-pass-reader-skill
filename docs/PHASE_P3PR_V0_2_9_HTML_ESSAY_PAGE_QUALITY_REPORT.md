# PHASE P3PR-V0.2.9-HTML-ESSAY-PAGE-QUALITY REPORT

## STATUS

PASS

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.2.8-alpha

## TARGET_VERSION

v0.2.9-alpha

## PROBLEM

The v0.2.8 renderer treated every input as a typical experimental paper. When applied to a real-world essay / talk — Richard Hamming's *You and Your Research* — the published page at `https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/` showed six visible rendering problems:

1. The Five Cs cards rendered as raw Python dict reprs (`{'label': ...}`) instead of clean per-Card content.
2. The Related Work area leaked an unfinished `{% else %}` template tag into the final HTML.
3. The Key References list showed empty bullet placeholders.
4. The Figures & Tables section was effectively empty / noisy.
5. The footer still said `v0.1.0-alpha` because the `generator_version` field was not threaded through.
6. The Claims-Evidence table rendered claim IDs as empty `<code></code>` cells because the template read `id` while the data used `claim_id`.

Validation also asserted a legacy `class="accordion"` CSS class that the v0.2.9 template (using native `<details>`) no longer produces, producing one false-FAIL in step 5.

## FIX_SUMMARY

Renderer and template were updated together so that essay / talk inputs render as polished, formal reading pages:

- Renderer gained a real `else`-branch in its mini-template engine.
- Renderer gained `normalize_five_cs`, `normalize_claim`, `is_essay_talk`, `normalize_reproduction_plan`, `normalize_related_work`, and exposes `generator_version` / `_is_essay_talk` to the template.
- Template now uses those normalised fields, switches `Reproduction Plan` → `实践计划` for essay mode, and renders fallback strings where the source has no real figures / reproduction plan / related work.
- Validation step 5's brittle `class="accordion"` assertion was replaced with a robust `details / accordion` regex check.
- YAYR `paper_reading.json` was enriched with `plan_7_day / plan_30_day / plan_90_day / success_criteria / risks`, 5 conceptual figure notes, and 6 narrative related-work entries.
- The Chinese YAYR page was re-rendered and re-published.

## VALIDATION_FIX

`scripts/validate.sh` step 5 used to require `class="accordion"` literally. The v0.2.9 template uses native `<details>` (13 of them in the bundled sample render). Replaced the needle with a regex `class="accordion"|<details( |>)` so the assertion checks the intent (collapsible disclosure) rather than a specific CSS class. Comment in the script explains the swap.

## RENDERER_FIXES

- `skills/paper-three-pass-reader/scripts/render_page.py`:
  - `_TAG_RE` now matches `{% else %}`; `parse()` and `emit()` learn the `else` branch.
  - `GENERATOR_VERSION = "v0.2.9-alpha"` exposed as `data["generator_version"]`.
  - New `normalize_five_cs()` flattens each Five-C item into `{label, value, evidence_label, note}`.
  - New `normalize_claim()` derives `claim_id` from `id` and stamps `evidence_label`.
  - New `is_essay_talk()` + `ESSAY_TALK_CATEGORIES` set; `data["_is_essay_talk"]` exposed.
  - New `normalize_reproduction_plan()` adds `plan_7_day / plan_30_day / plan_90_day / success_criteria / risks / kind`.
  - New `normalize_related_work()` flattens dict entries into `{kind, authors, year, why, evidence_label}`.
  - `normalize_reading()` now invokes all of the above.
  - Report-writer safety: `pass1_five_cs.md` and `final_reading_report.md` no longer assume contributions are strings.

## DATA_FIXES

- `runs/you-and-your-research-20260615/you-and-your-research-cn/work/paper_reading.json`:
  - `reproduction_plan` rewritten to expose `plan_7_day` (3), `plan_30_day` (3), `plan_90_day` (3), `success_criteria` (4), `risks` (4), `kind=essay`, `rationale`.
  - `figures_tables` extended to 5 conceptual notes (Hamming's 5 most-quoted frameworks), each `{id, kind=concept, title, explanation, evidence_label}`.
  - `related_work` extended to 6 narrative entries (Bell Labs / Shannon / Los Alamos / Hamming code / research taste / career-advice literature).
  - `open_questions` extended to 6.
  - `final_checklist` retained 11 zh-CN items, each with `question`.

## ESSAY_TALK_HANDLING

- `Reproduction Plan` heading now reads `{% if _is_essay_talk %}实践计划{% else %}复现计划{% endif %}` and the body renders 7/30/90-day plans + success criteria + risks when `kind == "essay"`.
- `Figures & Tables` heading reads `图表 / 结构说明` and the empty state shows `原文无传统图表` followed by conceptual notes when the source is essay-mode.
- `Related Work` heading reads `相关脉络` and shows a `原文不是学术论文…` fallback for essay-mode inputs.
- `Five Cs` heading reads `Five Cs 面板` everywhere (consistent across modes) but its card rendering is now mode-agnostic because the dict is always flattened.

## ZH_CN_UI_FIXES

All English headings/filter labels in `skills/paper-three-pass-reader/templates/index.html` were replaced with zh-CN labels (e.g. `论文信息 / 输入解析状态 / 摘要 / 一/三/十句话总结 / 论文地图 / 三遍阅读 / 主张—证据地图 / 关键术语 / 方法重建 / 正确性与局限 / 实践启发 / 开放问题 / 最终理解检查表 / 筛选置信度 / 筛选证据标签 / 只看需验证项`). `<html lang="…">` is set from `ui_language`. Footer uses `{{ generator_version }}`. Glossary chips show term + Chinese term + Chinese definition in an explicit `<div class="chip-body">`.

## YAYR_PAGE_REPUBLISH

- Re-rendered locally: `runs/you-and-your-research-20260615/you-and-your-research-cn/paper-reading-output/index.html` (37,717 bytes).
- Re-published to `gh-pages` of `conanxin/paper-reading-pages` via `publish_output_to_github.sh --site-path you-and-your-research-cn --page-title "You and Your Research：如何选择重要问题并做好研究"`.
- Verified: `curl -I -L` returns `200` for `/`, `/you-and-your-research-cn/`, and `/published_pages.json`.
- Live URL: <https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/>

## VALIDATION

```
PASS: 220    FAIL: 0
STATUS: PASS
```

`bash scripts/validate.sh` ran clean. `audit_paper_reading.py --quality-gate` returned `Audit status: PASS` (claims=12, glossary=13, checklist=11, no DRAFT placeholders). `quality_gate_zh_cn.py --warn-only` returned `WARN` (1 long-English-blob warning on `claims_evidence_map[0].comment`, the intentional Newton / Pasteur direct quote — preserved by design).

## FILES_CREATED

- `docs/RELEASE_NOTES_v0.2.9-alpha.md`
- `docs/PHASE_P3PR_V0_2_9_HTML_ESSAY_PAGE_QUALITY_REPORT.md`
- `runs/you-and-your-research-20260615/you-and-your-research-cn/work/audit_final.json`
- `runs/you-and-your-research-20260615/you-and-your-research-cn/work/quality_gate_zh_cn.json`

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/render_page.py`
- `skills/paper-three-pass-reader/templates/index.html`
- `scripts/validate.sh`
- `README.md`
- `README.zh-CN.md`
- `CHANGELOG.md`
- `skills/paper-three-pass-reader/docs/USAGE.md`
- `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md`
- `skills/paper-three-pass-reader/docs/SOURCE_RESOLUTION.md`
- `docs/REALPAPER_RUNS.md`
- `runs/you-and-your-research-20260615/you-and-your-research-cn/work/paper_reading.json`
- `runs/you-and-your-research-20260615/you-and-your-research-cn/paper-reading-output/index.html` (re-rendered)
- `runs/you-and-your-research-20260615/you-and-your-research-cn/paper-reading-output/data/*` (re-rendered)
- `runs/you-and-your-research-20260615/you-and-your-research-cn/paper-reading-output/reports/*` (re-written)

## COMMIT

`git commit -m "Polish HTML essay reading page rendering"`

(SHA will be filled in by the git step in the run that actually commits; not pre-computed here.)

## PUSH

`git push origin main` — pending the git step.

## TAG

Annotated tag `v0.2.9-alpha` pointing at the post-render commit. Pending the git step.

## RELEASE

GitHub Release `paper-three-pass-reader v0.2.9-alpha` with `--notes-file docs/RELEASE_NOTES_v0.2.9-alpha.md`. Pending the gh step.

## GITHUB_PAGES_URL

<https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/>

## LIMITATIONS

- `quality_gate_zh_cn` reports a single `long_en_blobs` warning on `claims_evidence_map[0].comment` (Hamming's direct English quote). Preserved by design.
- Validation step 5 no longer asserts a literal `class="accordion"`. The legacy CSS class is still present in `templates/style.css` for any pages that opt to use it; the template itself uses `<details>`.
- Re-published page is one essay example. The renderer now handles both essay/talk and experimental-paper modes, but more varied samples (slides, posters, opinion pieces) have not been re-rendered.

## NEXT_USER_ACTION

- Verify the live page at <https://conanxin.github.io/paper-reading-pages/you-and-your-research-cn/> in a browser.
- Optionally re-render the other published essay pages (e.g. `second-me` Chinese, `arxiv-2503.08102`) to take advantage of the new glossary / claim-ID / footer-version fixes.
- Consider promoting `class="accordion"` out of `templates/style.css` in a later release if no template uses it.
