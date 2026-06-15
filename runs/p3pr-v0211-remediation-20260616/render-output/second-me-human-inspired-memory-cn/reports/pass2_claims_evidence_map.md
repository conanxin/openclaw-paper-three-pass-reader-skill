# Pass 2 — Claims → Evidence Map

- **C-001** — SECOND ME 将用户记忆参数化为 L2 模型权重，叠加在 L0（原始数据）和 L1（自然语言记忆）之上。  
  Evidence: [Paper evidence] (§2.1 (LPM 1.0 回顾) + §2.2 (Overall Design))  
  Confidence: high
- **C-002** — SECOND ME 作为'上下文提供者'而非任务执行器，与用户视角对齐。  
  Evidence: [Author claim] (§2.2 — 'we position SECOND ME as a context provider aligned with the user's perspective, rather than a task executor.')  
  Confidence: high
- **C-003** — 训练流水线完全自动化，包含数据合成、五级过滤、PEFT SFT 和 DPO。  
  Evidence: [Paper evidence] (§3.1 (Training Pipeline) + Figure 2)  
  Confidence: high
- **C-004** — 基座模型为 Qwen2.5-7B-Instruct，训练以 PEFT 开始。  
  Evidence: [Paper evidence] (§3.1 — 'Our base model, Qwen2.5-7B-Instruct (Qwen et al., 2025), undergoes automatic training and evaluation.')  
  Confidence: high
- **C-005** — 训练中使用三种答案风格 COT 策略：Weak、Multi-step 和 Strong（后者使用 Deepseek-R1 并施加严格格式约束）。  
  Evidence: [Paper evidence] (§3.2 (Answer Style: COT or Not?))  
  Confidence: high
- **C-006** — DPO 不引入新知识，而是在约 20% 的 SFT 数据上精炼偏好对齐。  
  Evidence: [Paper evidence] (§3.3 — 'Preference pairs constitute approximately 20% of the total SFT training data.')  
  Confidence: high
- **C-007** — 评估使用四个指标：Memory（Self）、Memory（Third-party）、Context Enhance、Context Critic。  
  Evidence: [Paper evidence] (§3.4 + Appendix C)  
  Confidence: high
- **C-008** — Strong COT 显著提升了 Memory（Self）和 Context Critic 性能；Multi-step COT 往往弱于 Weak COT。  
  Evidence: [Paper evidence] (Table 1（提取）: Strong Memory (Self) = 0.91 vs Weak = 0.86 vs Multi-step = 0.64。)  
  Confidence: high
- **C-009** — DPO 在与迭代 COT 精炼结合时，在所有任务上带来显著改进。  
  Evidence: [Paper evidence] (§3.5 — 'Table 2 demonstrates that DPO brings substantial improvements'.)  
  Confidence: medium
- **C-010** — 人工评估报告 Strong-COT-with-DPO 得分接近 1，Strong-COT-without-DPO 平均约 0.95。  
  Evidence: [Author claim] (§3.5 — 'Human evaluation shows Strong COT without DPO achieves an average score of 0.95, while Strong COT with DPO scores close to 1.')  
  Confidence: medium
- **C-011** — SECOND ME 在人机网络中通过梅特卡夫定律驱动 3-5 个数量级的网络效率提升。  
  Evidence: [Author claim] (§4 — 'integration of human and AI nodes increases network efficiency by 3 to 5 orders of magnitude.')  
  Confidence: low
- **C-012** — 完整系统在 github.com/Mindverse/Second-Me 开源（注意：是 Mindverse，不是 mindhive）。  
  Evidence: [Paper evidence] (Abstract + §4 — 'https://github.com/Mindverse/Second-Me'.)  
  Confidence: high
