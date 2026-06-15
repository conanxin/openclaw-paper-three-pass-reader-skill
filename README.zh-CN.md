# paper-three-pass-reader（中文）

本地优先的"三遍阅读论文"skill,面向 Hermes / OpenClaw agent 和人类用户。严格按 S. Keshav《How to Read a Paper》(2007) 的三遍阅读法执行,最后产出一个可离线打开、可发布到 GitHub Pages 的交互式 HTML 阅读页。

> 读一次、读对、走的时候带一个能证明"我真的读懂"的可读页面。

---

## 这是什么

一个独立 skill 包,接收**任何"指向某篇论文"的线索**(PDF、arXiv URL、DOI、标题、首页截图、摘要、社交媒体一句话、GitHub repo、topic 关键词),产出:

1. **规范化的论文身份**(Stage 0: 摄入与解析)
2. **第一遍通读 + Five Cs**(Stage 1)
3. **第二遍理解 + 主张-证据映射**(Stage 2)
4. **第三遍重建 + 批判性复现计划**(Stage 3)
5. **自包含的交互式 HTML 阅读页**

纯本地、纯静态、无后端,`file://` 直接打开。

---

## 什么时候用

适合:

- 你拿到一篇论文(或者一个很强的线索),想**真正读懂**而不是简单总结
- 在准备 reading group、literature review、毕业论文、或依赖某篇论文的项目
- 需要一个能反复重读、能分享、能发布的产物(HTML + JSON + Markdown 报告)
- 作为 agent,想要有**显式 evidence 标签**的论文阅读工作流,而不是 vibe-based 总结

不适合:

- 只是想要一段"这篇论文讲啥"的简介——那是 `pdf-to-markdown-pipeline` 或一次 LLM 调用的事

---

## 支持的输入

Stage 0 把以下任意输入归一化成 canonical paper:

| 输入类型 | 示例 |
|---|---|
| `complete_paper` | PDF 文件、完整正文、LaTeX 源、HTML 论文 |
| `paper_url` | arXiv、DOI、出版商(ACM/IEEE/Springer/Nature/ScienceDirect)、OpenReview、PubMed/bioRxiv/medRxiv |
| `paper_identifier` | arXiv ID、DOI、OpenReview ID |
| `paper_title` | "How to Read a Paper" |
| `paper_metadata` | 标题 + 作者 + 年份 + 会议/期刊 |
| `paper_excerpt` | 摘要、引言、结论、BibTeX、citation 文本 |
| `paper_image` / `paper_screenshot` | 印刷页照片、slide 截图、poster 图 |
| `paper_topic` | 方法/模型/数据集/benchmark/作者/会议线索 |
| `project_or_repo` | 配套论文的 GitHub repo 或项目主页 |
| `ambiguous_clue` | 提到某论文的社交媒体 post 或截图 |

每一步都会输出 `intake_quality.json` 和 `reading_mode`,清楚标出当前 skill 是在 **full_text** / **partial_text** / **abstract_only** / **screenshot_only** 哪种模式下工作。

---

## 三遍阅读法(简版)

### 第一遍 — 鸟瞰(5–10 分钟)

- 读**标题、摘要、引言、各节标题、结论、参考文献**
- 扫一遍图表和数学
- 回答 **Five Cs**:
  - **Category** — 这是什么类型的论文?
  - **Context** — 与哪些其它论文相关?
  - **Correctness** — 假设和方法看起来成立吗?
  - **Contributions** — 主要贡献是什么?
  - **Clarity** — 写得清晰吗?
- 显式记录"是否值得继续读"。

### 第二遍 — 理解内容(约 1 小时)

- 仔细读,但**跳过证明**
- 拎出**主要观点、主张、证据、图表**
- 建立**Claims → Evidence map**:每条承重主张都配上支持它的图/表/章节(或标记"待验证")

### 第三遍 — 重建论文(1–4 小时,深度阅读)

- **假设自己是作者**再读一遍:隐含假设、隐藏决策、失败模式
- 产出**方法重建**:如果要复现这篇论文,你会怎么搭?
- 写**批判性 review**:局限性、范围、validity threat、可复现计划

完整定义见 `skills/paper-three-pass-reader/SKILL.md`。

---

## 输出目录

每次运行产出 `paper-reading-output/`:

```
paper-reading-output/
├── README.md
├── index.html
├── assets/{style.css, app.js}
├── data/{intake_quality, candidate_papers, source_resolution,
│         paper_metadata, paper_outline, paper_reading,
│         claims_evidence_map, figures_tables}.json
└── reports/{stage0_intake, pass1_first_pass, pass1_five_cs,
             pass1_reading_decision, pass2_main_ideas,
             pass2_figures_tables, pass2_claims_evidence_map,
             pass2_key_references, pass3_reconstruction,
             pass3_critical_review, pass3_reproduction_plan,
             final_reading_report}.md
```

