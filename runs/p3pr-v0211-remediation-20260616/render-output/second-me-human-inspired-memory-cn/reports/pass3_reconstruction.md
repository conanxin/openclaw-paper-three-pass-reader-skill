# Pass 3 — Method Reconstruction

1. 输入：原始用户数据（文本、交互、偏好、简介、记录）以及可选的预训练 LLM 常识。
2. 阶段 A — 合成：提取实体 / 主题 / 关系；通过自我定位强化和记忆认知增强生成 Memory-QA 对；通过模拟场景和多 Agent 交互生成 Context-Enhance 和 Context-Critic 对。
3. 阶段 B — 过滤：五级质量过滤器（Taori 风格）仅保留高质量合成数据。
4. 阶段 C — SFT：在 Qwen2.5-7B-Instruct 上使用 PEFT（Bitfit / LoRA 家族），答案风格从三种 COT 策略之一（Weak / Multi-step / Strong，后者使用 Deepseek-R1 作为专家）抽取。
5. 阶段 D — DPO：从 SFT 模型构建偏好对（~20% SFT 数据）并运行 Direct Preference Optimization 以精炼偏好对齐，不注入新知识。
6. 阶段 E — 编排：推理时，训练后的 L2 在三种部署模式中选择——Memory QA（Self/Third-party）、Context Enhance、Context Critic——并在（复杂任务）情况下路由到外部专家模型（GPT-4o、Deepseek-R1），同时保持用户上下文。
7. 输出：与用户身份、偏好和历史对齐的上下文增强查询、批判和直接回答。
