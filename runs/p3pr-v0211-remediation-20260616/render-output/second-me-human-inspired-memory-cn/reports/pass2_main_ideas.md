# Pass 2 — Main Ideas

1. AI-native 记忆应存在于三个协调层中：L0（原始数据 / RAG 风格）、L1（自然语言摘要、标签、简介）、L2（神经网络参数记忆）。 [Paper evidence, §2.1]
2. SECOND ME 是 LPM 的演进版本，其 L2 作为编排器，将用户桥接到外部专家模型（如 GPT-4o、Deepseek-R1），而非自身执行任务。 [Paper evidence, §2.2]
3. 自动化训练流水线——数据合成、五级过滤、PEFT SFT on Qwen2.5-7B-Instruct，然后 DPO——产生具有强偏好对齐的个性化 L2。 [Paper evidence, §3.1]
4. 答案风格在三种 COT 策略（Weak / Multi-step / Strong）下生成，Strong 使用 Deepseek-R1 推理和严格格式约束；DPO 进一步精炼偏好。 [Paper evidence, §3.2-§3.3]
5. 评估分解为 Memory（Self）、Memory（Third-party）、Context Enhance、Context Critic，附带显式评分标准（Appendix C）和人工评估作为 ground truth。 [Paper evidence, §3.4-§3.5]
