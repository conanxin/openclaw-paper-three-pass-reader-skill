#!/usr/bin/env python3
"""
fill_pack_writer.py — paper-three-pass-reader (v0.2.1-alpha)

Generates the Agent Fill Pack for a run directory. The fill pack is a set
of step-by-step task files that an agent (or a human) can follow to turn a
fresh runner draft into a real paper_reading.json.

Generated layout (under <run_dir>/fill-pack/):
    00_README.md
    01_stage0_intake_resolution.md
    02_pass1_five_cs.md
    03_pass2_main_ideas.md
    04_claims_evidence_map.md
    05_figures_tables.md
    06_pass3_reconstruction.md
    07_critical_review.md
    08_reproduction_plan.md
    09_finalize_json.md
    10_quality_gate.md
    prompts.json
    field_checklist.json
    draft_status.json

The writer is stdlib-only and language-aware (zh-CN / en).
"""

from __future__ import annotations

import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

VALID_EVIDENCE_LABELS = [
    "[Paper evidence]",
    "[Figure/Table evidence]",
    "[Author claim]",
    "[Agent inference]",
    "[Uncertain]",
    "[Needs verification]",
]
WEAK_MODES = {"abstract_only", "screenshot_only"}

# Strings used in many places — keep in one dict per language for easy
# review and translation.
T = {
    "zh-CN": {
        "header": "# Agent Fill Pack — paper-three-pass-reader",
        "step_label": "步骤",
        "goal": "目标",
        "allowed": "允许使用的材料",
        "forbidden": "不允许做什么",
        "fields": "要填哪些 JSON 字段",
        "evidence_rules": "Evidence label 规则",
        "output": "输出格式",
        "stop": "Stop condition",
        "fields_to_fill": "需要填的字段",
        "version": "v0.2.1-alpha",
        "ts_label": "生成时间",
    },
    "en": {
        "header": "# Agent Fill Pack — paper-three-pass-reader",
        "step_label": "Step",
        "goal": "Goal",
        "allowed": "Allowed materials",
        "forbidden": "Forbidden",
        "fields": "JSON fields to fill",
        "evidence_rules": "Evidence label rules",
        "output": "Output format",
        "stop": "Stop condition",
        "fields_to_fill": "Fields to fill",
        "version": "v0.2.1-alpha",
        "ts_label": "Generated at",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_weak(mode: str) -> bool:
    return mode in WEAK_MODES


def _common_block(step_no: int, title: str, lang: str) -> str:
    t = T[lang]
    return f"# {step_no:02d}. {title}\n\n- {t['version']}\n\n"


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body}\n\n"


def write_fill_pack(*, run_dir: Path, work_json: Path, draft: dict,
                    out_dir: Path, agent_profile: str = "default",
                    language: str = "zh-CN",
                    max_claims: int = 8, max_figures: int = 6) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if language not in ("zh-CN", "en"):
        language = "zh-CN"

    pm = draft.get("paper_metadata") or {}
    iq = draft.get("intake_quality") or {}
    reading_mode = pm.get("reading_mode") or "partial_text"
    input_kind = iq.get("input_kind") or pm.get("source_kind") or "unknown"
    confidence = iq.get("confidence") or "low"
    needs_confirmation = bool(iq.get("needs_confirmation"))
    weak = _is_weak(reading_mode)

    if language == "zh-CN":
        files = _zh_files(reading_mode, input_kind, confidence,
                          needs_confirmation, weak, agent_profile,
                          max_claims, max_figures, work_json, draft)
    else:
        files = _en_files(reading_mode, input_kind, confidence,
                          needs_confirmation, weak, agent_profile,
                          max_claims, max_figures, work_json, draft)

    for name, content in files.items():
        (out_dir / name).write_text(content, encoding="utf-8")

    # JSON artifacts.
    _write_prompts(out_dir, language, reading_mode, input_kind, agent_profile,
                   max_claims, max_figures)
    _write_field_checklist(out_dir, draft, language)
    _write_draft_status(out_dir, draft, language)


# ---------- Chinese content ----------

def _zh_files(reading_mode, input_kind, confidence, needs_confirmation,
              weak, agent_profile, max_claims, max_figures,
              work_json, draft) -> "dict[str, str]":
    files = OrderedDict()

    files["00_README.md"] = f"""# Agent Fill Pack — paper-three-pass-reader

> 这个目录 (`fill-pack/`) 是由 `run_paper_reading.py --fill-pack` 自动生成的**任务包**，不是阅读结果。
> 它的目标是把 `work/paper_reading.json` 中的 `[DRAFT]` 占位符逐字段填满，变成一份可发布的论文阅读页面。

## 当前 run 状态

| 项 | 值 |
| --- | --- |
| slug | `{work_json.parent.parent.name}` |
| `paper_reading.json` 路径 | `{work_json}` |
| `input_kind` | `{input_kind}` |
| `reading_mode` | `{reading_mode}` |
| `confidence` | `{confidence}` |
| `needs_confirmation` | `{needs_confirmation}` |
| agent profile | `{agent_profile}` |
| max_claims | `{max_claims}` |
| max_figures | `{max_figures}` |

## 哪些部分已经可做

- Stage 0 intake/resolution：runner 已经写了 `paper_metadata` + `intake_quality` + `source_resolution`。
- One / three / ten sentence summary：可以基于 abstract（如果存在）写**草稿**，但必须保留 `[Author claim]` / `[Needs verification]`。
- Pass 1 (Five Cs)：基于 metadata + abstract 通常已经可以写**骨架**。

## 哪些部分不可做

- Pass 2 main ideas / method summary / Pass 3 reconstruction：**只有在 `reading_mode == full_text` 时才能完整写**。
- Claims-Evidence Map：弱输入下每条 claim 必须带 `[Author claim]` / `[Uncertain]` / `[Needs verification]`。
- Reproduction plan：弱输入下只能写"待补"，不能编造。

## 如何一步步填 `work/paper_reading.json`

按编号顺序打开本目录下的 markdown，每读完一个 step，修改 `work/paper_reading.json` 对应字段。

1. `01_stage0_intake_resolution.md` — 校对 input 解析是否正确。
2. `02_pass1_five_cs.md` — 写 Five Cs。
3. `03_pass2_main_ideas.md` — 写 Pass 2 main ideas（弱输入下保留 `[DRAFT]`）。
4. `04_claims_evidence_map.md` — 写 claims + evidence。
5. `05_figures_tables.md` — 写 figure/table 解释。
6. `06_pass3_reconstruction.md` — 写 method reconstruction。
7. `07_critical_review.md` — 写 critical review + limitations。
8. `08_reproduction_plan.md` — 写 reproduction plan。
9. `09_finalize_json.md` — 校对整份 JSON。
10. `10_quality_gate.md` — 重新跑 audit + render。

## 重新 render

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \\
  --input {work_json} \\
  --output {work_json.parent.parent}/paper-reading-output
```

## 重新 audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
  --input {work_json} --json-output {work_json.parent}/audit_result.json
```

## 发布到 GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \\
  --output {work_json.parent.parent}/paper-reading-output \\
  --repo conanxin/paper-reading-pages \\
  --branch gh-pages \\
  --message "Publish {work_json.parent.parent.name}"
```

> 不要在没有真实阅读过论文之前发布。弱输入可以发布，但页面顶部 reading mode badge 必须如实显示 `{reading_mode}`。

## 不允许做的事

- 不要把 `[Author claim]` / `[Uncertain]` 改成 `[Paper evidence]` —— 这就是 audit 会发现的不诚实。
- 不要在没有 body 的情况下写出 "Pass 3 reconstruction was performed" 这种句子。
- 不要扩大成 SaaS / 自动论文总结 / 接入外部 LLM API。
"""

    # 01 Stage 0
    files["01_stage0_intake_resolution.md"] = f"""# 01. Stage 0 — Intake and Resolution

## 目标

校对 Stage 0 解析是否正确：这份输入到底是不是那篇论文？是不是合法 arXiv ID / DOI？是否需要人工确认 canonical paper？

## 允许使用的材料

- 本目录 `input/input.md` 里捕获的原始输入。
- 联网搜索 arXiv / DOI / OpenReview / 出版方页面（仅用于**确认 canonical**，不下载 body）。
- runner hint（如果存在）。

## 不允许做什么

- 不要直接下载 PDF / 提取全文。runner 不做自动 deep-read。
- 不要把含糊 clue 自动当成 canonical paper。如果 `needs_confirmation = true`，必须显式标注。

## 要填的字段

- `paper_metadata.title` — 校对为 canonical title（arXiv 上显示的那个）。
- `paper_metadata.authors` — 与 arXiv 一致。
- `paper_metadata.year` — 首次公开年。
- `paper_metadata.identifiers.arxiv_id` — `None` 或形如 `"1706.03762"`。
- `paper_metadata.identifiers.doi` — `None` 或形如 `"10.xxxx/xxxx"`。
- `intake_quality.ambiguities` — 写下任何 disambiguation 问题。
- `intake_quality.source_resolution` — 每一步解析写成单独一行。

## Evidence label 规则

Stage 0 阶段的来源标注用纯文本即可，不需要 `[Paper evidence]`。但 `intake_quality` 里写"我们如何确认这篇就是 canonical"时，可以标注 `[Author claim]`（来源是 arXiv 页）或 `[Needs verification]`（来源是社交媒体线索）。

## 输出格式

直接在 `work/paper_reading.json` 里修改对应字段。**不要**把 `[DRAFT]` 占位符留在这里。

## Stop condition

- `intake_quality.needs_confirmation = false`，并且
- `paper_metadata.title` 与 arXiv 页完全一致。
"""

    # 02 Five Cs (Pass 1)
    p1_caveat = ""
    if weak:
        p1_caveat = """
> **弱输入提醒**：`reading_mode = {reading_mode}`，没有 body。Five Cs 只能基于 abstract + metadata 写**骨架**。`correctness` / `clarity` 这两项要诚实标 `[Needs verification]`。
""".format(reading_mode=reading_mode)
    files["02_pass1_five_cs.md"] = f"""# 02. Pass 1 — Five Cs

## 目标

写完 Five Cs：Category / Context / Correctness / Contributions / Clarity。

## 允许使用的材料

- abstract（如果 input 含 abstract）。
- title + authors + venue + field。
- 如果 `reading_mode == full_text`，允许读 introduction / conclusion。
{p1_caveat}
## 不允许做什么

- 不要在 `correctness` 字段里说"论文实验全部正确"——除非你真的核对了实验部分。
- 不要把 author 在 abstract 中**声称**的贡献直接当作已验证贡献。
- 不要在没有 references 的情况下，写出"本文是第一个提出 X 的论文"。

## 要填的字段

```json
"five_cs": {{
  "category": "<1-2 句：论文类型>",
  "context": "<2-4 句：研究背景 + 与已有工作的关系>",
  "correctness": "<1-3 句：方法 / 实验 / 论证是否成立 + evidence label>",
  "contributions": ["<贡献 1>", "<贡献 2>", ...],
  "clarity": "<1-3 句：写作 / 结构 / 图表清晰度 + evidence label>"
}}
```

## Evidence label 规则

| 字段 | 弱输入下默认 label | full_text 下默认 label |
| --- | --- | --- |
| `category` | `[Author claim]` | `[Paper evidence]` |
| `context` | `[Author claim]` | `[Paper evidence]` |
| `correctness` | `[Needs verification]` | `[Paper evidence]` 或 `[Agent inference]` |
| `contributions` | `[Author claim]` | `[Author claim]`（作者自述） |
| `clarity` | `[Needs verification]` | `[Paper evidence]` 或 `[Agent inference]` |

## Stop condition

- 五个字段全部非空。
- `correctness` 和 `clarity` 必须含 evidence label。
"""

    # 03 Pass 2 main ideas
    p2_caveat = ""
    if weak:
        p2_caveat = """
> **弱输入提醒**：`reading_mode = {reading_mode}`。Pass 2 main ideas 只能在 abstract 范围内写。**不要**写出"我们读了 Section 3.2，发现 X"这种假装读过 body 的句子。如果 abstract 没提到 main idea，留 `[DRAFT]` 并在 `notes` 里说明。
""".format(reading_mode=reading_mode)
    files["03_pass2_main_ideas.md"] = f"""# 03. Pass 2 — Main Ideas

## 目标

写出论文的主要 idea（最多 3-5 条），以及方法的核心机制。

## 允许使用的材料

- abstract（必须）。
- introduction / conclusion / figures（仅 `full_text`）。
{p2_caveat}
## 不允许做什么

- 不要编造方法细节。如果 abstract 没描述，留 `[DRAFT]`。
- 不要把 author 在 future work 里写的设想当作 main idea。

## 要填的字段

```json
"pass2": {{
  "main_ideas": ["<idea 1>", "<idea 2>", ...],
  "method_summary": "<1-3 句：方法核心机制>",
  ...
}}
```

## Evidence label 规则

- `main_ideas[i]`：弱输入 → `[Author claim]`；full_text → `[Paper evidence]` + section 编号。
- `method_summary`：弱输入 → `[Author claim]`；full_text → `[Paper evidence]` + equation / section 编号。

## Stop condition

- 至少有 1 条 `main_ideas`。
- `method_summary` 长度 >= 30 字符。
"""

    # 04 Claims-Evidence Map
    files["04_claims_evidence_map.md"] = f"""# 04. Claims → Evidence Map

## 目标

为论文中重要 claim 写一条 claim-evidence 条目。**每条 claim 必须有 evidence_label**。

## 允许使用的材料

- abstract / introduction / experiments / figures / tables（按 `reading_mode` 决定）。
- 弱输入下：abstract 提到的每个数字 / 性能 / 主张都算一条候选 claim。

## 不允许做什么

- 不要把 `[Agent inference]` 写成 `[Paper evidence]`。
- 弱输入下不要写超过 `{max_claims}` 条 claim（runner 默认上限）。
- 不要给 claim 编号 `C-DRAFT-xxx`——runner 已经在 draft 里放了一个示例，**全部替换**。

## 要填的字段

```json
"claims_evidence_map": [
  {{
    "claim_id": "C-001",
    "claim_text": "<claim 的精确措辞>",
    "evidence_label": "[Paper evidence] | [Figure/Table evidence] | [Author claim] | [Agent inference] | [Uncertain] | [Needs verification]",
    "evidence_location": "<section / figure / table / abstract>",
    "evidence_kind": "paper_text | paper_figure | paper_table | author_claim | external_knowledge | none",
    "confidence": "high | medium | low",
    "notes": "<为什么是这个 label>",
    "needs_verification": true | false
  }},
  ...
]
```

## Evidence label 规则（核心）

| Label | 含义 | 弱输入下可用？ |
| --- | --- | --- |
| `[Paper evidence]` | 论文 body 明确写了 | 否 |
| `[Figure/Table evidence]` | 论文图表明确显示 | 否 |
| `[Author claim]` | 作者在 abstract/conclusion 自述 | 是 |
| `[Agent inference]` | agent / reader 推断 | 是（但要说明依据） |
| `[Uncertain]` | 不能确定 | 是 |
| `[Needs verification]` | 需要再查 | 是 |

> **关键纪律**：弱输入下，`[Paper evidence]` 和 `[Figure/Table evidence]` 通常**不可用**——因为你没读过 body / 没看图。所有这些 claim 都要降级为 `[Author claim]` / `[Uncertain]` / `[Needs verification]`。

## Stop condition

- claim 数量：full_text ≥ 5，弱输入 1-{max_claims}。
- 每条 claim 都有 `evidence_label` 且 label 在白名单内。
"""

    # 05 Figures / Tables
    files["05_figures_tables.md"] = f"""# 05. Figures and Tables

## 目标

为论文中的每个关键 figure / table 写一条 explanation 条目。

## 允许使用的材料

- 弱输入下：abstract 提到的 figure / table 编号 + title。
- full_text 下：实际看 figure / table。

## 不允许做什么

- 不要解释你没看过的 figure。
- 弱输入下，`[Figure/Table evidence]` 不可用——所有条目都用 `[Author claim]` / `[Needs verification]`。

## 要填的字段

```json
"figures_tables": [
  {{
    "id": "F-1",
    "kind": "figure | table",
    "label": "<Figure 1: ...>",
    "explanation": "<这张图说明了什么>",
    "evidence_label": "[Author claim] | [Needs verification] | ...",
    "notes": "<可选>"
  }},
  ...
]
```

## Stop condition

- 弱输入下：0-{max_figures} 条，每条 evidence_label ∈ {{`[Author claim]`, `[Needs verification]`, `[Uncertain]`}}。
- full_text 下：实际 figure 数。
"""

    # 06 Pass 3 reconstruction
    p3_caveat = ""
    if weak:
        p3_caveat = """
> **弱输入提醒**：`reading_mode = {reading_mode}`。Pass 3 method reconstruction **不能**填——保留 `[DRAFT]`，并在 audit 里承认是 `unavailable_due_to_reading_mode`。
""".format(reading_mode=reading_mode)
    files["06_pass3_reconstruction.md"] = f"""# 06. Pass 3 — Method Reconstruction

## 目标

用自己的话把方法重建一遍：input → algorithm → output。要让一个没读过论文的人能复述。
{p3_caveat}
## 允许使用的材料

- full_text：method / algorithm / equations / appendix。
- 弱输入：abstract 范围。

## 要填的字段

```json
"pass3": {{
  "method_reconstruction": ["<step 1>", "<step 2>", ...],
  "hidden_assumptions": ["<assumption 1>", ...],
  ...
}}
```

## Stop condition

- full_text：`method_reconstruction` 至少 3 步。
- 弱输入：保留 `[DRAFT]`，并在 `notes` / `intake_quality.missing_fields` 里写明。
"""

    # 07 Critical review
    files["07_critical_review.md"] = f"""# 07. Critical Review

## 目标

写 critical review + limitations + hidden assumptions + future work。

## 要填的字段

```json
"pass3": {{
  "critical_review": ["<critique 1>", ...],
  "hidden_assumptions": ["<assumption 1>", ...],
  "limitations": ["<limitation 1>", ...],
  "future_work": ["<future direction 1>", ...],
  "application_notes": ["<how to apply 1>", ...]
}}
```

## Evidence label 规则

- `critical_review` / `limitations` / `hidden_assumptions`：默认 `[Agent inference]` + 说明依据。
- `future_work`：默认 `[Author claim]`（作者自述）或 `[Agent inference]`。
- `application_notes`：默认 `[Agent inference]`。

## Stop condition

- 至少 1 条 `critical_review`，至少 1 条 `limitations`。
"""

    # 08 Reproduction plan
    files["08_reproduction_plan.md"] = f"""# 08. Reproduction Plan

## 目标

写一份最小可执行 reproduction plan：data + baseline + hardware + steps + sanity checks + success criteria。

## 允许使用的材料

- 实验部分（仅 full_text）。
- GitHub repo（如果存在）。
- 弱输入：仅 abstract 提到的 dataset / metric 名称。

## 要填的字段

```json
"reproduction_plan": {{
  "dataset": "<name + 链接>",
  "baseline": "<baseline name>",
  "hardware": "<GPU/CPU/RAM>",
  "steps": ["<step 1>", ...],
  "sanity_checks": ["<check 1>", ...],
  "success_criteria": ["<criterion 1>", ...]
}}
```

## Stop condition

- full_text：dataset + baseline + steps 全部非空。
- 弱输入：保留 `[DRAFT]` 或写"待补"。
"""

    # 09 Finalize JSON
    files["09_finalize_json.md"] = f"""# 09. Finalize JSON

## 目标

校对 `work/paper_reading.json` 整体质量，准备 audit + render。

## 检查清单

- [ ] 所有 `[DRAFT]` 已替换（保留在 Pass 2/3 在弱输入下的合法 `[DRAFT]` 除外）。
- [ ] `paper_metadata.reading_mode` 与实际阅读情况一致。
- [ ] `intake_quality.needs_confirmation = false`，除非确实还有歧义。
- [ ] `claims_evidence_map` 每条 claim 都有 `evidence_label`，且 label ∈ 白名单。
- [ ] 弱输入下没有 `[Paper evidence]` / `[Figure/Table evidence]`（这是 audit 会标 FAIL 的）。
- [ ] `final_checklist` 至少 5 条；full_text ≥ 8 条。
- [ ] `glossary` 至少 3 条（除非论文领域陌生术语极少）。

## 跑 audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
  --input work/paper_reading.json \\
  --json-output work/audit_result.json
```

audit status 必须是 `PASS` 才能继续到 render / publish。

## Stop condition

- audit status = PASS。
"""

    # 10 Quality gate
    files["10_quality_gate.md"] = f"""# 10. Quality Gate

## 目标

最终质量门：audit + render + （可选）publish。

## 命令

```bash
# 1. Audit
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
  --input work/paper_reading.json

# 2. Render
python3 skills/paper-three-pass-reader/scripts/render_page.py \\
  --input work/paper_reading.json \\
  --output paper-reading-output

# 3. Publish（可选）
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \\
  --output paper-reading-output \\
  --repo conanxin/paper-reading-pages \\
  --branch gh-pages \\
  --message "Publish <slug>"
```

## Quality bar

- audit status = **PASS**。
- `index.html` 打开后 Five Cs / Claims-Evidence / Pass 1/2/3 / Final Checklist 全部可见。
- reading mode badge 与 JSON 一致。
- 所有 evidence label 至少有一个 `[Author claim]` / `[Paper evidence]` / `[Figure/Table evidence]` / `[Agent inference]` / `[Uncertain]` / `[Needs verification]` 之一。

## Stop condition

- audit PASS。
- index.html 生成。
- 如 publish：远端 URL HTTP 200。
"""

    return files


# ---------- English content (parallel structure) ----------

def _en_files(reading_mode, input_kind, confidence, needs_confirmation,
              weak, agent_profile, max_claims, max_figures,
              work_json, draft) -> "dict[str, str]":
    # Most English content mirrors the zh-CN content with English headings.
    # We keep the full set of files to make sure language='en' is symmetric.
    files = OrderedDict()

    files["00_README.md"] = _en_readme(reading_mode, input_kind, confidence,
                                        needs_confirmation, agent_profile,
                                        max_claims, max_figures, work_json)
    files["01_stage0_intake_resolution.md"] = _en_step(
        1, "Stage 0 — Intake and Resolution", weak,
        "Confirm Stage 0 parsing is correct. Is this actually the canonical paper? "
        "Is the arXiv ID / DOI valid? Does `needs_confirmation` need to flip to false?",
        ["The original input in `input/input.md`.",
         "External lookup of arXiv / DOI / OpenReview / publisher (for *confirmation* only — do not download the body).",
         "Runner resolver hint (if any)."],
        ["Do not download the PDF or extract full text. The runner does not auto deep-read.",
         "Do not auto-promote an ambiguous clue into a canonical paper. If `needs_confirmation = true`, keep it true."],
        ["paper_metadata.title", "paper_metadata.authors", "paper_metadata.year",
         "paper_metadata.identifiers.arxiv_id", "paper_metadata.identifiers.doi",
         "intake_quality.ambiguities", "intake_quality.source_resolution"],
        "Stage 0 evidence is plain prose; only `intake_quality` sources may carry labels.",
        "Edit `work/paper_reading.json` directly. No `[DRAFT]` should remain in this stage.",
        "intake_quality.needs_confirmation = false AND paper_metadata.title matches arXiv exactly.",
    )

    p1_extra = ""
    if weak:
        p1_extra = (f"\n> **Weak-input note**: `reading_mode = {reading_mode}`. "
                    "Five Cs can only be a *skeleton* based on abstract + metadata. "
                    "`correctness` / `clarity` should carry `[Needs verification]`.\n")
    files["02_pass1_five_cs.md"] = _en_step(
        2, "Pass 1 — Five Cs", weak,
        "Write Five Cs: Category / Context / Correctness / Contributions / Clarity.",
        ["Abstract (if present).", "Title + authors + venue + field.",
         "If `reading_mode == full_text`, introduction / conclusion are allowed." + p1_extra],
        ["Don't claim 'all experiments are correct' unless you actually checked the experimental section.",
         "Don't take an author's abstract claim as verified contribution.",
         "Don't write 'this is the first paper to propose X' without checking references."],
        ["five_cs.category", "five_cs.context", "five_cs.correctness",
         "five_cs.contributions", "five_cs.clarity"],
        ("Weak mode defaults: category/context → [Author claim]; correctness/clarity → [Needs verification].\n"
         "Full-text defaults: paper_text → [Paper evidence]; inferences → [Agent inference]."),
        "All five fields non-empty; correctness and clarity carry an evidence label.",
        "All five fields filled with at least one sentence each.",
    )

    p2_extra = ""
    if weak:
        p2_extra = (f"\n> **Weak-input note**: `reading_mode = {reading_mode}`. "
                    "Pass 2 main ideas can only use the abstract range. Do NOT write "
                    "'we read Section 3.2 and found X'. If the abstract does not name the idea, "
                    "leave `[DRAFT]` and explain in `notes`.\n")
    files["03_pass2_main_ideas.md"] = _en_step(
        3, "Pass 2 — Main Ideas", weak,
        "Write the paper's main ideas (3-5 max) and the core mechanism of the method.",
        ["Abstract (required).", "Introduction / conclusion / figures (only if full_text)."] + ([p2_extra] if p2_extra else []),
        ["Don't fabricate method details. If the abstract doesn't say, leave `[DRAFT]`.",
         "Don't treat author future work as main ideas."],
        ["pass2.main_ideas", "pass2.method_summary"],
        ("weak → [Author claim]; full_text → [Paper evidence] + section number."),
        "main_ideas length >= 1; method_summary length >= 30 chars.",
        "Both fields non-empty.",
    )

    files["04_claims_evidence_map.md"] = _en_step(
        4, "Claims → Evidence Map", weak,
        "Write one claim-evidence entry for each important claim. Every claim must have an evidence_label.",
        ["Abstract / introduction / experiments / figures / tables (per reading_mode).",
         "In weak mode: every number / metric / claim in the abstract is a candidate claim."],
        ["Don't relabel [Agent inference] as [Paper evidence].",
         f"Don't write more than {max_claims} claims in weak mode.",
         "Don't keep `C-DRAFT-xxx` IDs — replace them all."],
        ["claims_evidence_map[*].claim_id", "claims_evidence_map[*].claim_text",
         "claims_evidence_map[*].evidence_label", "claims_evidence_map[*].evidence_location",
         "claims_evidence_map[*].confidence"],
        ("Valid labels: [Paper evidence], [Figure/Table evidence], [Author claim], "
         "[Agent inference], [Uncertain], [Needs verification].\n"
         "Weak mode: [Paper evidence] and [Figure/Table evidence] are NOT available."),
        "full_text ≥ 5 claims; weak mode 1-{max_claims}. All labels in whitelist.".format(max_claims=max_claims),
        "Every claim has a label and the audit confirms the whitelist.",
    )

    files["05_figures_tables.md"] = _en_step(
        5, "Figures and Tables", weak,
        "For each key figure / table, write an explanation entry.",
        ["Weak mode: figure/table numbers and titles from abstract.",
         "Full-text mode: actual figures / tables."],
        ["Don't explain a figure you didn't see.",
         "Weak mode: [Figure/Table evidence] is NOT allowed — use [Author claim] / [Needs verification]."],
        ["figures_tables[*].id", "figures_tables[*].kind", "figures_tables[*].label",
         "figures_tables[*].explanation", "figures_tables[*].evidence_label"],
        ("Valid evidence labels per the whitelist. "
         f"Weak mode: 0-{max_figures} entries, each with a label in {{[Author claim], [Needs verification], [Uncertain]}}."),
        f"≤ {max_figures} entries in weak mode; matches actual figure count in full_text.",
        "Each entry has a label in the whitelist.",
    )

    p3_extra = ""
    if weak:
        p3_extra = (f"\n> **Weak-input note**: `reading_mode = {reading_mode}`. "
                    "Pass 3 method reconstruction CANNOT be filled. Keep `[DRAFT]` and "
                    "acknowledge in audit that it is `unavailable_due_to_reading_mode`.\n")
    files["06_pass3_reconstruction.md"] = _en_step(
        6, "Pass 3 — Method Reconstruction", weak,
        "Reconstruct the method in your own words: input → algorithm → output. A non-reader should be able to retell it." + p3_extra,
        ["full_text: method / algorithm / equations / appendix.", "weak: abstract range only."],
        ["Don't claim to have reconstructed details that came from body you didn't read."],
        ["pass3.method_reconstruction", "pass3.hidden_assumptions"],
        "Default label: [Agent inference] with reasoning. weak mode: leave [DRAFT].",
        "full_text: method_reconstruction has at least 3 steps. weak: [DRAFT] remains, with notes explaining.",
        "Reconstruction length adequate for the reading mode.",
    )

    files["07_critical_review.md"] = _en_step(
        7, "Critical Review", weak,
        "Write critical review + limitations + hidden assumptions + future work.",
        ["Your own judgment grounded in the paper + external knowledge."],
        ["Don't borrow limitations from related work without flagging."],
        ["pass3.critical_review", "pass3.hidden_assumptions",
         "pass3.limitations", "pass3.future_work", "pass3.application_notes"],
        "Default label: [Agent inference] with reasoning.",
        "At least 1 critical_review and 1 limitation.",
        "Both fields filled.",
    )

    files["08_reproduction_plan.md"] = _en_step(
        8, "Reproduction Plan", weak,
        "Write a minimal executable reproduction plan: data + baseline + hardware + steps + sanity checks + success criteria.",
        ["Experimental section (full_text only).", "GitHub repo if any.",
         "Weak mode: dataset / metric names from abstract only."],
        ["Don't fabricate hyperparameters. If unknown, write 'unknown — verify from paper'."],
        ["reproduction_plan.dataset", "reproduction_plan.baseline",
         "reproduction_plan.steps", "reproduction_plan.sanity_checks",
         "reproduction_plan.success_criteria"],
        "Default label: [Author claim] for dataset/baseline; [Needs verification] for steps you haven't executed.",
        "full_text: dataset + baseline + steps all non-empty. weak: leave [DRAFT].",
        "All required fields present.",
    )

    files["09_finalize_json.md"] = _en_step(
        9, "Finalize JSON", weak,
        "Audit the whole JSON before render / publish.",
        ["work/paper_reading.json", "audit_result.json (previous run)."],
        ["Don't publish a draft that still has [DRAFT] in stages that should be filled."],
        ["All [DRAFT] placeholders (except legitimate weak-mode Pass 2/3 ones) replaced.",
         "paper_metadata.reading_mode matches reality.",
         "intake_quality.needs_confirmation = false unless there's a real ambiguity.",
         "claims_evidence_map every claim has evidence_label in whitelist.",
         "Weak mode has no [Paper evidence] / [Figure/Table evidence] labels.",
         "final_checklist: ≥ 5 questions; full_text ≥ 8.",
         "glossary: ≥ 3 terms (unless domain is unusual)."],
        "Standard checklist.",
        "Run audit, see status PASS.",
        "audit status = PASS.",
    )

    files["10_quality_gate.md"] = """# 10. Quality Gate

## Goal

Final quality gate: audit + render + (optional) publish.

## Commands

```bash
# 1. Audit
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
  --input work/paper_reading.json

# 2. Render
python3 skills/paper-three-pass-reader/scripts/render_page.py \\
  --input work/paper_reading.json \\
  --output paper-reading-output

# 3. Publish (optional)
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \\
  --output paper-reading-output \\
  --repo conanxin/paper-reading-pages \\
  --branch gh-pages \\
  --message "Publish <slug>"
```

## Quality bar

- audit status = **PASS**.
- `index.html` shows Five Cs / Claims-Evidence / Pass 1/2/3 / Final Checklist.
- Reading mode badge matches the JSON.
- All evidence labels come from the whitelist.

## Stop condition

- audit PASS.
- index.html generated.
- If publish: remote URL HTTP 200.
"""
    return files


def _en_readme(reading_mode, input_kind, confidence, needs_confirmation,
               agent_profile, max_claims, max_figures, work_json) -> str:
    return f"""# Agent Fill Pack — paper-three-pass-reader

> This directory (`fill-pack/`) is an auto-generated **task pack** from
> `run_paper_reading.py --fill-pack`. It is NOT the reading itself.
> Its goal is to help an agent (or human) replace the `[DRAFT]` placeholders in
> `work/paper_reading.json` with real content.

## Current run status

| Field | Value |
| --- | --- |
| slug | `{work_json.parent.parent.name}` |
| paper_reading.json path | `{work_json}` |
| input_kind | `{input_kind}` |
| reading_mode | `{reading_mode}` |
| confidence | `{confidence}` |
| needs_confirmation | `{needs_confirmation}` |
| agent profile | `{agent_profile}` |
| max_claims | `{max_claims}` |
| max_figures | `{max_figures}` |

## What's already doable

- Stage 0 intake/resolution: runner already wrote `paper_metadata`, `intake_quality`, `source_resolution`.
- One / three / ten sentence summaries: can draft from abstract but must keep `[Author claim]` / `[Needs verification]`.
- Pass 1 (Five Cs): can write a skeleton from metadata + abstract.

## What's NOT doable

- Pass 2 main ideas / method summary / Pass 3 reconstruction: only fillable when `reading_mode == full_text`.
- Claims-Evidence Map: every weak-mode claim must carry `[Author claim]` / `[Uncertain]` / `[Needs verification]`.
- Reproduction plan: weak mode can only say "TBD".

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
python3 skills/paper-three-pass-reader/scripts/render_page.py \\
  --input {work_json} \\
  --output {work_json.parent.parent}/paper-reading-output
```

## Re-audit

```bash
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \\
  --input {work_json} --json-output {work_json.parent}/audit_result.json
```

## Publish to GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \\
  --output {work_json.parent.parent}/paper-reading-output \\
  --repo conanxin/paper-reading-pages \\
  --branch gh-pages \\
  --message "Publish {work_json.parent.parent.name}"
```

> Don't publish before you've actually read the paper. Weak input can be published,
> but the page's reading mode badge must show `{reading_mode}` honestly.

## What NOT to do

- Don't relabel `[Author claim]` / `[Uncertain]` to `[Paper evidence]` — the audit will catch it.
- Don't write sentences like "Pass 3 reconstruction was performed" when you have no body.
- Don't expand this into a SaaS / automatic paper summarizer / external LLM API.
"""


def _en_step(step_no: int, title: str, weak: bool,
             goal: str, allowed: list, forbidden: list,
             fields: list, evidence_rules: str,
             output: str, stop: str) -> str:
    out = [f"# {step_no:02d}. {title}", "", "## Goal", "", goal, "",
           "## Allowed materials", ""]
    for a in allowed:
        out.append(f"- {a.strip()}" if a.strip() else "")
    out += ["", "## Forbidden", ""]
    for f in forbidden:
        out.append(f"- {f}")
    out += ["", "## JSON fields to fill", ""]
    for fld in fields:
        out.append(f"- `{fld}`")
    out += ["", "## Evidence label rules", "", evidence_rules, "",
            "## Output format", "", output, "",
            "## Stop condition", "", stop, ""]
    return "\n".join(out)


# ---------- JSON artifacts ----------

def _write_prompts(out_dir: Path, language: str, reading_mode: str,
                   input_kind: str, agent_profile: str,
                   max_claims: int, max_figures: int) -> None:
    if language == "zh-CN":
        prompts = OrderedDict([
            ("language", "zh-CN"),
            ("agent_profile", agent_profile),
            ("reading_mode", reading_mode),
            ("input_kind", input_kind),
            ("max_claims", max_claims),
            ("max_figures", max_figures),
            ("stage0_intake_resolution", OrderedDict([
                ("goal", "校对 Stage 0 解析是否正确，确认 canonical paper。"),
                ("allowed_inputs", ["input/input.md", "arXiv / DOI 页面（仅确认）", "runner hint"]),
                ("forbidden", ["下载 PDF", "自动 deep-read", "把含糊 clue 当成 canonical"]),
                ("fields", ["paper_metadata.title", "paper_metadata.authors",
                            "paper_metadata.identifiers.arxiv_id",
                            "intake_quality.source_resolution"]),
                ("evidence_labels", ["[Author claim]", "[Needs verification]"]),
                ("stop_condition", "needs_confirmation = false 且 title 与 arXiv 完全一致。"),
            ])),
            ("pass1_five_cs", OrderedDict([
                ("goal", "写完 Five Cs：Category / Context / Correctness / Contributions / Clarity。"),
                ("fields", ["five_cs.category", "five_cs.context",
                            "five_cs.correctness", "five_cs.contributions", "five_cs.clarity"]),
                ("evidence_labels_weak", ["[Author claim]", "[Needs verification]"]),
                ("evidence_labels_full", ["[Paper evidence]", "[Agent inference]"]),
                ("stop_condition", "五个字段全部非空。"),
            ])),
            ("pass2_main_ideas", OrderedDict([
                ("goal", "写 main ideas + method summary。"),
                ("fields", ["pass2.main_ideas", "pass2.method_summary"]),
                ("stop_condition", "main_ideas ≥ 1；method_summary ≥ 30 字符。"),
            ])),
            ("claims_evidence_map", OrderedDict([
                ("goal", "为每个重要 claim 写一条 claim-evidence 条目。"),
                ("fields", ["claims_evidence_map"]),
                ("min_claims_full_text", 5),
                ("max_claims_weak", max_claims),
                ("stop_condition", "每条 claim 有 evidence_label 且在白名单内。"),
            ])),
            ("figures_tables", OrderedDict([
                ("goal", "为每个关键 figure/table 写 explanation。"),
                ("fields", ["figures_tables"]),
                ("max_entries_weak", max_figures),
                ("stop_condition", "weak 模式 label ∈ {[Author claim], [Needs verification], [Uncertain]}。"),
            ])),
            ("pass3_reconstruction", OrderedDict([
                ("goal", "用自己话重建方法。"),
                ("fields", ["pass3.method_reconstruction", "pass3.hidden_assumptions"]),
                ("stop_condition", "full_text ≥ 3 步；weak 保留 [DRAFT]。"),
            ])),
            ("critical_review", OrderedDict([
                ("goal", "写 critical review + limitations + hidden assumptions + future work。"),
                ("fields", ["pass3.critical_review", "pass3.limitations",
                            "pass3.hidden_assumptions", "pass3.future_work",
                            "pass3.application_notes"]),
                ("stop_condition", "critical_review ≥ 1；limitations ≥ 1。"),
            ])),
            ("reproduction_plan", OrderedDict([
                ("goal", "写最小可执行 reproduction plan。"),
                ("fields", ["reproduction_plan.dataset", "reproduction_plan.baseline",
                            "reproduction_plan.steps", "reproduction_plan.sanity_checks",
                            "reproduction_plan.success_criteria"]),
                ("stop_condition", "full_text 全非空；weak 保留 [DRAFT]。"),
            ])),
            ("finalize_json", OrderedDict([
                ("goal", "校对整份 JSON。"),
                ("checks", ["[DRAFT] 替换", "evidence_label 合法",
                            "reading_mode 一致", "final_checklist 数量充足",
                            "audit PASS"]),
            ])),
            ("quality_gate", OrderedDict([
                ("goal", "audit + render + 可选 publish。"),
                ("commands", ["audit_paper_reading.py", "render_page.py",
                              "publish_output_to_github.sh (optional)"]),
                ("quality_bar", ["audit status PASS", "index.html 完整",
                                 "reading mode badge 正确"]),
            ])),
        ])
    else:
        prompts = OrderedDict([
            ("language", "en"),
            ("agent_profile", agent_profile),
            ("reading_mode", reading_mode),
            ("input_kind", input_kind),
            ("max_claims", max_claims),
            ("max_figures", max_figures),
            ("stage0_intake_resolution", "Confirm Stage 0 parsing; ensure canonical identification."),
            ("pass1_five_cs", "Write Five Cs: Category / Context / Correctness / Contributions / Clarity."),
            ("pass2_main_ideas", "Write main_ideas + method_summary."),
            ("claims_evidence_map", "Write one entry per important claim with evidence_label."),
            ("figures_tables", "Write explanation entries for key figures/tables."),
            ("pass3_reconstruction", "Reconstruct the method in your own words."),
            ("critical_review", "Write critical_review + limitations + hidden_assumptions + future_work."),
            ("reproduction_plan", "Write minimal executable reproduction plan."),
            ("finalize_json", "Audit the whole JSON before render/publish."),
            ("quality_gate", "Run audit + render; optionally publish."),
        ])
    (out_dir / "prompts.json").write_text(
        json.dumps(prompts, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_field_checklist(out_dir: Path, draft: dict, language: str) -> None:
    """List each major field with status: present / draft / missing /
    unavailable_due_to_reading_mode / needs_verification."""

    reading_mode = (draft.get("paper_metadata") or {}).get("reading_mode") or "partial_text"
    weak = reading_mode in WEAK_MODES

    def status(field_path: str, value, required: bool) -> str:
        if value is None:
            return "missing"
        if isinstance(value, str) and "[DRAFT" in value:
            return "draft"
        if isinstance(value, list):
            if not value:
                return "missing"
            if any(isinstance(x, str) and "[DRAFT" in x for x in value):
                return "draft"
            return "present"
        if isinstance(value, dict):
            if not value:
                return "missing"
            blob = json.dumps(value, ensure_ascii=False)
            if "[DRAFT" in blob:
                return "draft"
            return "present"
        return "present"

    def override(field_path: str, base: str) -> str:
        # In weak mode, some fields are legitimately unavailable.
        if not weak:
            return base
        weak_unavailable = {
            "pass2.method_summary",
            "pass2.figure_table_notes",
            "pass3.method_reconstruction",
            "pass3.critical_review",
            "pass3.hidden_assumptions",
            "pass3.limitations",
            "pass3.future_work",
            "pass3.application_notes",
            "reproduction_plan.steps",
        }
        if field_path in weak_unavailable and base == "draft":
            return "unavailable_due_to_reading_mode"
        return base

    def needs_ver(base: str) -> str:
        return "needs_verification" if base == "draft" else base

    fields = [
        ("paper_metadata.title", (draft.get("paper_metadata") or {}).get("title"), True),
        ("paper_metadata.authors", (draft.get("paper_metadata") or {}).get("authors"), True),
        ("paper_metadata.year", (draft.get("paper_metadata") or {}).get("year"), True),
        ("paper_metadata.identifiers.arxiv_id",
         ((draft.get("paper_metadata") or {}).get("identifiers") or {}).get("arxiv_id"), False),
        ("paper_metadata.reading_mode", reading_mode, True),
        ("intake_quality.confidence",
         (draft.get("intake_quality") or {}).get("confidence"), True),
        ("intake_quality.source_resolution",
         (draft.get("intake_quality") or {}).get("source_resolution"), True),
        ("summaries.one_sentence", (draft.get("summaries") or {}).get("one_sentence"), True),
        ("summaries.three_sentence", (draft.get("summaries") or {}).get("three_sentence"), True),
        ("summaries.ten_sentence", (draft.get("summaries") or {}).get("ten_sentence"), True),
        ("five_cs.category", (draft.get("five_cs") or {}).get("category"), True),
        ("five_cs.context", (draft.get("five_cs") or {}).get("context"), True),
        ("five_cs.correctness", (draft.get("five_cs") or {}).get("correctness"), True),
        ("five_cs.contributions", (draft.get("five_cs") or {}).get("contributions"), True),
        ("five_cs.clarity", (draft.get("five_cs") or {}).get("clarity"), True),
        ("pass1.bird_eye_notes", (draft.get("pass1") or {}).get("bird_eye_notes"), False),
        ("pass1.decision", (draft.get("pass1") or {}).get("decision"), False),
        ("pass2.main_ideas", (draft.get("pass2") or {}).get("main_ideas"), True),
        ("pass2.method_summary", (draft.get("pass2") or {}).get("method_summary"), True),
        ("pass2.figure_table_notes", (draft.get("pass2") or {}).get("figure_table_notes"), False),
        ("pass2.key_references", (draft.get("pass2") or {}).get("key_references"), False),
        ("claims_evidence_map", draft.get("claims_evidence_map"), True),
        ("figures_tables", draft.get("figures_tables"), False),
        ("pass3.method_reconstruction", (draft.get("pass3") or {}).get("method_reconstruction"), True),
        ("pass3.critical_review", (draft.get("pass3") or {}).get("critical_review"), True),
        ("pass3.hidden_assumptions", (draft.get("pass3") or {}).get("hidden_assumptions"), False),
        ("pass3.limitations", (draft.get("pass3") or {}).get("limitations"), True),
        ("pass3.future_work", (draft.get("pass3") or {}).get("future_work"), False),
        ("pass3.application_notes", (draft.get("pass3") or {}).get("application_notes"), False),
        ("reproduction_plan.dataset", (draft.get("reproduction_plan") or {}).get("dataset"), True),
        ("reproduction_plan.baseline", (draft.get("reproduction_plan") or {}).get("baseline"), True),
        ("reproduction_plan.hardware", (draft.get("reproduction_plan") or {}).get("hardware"), False),
        ("reproduction_plan.steps", (draft.get("reproduction_plan") or {}).get("steps"), True),
        ("reproduction_plan.sanity_checks", (draft.get("reproduction_plan") or {}).get("sanity_checks"), False),
        ("reproduction_plan.success_criteria", (draft.get("reproduction_plan") or {}).get("success_criteria"), False),
        ("glossary", draft.get("glossary"), False),
        ("open_questions", draft.get("open_questions"), False),
        ("final_checklist", draft.get("final_checklist"), True),
    ]

    items = []
    for path, val, required in fields:
        base = status(path, val, required)
        final = override(path, base)
        items.append(OrderedDict([
            ("field", path),
            ("required", required),
            ("status", final),
            ("needs_verification", final in ("draft", "unavailable_due_to_reading_mode")),
        ]))

    checklist = OrderedDict([
        ("language", language),
        ("reading_mode", reading_mode),
        ("generated_at", _now_iso()),
        ("summary", OrderedDict([
            ("present", sum(1 for i in items if i["status"] == "present")),
            ("draft", sum(1 for i in items if i["status"] == "draft")),
            ("missing", sum(1 for i in items if i["status"] == "missing")),
            ("unavailable_due_to_reading_mode",
             sum(1 for i in items if i["status"] == "unavailable_due_to_reading_mode")),
            ("needs_verification",
             sum(1 for i in items if i["needs_verification"])),
        ])),
        ("items", items),
    ])
    (out_dir / "field_checklist.json").write_text(
        json.dumps(checklist, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_draft_status(out_dir: Path, draft: dict, language: str) -> None:
    """Aggregate draft_status.json with recommended_next_action."""
    reading_mode = (draft.get("paper_metadata") or {}).get("reading_mode") or "partial_text"
    fc = (out_dir / "field_checklist.json")
    summary = {"present": 0, "draft": 0, "missing": 0,
               "unavailable_due_to_reading_mode": 0, "needs_verification": 0}
    if fc.exists():
        try:
            fc_doc = json.loads(fc.read_text(encoding="utf-8"))
            summary = fc_doc.get("summary") or summary
        except Exception:
            pass

    cem = draft.get("claims_evidence_map") or []
    claims_with_verification = sum(
        1 for c in cem
        if isinstance(c, dict)
        and c.get("evidence_label") in ("[Needs verification]", "[Uncertain]")
    )

    if reading_mode in WEAK_MODES:
        recommended = (
            "1. Run `audit_paper_reading.py` to confirm structural PASS.\n"
            "2. Fill Pass 1 (Five Cs) using only abstract + metadata. Use "
            "`[Author claim]` / `[Needs verification]` for correctness / clarity.\n"
            "3. Fill claims_evidence_map with up to `max_claims` entries, all "
            "with weak-mode labels.\n"
            "4. To upgrade to full_text: place the body text in "
            "`runs/<slug>/extracted/` and re-run the runner with "
            "`--reading-mode full_text`."
        )
    elif summary["draft"] > 0 or summary["missing"] > 0:
        recommended = (
            "1. Open `fill-pack/01_stage0_intake_resolution.md` and work through "
            "each step in order.\n"
            "2. Replace remaining [DRAFT] placeholders in `work/paper_reading.json`.\n"
            "3. Re-run `audit_paper_reading.py` until status = PASS.\n"
            "4. Re-run `render_page.py` and (optionally) publish."
        )
    else:
        recommended = (
            "1. Re-run `audit_paper_reading.py` to confirm PASS.\n"
            "2. Render with `render_page.py`.\n"
            "3. Optionally publish to GitHub Pages."
        )

    can_render = True  # render_page.py is forgiving; audit gate is the real one.
    can_publish = True

    doc = OrderedDict([
        ("language", language),
        ("generated_at", _now_iso()),
        ("input_kind", (draft.get("paper_metadata") or {}).get("source_kind")),
        ("reading_mode", reading_mode),
        ("confidence", (draft.get("intake_quality") or {}).get("confidence")),
        ("needs_confirmation", (draft.get("intake_quality") or {}).get("needs_confirmation")),
        ("counts", OrderedDict([
            ("draft_fields_count", summary["draft"]),
            ("missing_fields_count", summary["missing"]),
            ("unavailable_due_to_reading_mode_count",
             summary["unavailable_due_to_reading_mode"]),
            ("needs_verification_count", summary["needs_verification"]),
            ("claims_total", len(cem)),
            ("claims_with_verification_or_uncertain", claims_with_verification),
        ])),
        ("can_render", can_render),
        ("can_publish", can_publish),
        ("recommended_next_action", recommended),
    ])
    (out_dir / "draft_status.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
