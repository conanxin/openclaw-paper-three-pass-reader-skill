# SOURCE_RESOLUTION — paper-three-pass-reader (v0.2.8)

This document is the canonical reference for the **structured
`source_resolution` block** that lives at the top level of every
`paper_reading.json` draft produced by `paper-three-pass-reader` since
v0.2.7. v0.2.8 makes every downstream consumer (renderer, audit,
fill-pack, zh-CN quality gate) read it.

> The top-level structured `source_resolution` block is canonical. The
> legacy `intake_quality.source_resolution` list is **kept** for
> back-compat with v0.2.5 samples; the shared utility
> `scripts/source_resolution_utils.py` upgrades it on the fly so
> downstream consumers do not need a branch.

---

## Where the block lives

`paper_reading.json` (v0.2.7+):

```jsonc
{
  "source_resolution": {
    "steps": ["..."],                  // ordered resolver attempts (audit trail)
    "hint_input": "Attention Is All You Need",
    "resolver_source": "skills/paper-three-pass-reader/data/resolver_hints.json",
    "resolver_helper": "skills/paper-three-pass-reader/scripts/resolver_hints.py",
    "resolver_status": "matched",      // matched | weak | ambiguous_clue | error
    "resolver_match_type": "title",    // title | alias | repo | arxiv | abstract | overlay
    "confidence": "high",              // "high" | "medium" | "low" | 0.0-1.0 number
    "matched_paper_id": "attention-is-all-you-need",
    "matched_canonical_title": "Attention Is All You Need",
    "matched_arxiv_id": "1706.03762",
    "matched_alias": null,
    "matched_repo": null,
    "candidates": [{"id": "...", "title": "...", "arxiv": "...", "confidence": "..."}],
    "source_resolution_step": "cli overlay via p3pr paper_title subcommand",
    "degraded": null,                  // "ambiguous_clue" if the resolver helper crashed
    "fallback_legacy": false           // true when this block was synthesised from intake_quality.source_resolution
  }
}
```

### Required minimum fields (for a healthy draft)

- `resolver_status` (one of `matched`, `weak`, `ambiguous_clue`, `error`)
- `resolver_match_type` (string or null)
- `confidence` (string label or number)
- `source_resolution_step` (string, used for tracing)

### Matched cases should also carry

- at least one of `matched_paper_id` / `matched_canonical_title` / `matched_arxiv_id`

### Error / degraded cases should also carry

- `degraded: "ambiguous_clue"` plus a `intake_quality.warnings` entry —
  never a bare `resolver_status: "error"` with no degradation marker.

---

## Helper module

`skills/paper-three-pass-reader/scripts/source_resolution_utils.py`

Public API:

| function | purpose |
| --- | --- |
| `is_structured_source_resolution(value)` | True if `value` looks like the canonical block. |
| `get_source_resolution(data)` | Return the structured block, with `intake_quality.source_resolution` legacy fallback. |
| `legacy_source_resolution_to_structured(legacy)` | Upgrade a legacy list / dict to the canonical shape. |
| `summarize_source_resolution(data)` | Renderer-friendly summary (17 keys, including `candidate_count` and `candidates_top`). |
| `validate_source_resolution(data)` | Returns `(errors, warnings)`. Always non-throwing. |

The helper has a tiny CLI for debugging:

```bash
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "Attention Is All You Need"
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py repo https://github.com/google-research/bert
python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py arxiv 2503.08102
```

---

## Consumers

| consumer | behaviour in v0.2.8 |
| --- | --- |
| `render_page.py` | Renders a new "Resolver Trail" section in `index.html` with: structured / legacy badge, Resolver status, Match type, Confidence, Matched paper / id, Matched arXiv ID, Matched repo, Resolver source, Source resolution step, Candidate count, Top 3 candidates, a "Degraded fallback" badge and a callout when the resolver returned an error. Localised for zh-CN. |
| `audit_paper_reading.py` | Adds a `source_resolution` field to the audit OrderedDict with `status / structured / legacy_fallback / warnings / errors / summary`. WARNs on legacy-only, WARNs on missing structured block (non-weak modes), WARNs on `matched` without identity, WARNs on missing confidence, FAILs on `error` with no degraded / warning marker. |
| `fill_pack_writer.py` | Embeds a "Source Resolution 摘要 (v0.2.8)" block in `fill-pack/00_README.md` (zh and en) listing the trail plus a "Source Resolution Checklist" the agent must tick off before Stage 0 closes. |
| `quality_gate_zh_cn.py` | Adds a `source_resolution_check` field to the gate result. WARNs (as recommendations, **never as gate failures**) when the structured block is missing, when `resolver_status` is `error` / `ambiguous_clue`, or when matched title / arXiv id is empty. |

---

## How renderer renders it

The renderer injects `source_resolution_summary` (from
`summarize_source_resolution`) into the Jinja context and adds a
`#resolver-trail` section to `templates/index.html`. Look for:

- `Resolver status` (or `解析状态` in zh-CN)
- `Match type` (or `匹配类型`)
- `Confidence` (or `置信度`)
- `Matched paper` (or `匹配论文`) / `Matched paper id` (or `匹配论文 ID`)
- `Matched arXiv ID` (or `匹配 arXiv ID`)
- `Matched repo` (or `匹配仓库`)
- `Resolver source` (or `解析来源`)
- `Source resolution step` (or `解析步骤`)
- `Candidate count` (or `候选数量`)
- `Top candidates (...)` (collapsed `<details>`)
- `Degraded fallback: <value>` (red badge)
- a callout below the badges when the resolver reported an error