`index.html` 模块:Hero Summary / Paper Metadata / Intake Status / 1-3-10 句摘要 / Paper Map / Five Cs Dashboard / Pass 1-2-3 Tabs / Claims-Evidence Map(图可过滤)/ Figures & Tables / Glossary / Method Reconstruction / Limitations / Related Work / Reproduction Plan / Open Questions / "Do I understand this paper?" Checklist。

---

## 快速开始

### 渲染示例页(无需联网)

```bash
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input skills/paper-three-pass-reader/examples/sample_paper_reading.json \
  --output paper-reading-output
```

打开 `paper-reading-output/index.html`。

### 为新论文创建空骨架

```bash
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
  --output paper-reading-output \
  --title "Attention Is All You Need"
```

### 发布到 GitHub Pages

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Publish reading page"
```

目标 repo 不存在时,**不会**自动创建,会打印确切的 `gh repo create` 命令后退出。

### 运行 smoke validation

```bash
bash scripts/validate.sh
```

---

## Evidence 纪律

每条解释都打标签:

- `[Paper evidence]` — 直接来自论文
- `[Figure/Table evidence]` — 来自具体图表
- `[Author claim]` — 作者原话,未独立验证
- `[Agent inference]` — agent 的推断,论文里没有
- `[Uncertain]` — 信心低,证据弱
- `[Needs verification]` — 待人工验证

看到承重主张没标签,默认当 `[Needs verification]` 处理。

---

## 当前版本限制(v0.1.1-alpha)

- 内置样例只用了 Keshav 自己的《How to Read a Paper》——元选择。流水线支持任意论文,但仓库只预置了这一个样例。
- Stage 0 是**输入驱动**的,不会自己去抓论文;你需要提供论文或强线索。
- HTML 页是**纯静态**的——无注释持久化、无笔记同步、无共享状态。
- 不内置 PDF 解析、OCR、网页抓取。需要你自己提供文本或 URL。
- 发布脚本刻意做得极简——不会自动回滚、自动重试、自动协调。推送失败请读错误。

## 多页发布(v0.1.1+)

把多篇论文归档到一个 Pages repo,用 slug 模式:

```bash
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output runs/attention-is-all-you-need-20260615/paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --site-path attention-is-all-you-need \
  --page-title "Attention Is All You Need"
```

页面会被复制到 `gh-pages/attention-is-all-you-need/`,repo 根变成一个简洁的索引页(`index.html` + `published_pages.json`),列出所有已发布的论文。每次调用新增/更新一条,其它论文保留。脚本会校验 slug,只允许 `[A-Za-z0-9._-]+`。

> **v0.1.2-alpha 备注:** 多页清理步骤已加固——重新发布一篇论文时,不会删除 `gh-pages` 上的其它论文子目录。已发布的论文保持完整。

---

## Agent Fill Pack + 结构化 audit(v0.2.1-alpha)

runner 现在支持 `--fill-pack` 和 `--audit`。这两个参数让 runner 的产物可以被另一个 agent(或人)直接接续阅读工作。

```bash
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "Attention Is All You Need" \
  --input-kind paper_title \
  --slug myrun \
  --output-root runs/ \
  --reading-mode partial_text \
  --fill-pack --audit --audit-warn-only --render
