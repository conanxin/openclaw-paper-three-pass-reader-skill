# 11. zh-CN 中文质量门（v0.2.4+）

## 目标

`audit_paper_reading.py` 只检查 JSON 结构与 reading-mode 纪律。**它不能判断中文解释质量。**
`quality_gate_zh_cn.py` 是为 zh-CN 输出专门加的第二道质量门。它会：

1. 检查 `target_language` / `ui_language` 字段。
2. 统计主要解释字段的中文覆盖率（≥ 50%）。
3. 检测解释字段中是否含过长的英文段落（≥ 30 个连续 ASCII 字符）。
4. 检查 glossary / claims / final_checklist 的最小项数。
5. 检查 full_text 模式下是否真的有 `[Paper evidence]` / `[Figure/Table evidence]` 的主张。
6. 检查 Pass 2 / Pass 3 在 full_text 模式下是否非空。

它**不是** LLM 真理判断，**也不是**翻译质量评分。它是**结构 + 双语纪律**的硬规则。

## 命令

```bash
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input work/paper_reading.json \
  --json-output work/quality_gate_zh_cn.json

# 集成在 audit 里：
python3 skills/paper-three-pass-reader/scripts/audit_paper_reading.py \
  --input work/paper_reading.json \
  --quality-gate

# runner 集成（draft 生成后自动跑）：
python3 skills/paper-three-pass-reader/scripts/run_paper_reading.py \
  --input "..." \
  --input-kind paper_title \
  --slug <slug> \
  --output-root <root> \
  --language zh-CN \
  --fill-pack \
  --quality-gate
```

## 中文质量门要检查什么

- **语言字段**：`target_language == "zh-CN"`（FAIL 条件），`ui_language == "zh-CN"`（WARN）。
- **CJK 覆盖率**：`summaries` / `pass1` / `pass2` / `pass3` / `claims_evidence_map` / `glossary` / `final_checklist` 这些主要解释字段中，至少 50% 包含中文字符（CJK U+4E00–U+9FFF）。
- **英文搬运风险**：单个解释字段里连续 30+ 个 ASCII 字符且无 CJK 字符——可能是从英文 draft 直接粘贴而忘记翻译。
- **Glossary**：≥ 10 项；每项 `definition` 必须含中文（English 术语要配中文解释）。
- **Claims-Evidence Map**：≥ 8 条；每条 `evidence_label` 必须是合法枚举；`claim_text` 或 `comment` 至少一个含中文；full_text 模式下至少有一个 `[Paper evidence]` / `[Figure/Table evidence]`。
- **Final Checklist**：≥ 8 项；每项 `question` 应含中文。
- **Pass depth（full_text 模式）**：`pass2.main_ideas` 与 `pass3.method_reconstruction` 不能为空。
- **Summaries shape**：`one_sentence` 必须存在；`three_sentence` 至少 1 项；`ten_sentence` 至少 5 项非空。

## 如何修复 WARN / FAIL

| 错误 | 修复 |
| --- | --- |
| CJK 覆盖率低 | 把英文解释字段翻译成中文。术语首次出现时保留英文原词并加中文解释。 |
| 单字段内长英文 blob | 该字段是直接搬运英文的，需要翻译。 |
| glossary < 10 | 补充术语表。每条术语应包含：term、definition（含中文）、role_in_paper（可选）。 |
| claims < 8 | 增加 claims。full_text 模式下必须包含基于论文正文的 `[Paper evidence]` claim。 |
| final_checklist < 8 | 增加检查项；用中文写问题。 |
| full_text 全是 `[Author claim]` | 至少要把核心论点标注为 `[Paper evidence]` 并附 `evidence_location`（§X.Y / p.N / Table N / Figure N）。 |
| Pass 2 / Pass 3 空 | 重新走 03-07 步骤：先写 main ideas，再写 method reconstruction。 |

## 为什么 evidence labels 保持英文枚举

evidence labels 是**审计可解析的固定枚举**：`[Paper evidence]`, `[Figure/Table evidence]`, `[Author claim]`, `[Agent inference]`, `[Uncertain]`, `[Needs verification]`。

如果把它们翻译成中文，audit 的 `evidence_label` 校验就会失败。所以：

- **labels 永远用英文**。
- **labels 周围的解释性文字**（例如 `notes` / `comment` / `claim_text`）用中文。
- 论文标题、作者名、方法名、benchmark 名保持原文（英文/中文都按作者写的）。

## 为什么不能只检查"有中文字符"

只检查"有中文字符"会被以下情况骗过：

1. **空中文夹大段英文**：每个字段塞一个"论文"二字，然后整段贴英文。
2. **Glossary 项全是英文术语 + 英文定义**：表面上看起来很专业，但读者是中文用户。
3. **final_checklist 写得很短**（2-3 项），但每项都说"是"——通过率 100%，但质量差。
4. **Pass 2 / Pass 3 留空**（runner draft 默认状态）：如果只看 CJK 字符，"[DRAFT]" 也会被算作 CJK 字段；但事实上是空。
5. **全 `[Author claim]` 却没有 `[Paper evidence]`**：表面上"读了论文"，但实际上没引用论文任何章节。

所以质量门要同时检查：

- **C覆盖**（语言层面）
- **结构深度**（claims / glossary / checklist 数量）
- **证据纪律**（evidence_label 分布 + ground 在 paper / figure）

## 如何重新 render / publish

修复后，按顺序：

```bash
# 1. 重新跑 quality gate
python3 skills/paper-three-pass-reader/scripts/quality_gate_zh_cn.py \
  --input work/paper_reading.json \
  --json-output work/quality_gate_zh_cn.json
# 应该返回 status: PASS，exit code 0

# 2. 重新 render
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input work/paper_reading.json \
  --output paper-reading-output

# 3. 重新 publish
./skills/paper-three-pass-reader/scripts/publish_output_to_github.sh \
  --output paper-reading-output \
  --repo conanxin/paper-reading-pages \
  --branch gh-pages \
  --message "Re-publish <slug> after zh-CN quality fix"
```

## Stop condition

- `quality_gate_zh_cn.py` 返回 `status: PASS`，`exit code: 0`。
- audit `--quality-gate` 集成后，audit 输出里 `[quality_gate_zh_cn]` 段显示 `PASS`。
- index.html 重新生成后所有中文 UI 标签仍在。
- 远端页面 HTTP 200。
