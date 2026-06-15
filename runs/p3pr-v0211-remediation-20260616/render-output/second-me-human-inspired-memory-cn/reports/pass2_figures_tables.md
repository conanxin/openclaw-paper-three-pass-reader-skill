# Pass 2 — Figures & Tables

### Figure  — (missing title)

展示 L0/L1/L2 混合架构，含内循环（层间无缝整合）和外循环（在 SECOND ME 指导下的 LLM 和互联网资源）。建立了论文其余部分详细说明的高层系统布局。 [Paper evidence, caption after §1]

### Figure  — (missing title)

端到端训练流水线的可视化：原始数据 → 实体/主题挖掘 → 记忆数据合成（自我定位强化、记忆认知增强）→ 通过模拟场景生成上下文增强/批判数据 → 五级过滤 → PEFT SFT → DPO 数据生成 → 评估。'LLM as Judge' 和 'LLM as data synthesizer' 标签强调自动化。 [Paper evidence, §3.1]

### Figure  — (missing title)

对 'When you think of me, what do you see?' 的 Weak / Multi-step / Strong COT 回答并排展示。展示从 Weak 到 Strong COT 的丰富度和风格约束递增，并支撑作者在 §3.5 中报告的质量差异。 [Paper evidence, §3.2]

### Figure  — (missing title)

Context-Enhance 任务的具体案例 1：关于两阶段模型训练初学者资源的查询。对比 Weak COT 与 Strong COT，用户记录中的实体以粗体标记。用于论证 Strong COT 的定性优势。 [Paper evidence, §3.5]

### Figure  — (missing title)

展示训练后的 L2 如何位于用户和专家模型（GPT-4o 等）之间，箭头表示可能的通信（用户-专家箭头为清晰起见省略）。支撑 §4 应用场景和 §3.1 多 Agent 叙事。 [Paper evidence, Appendix D]

### Table  — (missing title)

Strong / Multi-step / Weak COT 下的 Memory (Self) / Memory (Third-party) / Context Enhance / Context Critic 得分。报告数值（均值，0-1 尺度）：Strong 0.91/0.71/0.75/0.85；Multi-step 0.64/0.43/0.85/0.77；Weak 0.86/0.58/0.87/0.64。Strong COT 在 Memory (Self) 和 Context Critic 上获胜；Multi-step 总体弱于 Weak。 [Paper evidence, Table 1 + §3.5]

### Table  — (missing title)

在 §3.5 中被引用为显示 DPO 在所有任务上带来显著改进。具体单元格值未被 pdftotext -layout 清晰恢复；提取限制。作者的定性声明是迭代 COT 精炼 + DPO 产生一致增益。 [Paper evidence, §3.5 引用] [Needs verification 具体数值]