```

产物:

- `runs/myrun/work/paper_reading.json` — 草稿。
- `runs/myrun/work/audit_result.json` — 完整 audit JSON(status / errors / warnings / recommendations)。
- `runs/myrun/reports/audit_summary.md` — audit 的 markdown 摘要。
- `runs/myrun/fill-pack/` — 11 个 markdown(`00_README.md` 到 `10_quality_gate.md`)+ `prompts.json` + `field_checklist.json` + `draft_status.json`。
- `runs/myrun/paper-reading-output/index.html` — 渲染好的页面(仅在 audit 不 FAIL 时)。

关键行为:

- `--audit` 在 audit status = FAIL 时阻止 `--render` 和 `--publish`。要绕过用 `--audit-warn-only`。
- `--fill-pack` 写出的步骤说明会随 reading_mode 自适应——弱输入下会显式标注"弱输入提醒"。
- `audit_paper_reading.py` 可独立运行:
  ```bash
  python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
    --input runs/myrun/work/paper_reading.json \
    --json-output runs/myrun/work/audit_result.json
  ```

audit 只做**结构 + reading-mode 纪律**检查,不评判论文是否正确。

详见 [`skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md`](skills/paper-three-pass-reader/docs/AGENT_FILL_PACK.md) 和 [`skills/paper-three-pass-reader/docs/AUDIT.md`](skills/paper-three-pass-reader/docs/AUDIT.md)。

---

## 版本历史

| Tag | 状态 | 说明 |
|---|---|---|
| `v0.1.0-alpha` | 不可变 | 初始发布。 |
| `v0.1.1-alpha` | 不可变 | 渲染器加固(松 JSON 容忍)+ 多页发布脚本。 |
| `v0.1.2-alpha` | 不可变 | 发布脚本修复,保证多页之间互不删除。 |
| `v0.2.0-alpha` | 不可变 | 一键 runner:弱输入/完整输入 → 标准 run 目录 + 草稿 JSON + (可选)渲染/发布。 |
| `v0.2.1-alpha` | 不可变 | Agent Fill Pack + 结构化 audit。runner 新增 `--fill-pack`、`--audit`、`--agent-profile`、`--language`、`--max-claims`、`--max-figures`。 |
| `v0.2.2-alpha` | 不可变 | auto-fill 烟测运行 + runner/render 健壮性修复。 |
| `v0.2.3-alpha` | 不可变 | 一等中文 (zh-CN) 输出支持。runner 写入 `target_language` / `ui_language`;渲染器本地化 UI;audit 检查中文内容。 |
| `v0.2.4-alpha` | 不可变 | zh-CN 质量门。不只看"有没有中文",而看"中文是否真的算读完"。捕捉低 CJK 覆盖、英文残留、浅薄 glossary/claims/checklist、full_text 缺 `[Paper evidence]`。已集成到 audit (`--quality-gate`) 和 runner。 |
| `v0.2.5-alpha` | 不可变 | 一行 CLI `p3pr`。`./p3pr arxiv 2503.08102 --zh --full --publish` 跑完整流水线 (runner + fill-pack + audit + quality gate + render + publish)。6 个子命令:arxiv / title / abstract / screenshot / repo / pdf。强制 weak-mode / quality-gate 边界。 |
| `v0.2.6-alpha` | 不可变 | 共享 resolver hints。`data/resolver_hints.json` 成为唯一真源,配合 `scripts/resolver_hints.py` 与 `scripts/resolve_paper_hint.py` 助手。取代 `p3pr.py` 里的 HINTS 与 runner 里的 RESOLVER_HINTS。 |
| `v0.2.7-alpha` | 不可变 | v0.2.6 round-2 硬化,以新 tag 发布 (v0.2.6-alpha 不可变,绝不重指)。新增结构化顶层 `source_resolution`、CLI→runner overlay (`work/resolver_source.json` + `--resolver-source`)、resolver 助手降级行为(助手坏了降为 `ambiguous_clue` 但 run 仍 rc=0 完成)。验证 195/0 PASS。 |
| `v0.2.10-alpha` | 不可变 | 已发布页面回归审计。新增 `audit_published_pages.py` 读取 `published_pages.json`,抓取每页,生成 JSON + Markdown 审计报告,覆盖 template leak、raw dict、旧 footer、弱 zh-CN UI、缺 Resolver Trail、缺 Claims / Glossary、essay 模式回归。`--selftest-dir` 模式接入 `scripts/validate.sh` 第 17 步。首次实测审计 1/9 页面 PASS。验证 225/0 PASS。 |
| `v0.2.12-alpha` | 当前 | 根首页审计豁免。新增 `page_type` 分类(`site_index` / `paper_page` / `manifest` / `unknown`),根首页不再被论文级检查(`missing_resolver_trail` / `missing_claims_section` / `missing_glossary`)误报。严重检查(`template_leak` / `raw_dict` / `old_footer`)在根首页仍生效。新增顶层 `page_type_counts` 与每页 `page_type` 字段;Markdown 报告新增 `## Page Type Summary` 段。新增 `--include-manifest` 旗标。`scripts/validate.sh` 第 18 步用 8 个 selftest fixture + 实站点端到端校验。验证 236/0 PASS。 |
| `v0.2.9-alpha` | 前序 | 打磨 HTML 随笔 / 演讲型页面渲染。renderer 不再泄漏原始 `{'label': ...}` 字典,不再泄漏 `{% else %}` 模板标签,页面 footer 暴露 `generator_version`,essay 模式下 `Reproduction Plan` 切换为 `实践计划`,并使用 `<details>` 实现的折叠面板。Claim ID 与术语表定义正确显示。重新发布 *You and Your Research* 中文页面。验证 220/0 PASS。 |
| `v0.2.8-alpha` | 前序 | 结构化 `source_resolution` 消费者。新增 `source_resolution_utils.py` 作为共享助手;renderer / audit / fill-pack / zh-CN quality gate 全部读取结构化 block;legacy `intake_quality.source_resolution` list 通过在线升级继续支持。验证 210/0 PASS。 |

本项目把已发布的 tag 视为不可变——绝不移动、绝不重写历史。

---

## 一键 runner(v0.2.0-alpha)

`skills/paper-three-pass-reader/scripts/run_paper_reading.py` 把任何"指向某篇论文"的输入(标题、摘要、OCR 转写、repo URL …)转成标准 run 目录 + 草稿 `paper_reading.json` +(可选)渲染好的页面 +(可选)发布的 GitHub Page。

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

runner **不会**替你读论文——它生成的是带 `[DRAFT]` 占位符的草稿,由你(或 agent)填写。它负责强制 reading-mode 纪律、写标准 run 布局、让工作流可重复。完整接口、示例、边界见 [`skills/paper-three-pass-reader/docs/RUNNER.md`](skills/paper-three-pass-reader/docs/RUNNER.md)。

---

## License
MIT — 见 [`LICENSE`](LICENSE)。

版本:**v0.2.12-alpha**。前序:v0.2.10-alpha (不可变,保留以保证可复现)。
