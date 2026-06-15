# Pass 3 — Reproduction Plan

- **Dataset:** 通过 SECOND ME 流水线合成用户数据（原始用户记录 → 实体/主题挖掘 → 自我定位强化和记忆认知增强 → 模拟 Context-Enhance/Critic）。作者未发布固定数据集；复现需要重新合成。可选从公共长时记忆数据集（如 LoCoMo、MSC）启动以引导原始记录。
- **Baseline:** 长上下文 LLM（如带扩展上下文的 Qwen2.5-7B-Instruct）和覆盖相同原始数据的 RAG 基线，在四个 SECOND ME 指标上评估。
- **Hardware:** 单张 A100 80GB 或等效设备用于 Qwen2.5-7B 的 SFT+DPO with PEFT（LoRA r=16 或 BitFit）。推理可在单张消费级 GPU 上运行，PEFT adapter 已合并。

## Steps

1. 1. 使用 SECOND ME 流水线（Appendix A）合成用户数据。
2. 2. 运行五级过滤（Appendix A）；保留过滤后的语料库。
3. 3. 使用 PEFT（LoRA）对 Qwen2.5-7B-Instruct 进行 SFT，为每种 COT 策略生成一个模型。
4. 4. 构建 DPO 偏好对（~20% SFT 数据）并运行 DPO。
5. 5. 在 Memory (Self)、Memory (Third-party)、Context Enhance、Context Critic 上评估（Appendix C 评分标准）。
6. 6. 在相同指标上与长上下文和 RAG 基线对比。

## Sanity checks

- Strong COT > Multi-step COT on Memory (Self)（Table 1 趋势）。
- Multi-step COT 在 Memory (Third-party) 上未击败 Weak COT（Table 1 趋势）。
- 添加 DPO 在 Context Enhance 和 Context Critic 上带来进一步增益。
- 人工评估子集（小 N）显示 Strong COT + DPO 得分 ≈ 1.0。

## Success criteria

- 复现 Table 1 趋势（Strong > Weak > Multi-step on Memory (Self) and Context Critic）。
- 复现 Table 2 定性趋势（DPO 增加增益）——精确数字可能因数据合成随机性而异。
- 证明 SECOND ME 在 Memory QA 指标上优于 RAG 基线。