---

## How audit checks it

`audit_paper_reading.audit(doc)` reads the block via the shared helper
and adds a `source_resolution` entry to the OrderedDict result. The
audit also runs the helper's own `validate_source_resolution` as a
sanity overlay, so the `errors` and `warnings` you see on the
`source_resolution` sub-dict are the helper's output, not a duplicate.

When the audit returns:

```json
{
  "source_resolution": {
    "status": "matched",
    "structured": true,
    "legacy_fallback": false,
    "warnings": [],
    "errors": [],
    "summary": { "matched_paper_id": "attention-is-all-you-need", "...": "..." }
  }
}
```

…you can trust the resolver trail.

---

## How fill-pack guides the agent

`fill-pack/00_README.md` (zh-CN and en) now includes a "Source
Resolution 摘要 (v0.2.8)" block with the trail rendered as a list, plus
a "Source Resolution Checklist" the agent must tick off:

- Read top-level `source_resolution` (NOT `intake_quality.source_resolution`).
- Keep the legacy list alive for v0.2.5 historical samples.
- Surface `confidence` and `matched_paper_id` / `matched_arxiv_id`.
- When `resolver_status` is `ambiguous_clue` or `error` / `degraded =
  ambiguous_clue`, record it in `intake_quality.ambiguities` and ask
  the user to confirm the paper identity.
- Debug with `python3 skills/paper-three-pass-reader/scripts/resolve_paper_hint.py title "<hint>"`.

---

## How zh-CN quality gate checks it

`quality_gate_zh_cn.run_quality_gate(doc, args)` returns:

```json
{
  "source_resolution_check": {
    "structured": true,
    "legacy_fallback": false,
    "resolver_status": "matched",
    "warnings": [],
    "errors": []
  }
}
```

`source_resolution_check` warnings are converted to
`recommendations` in the result, **never** to errors — so they never
fail the gate on their own. They serve as a paper-identity sanity
prompt for the agent / user.

---

## Validation

`scripts/validate.sh` step 15 covers consumers end-to-end:

- utility import
- utility reads structured block
- legacy-only sample does not crash
- matched render contains "Resolver status" / "Confidence" / "Matched arXiv ID" / paper id / arXiv id
- zh-CN render contains "解析状态" / "置信度" / "匹配 arXiv ID" / arXiv id
- degraded render contains "Degraded fallback" badge + "Resolver status"
- audit JSON has `source_resolution` block with summary
- quality gate JSON has `source_resolution_check` with structured flag
- all 4 fill-pack `00_README.md` files contain "Source Resolution"
- zh-CN fill-pack contains "解析状态" or "输入线索"
- v0.2.6 runner smoke still has structured source_resolution
- p3pr dry-run smoke still has structured resolver output

210/0 PASS as of v0.2.8.

---

## Backwards compatibility

- v0.2.5 historical samples (no top-level block, legacy list only)
  continue to render and audit. The shared helper upgrades them on
  the fly. A WARN is recorded.
- A draft with **no** `source_resolution` block at all is WARNed
  (not failed) unless `reading_mode` is `screenshot_only` /
  `abstract_only`, where the warning is suppressed because no resolver
  ever runs in those modes anyway.

---

## v0.2.9-alpha renderer 消费方更新

`render_page.py` 通过 `source_resolution_utils.get_source_resolution` 读取结构化 block,完全沿用 v0.2.8 的消费约定。v0.2.9 主要是把渲染质量打磨:

- 渲染页面的 footer 不再错误显示 v0.1.0-alpha,改为 `{{ generator_version }}` → `paper-three-pass-reader v0.2.9-alpha`。
- essay / talk 模式识别后会切换为 `实践计划 / 结构说明 / 相关脉络` 等中文标题,而不是默认的 `复现计划 / 图表 / Tables`。
- Claims-Evidence 表的 `C01` / `C02` ID 来自 `normalize_claim`,与 source_resolution 无关;但源解析失败时,fallback "Degraded fallback" 徽标会保留。
- 验证 220/0 PASS (v0.2.8 baseline 210 + 10 new step-16 essay / talk checks)。

---

## v0.2.14-alpha: URL input source resolution

The new `p3pr url <url>` subcommand produces drafts where the
`source_resolution` block is filled in even when no built-in paper
hint matched. The CLI's overlay passes these fields through:

| Field | Value (v0.2.14 url subcommand) |
|---|---|
| `hint_input` | The user-supplied URL |
| `resolver_source` | `user_supplied_url` (CLI overlay) |
| `resolver_status` | `not_found` (URL did not hit a built-in paper) — unless a known alias did match, in which case `matched` |
| `resolver_match_type` | `none` (or `legacy` / `arxiv` / `repo` if the URL happened to match) |
| `confidence` | `low` (or `high` if matched) |
| `matched_paper_id` | `None` (or the matched id) |
| `source_resolution_step` | `cli overlay via p3pr paper_url subcommand; input='<url>'` |

The `paper_metadata.identifiers.url` is the same URL. The
`intake_quality.warnings` array includes:

> "Input did not match any built-in resolver hint. Canonical identification is NOT confirmed; needs human confirmation."

so the agent / human filling the draft knows to confirm the paper identity
before treating the page as a real reading.

When `--input-file` is also supplied (the new v0.2.14 behaviour for
`p3pr url`), the runner records the local extracted body in
`input/input.md` alongside the URL, so the audit trail shows both the
"what the user pointed at" and the "what we actually have on disk".
