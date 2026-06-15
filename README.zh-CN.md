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

## 版本历史

| Tag | 状态 | 说明 |
|---|---|---|
| `v0.1.0-alpha` | 不可变 | 初始发布。 |
| `v0.1.1-alpha` | 不可变 | 渲染器加固(松 JSON 容忍)+ 多页发布脚本。 |
| `v0.1.2-alpha` | 当前 | 发布脚本修复,保证多页之间互不删除。 |

本项目把已发布的 tag 视为不可变——绝不移动、绝不重写历史。

---

## License

MIT — 见 [`LICENSE`](LICENSE)。

版本:**v0.1.2-alpha**。
