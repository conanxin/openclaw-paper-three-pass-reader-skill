# Pass 3 — Reproduction Plan

- **Dataset:** Synthetic user data via the SECOND ME pipeline (raw user records → entity/topic mining → self-location reinforcement and memory-cognition enhancement → simulated Context-Enhance/Critic). The authors do not publish a fixed dataset; replication requires re-synthesising. Optionally start from public long-term-memory datasets (e.g. LoCoMo, MSC) to bootstrap raw records.
- **Baseline:** Long-context LLM (e.g. Qwen2.5-7B-Instruct with extended context) and a RAG baseline over the same raw data, evaluated on the four SECOND ME metrics.
- **Hardware:** Single A100 80GB or equivalent for SFT+DPO of Qwen2.5-7B with PEFT (LoRA r=16 or BitFit). Inference can run on a single consumer GPU with PEFT adapters merged.

## Steps

1. 1. Synthesise user data using the SECOND ME pipeline (Appendix A).
2. 2. Run five-level filtering (Appendix A); keep filtered corpus.
3. 3. SFT Qwen2.5-7B-Instruct with PEFT (LoRA), generating one model per COT strategy.
4. 4. Build DPO preference pairs (~20% of SFT data) and run DPO.
5. 5. Evaluate on Memory (Self), Memory (Third-party), Context Enhance, Context Critic (Appendix C rubrics).
6. 6. Compare against long-context and RAG baselines on the same metrics.

## Sanity checks

- Strong COT > Multi-step COT on Memory (Self) (Table 1 trend).
- Multi-step COT does NOT beat Weak COT on Memory (Third-party) (Table 1 trend).
- Adding DPO yields further gains on Context Enhance and Context Critic.
- Human evaluation subset (small N) shows Strong COT + DPO scores ≈ 1.0.

## Success criteria

- Replicate Table 1 trends (Strong > Weak > Multi-step on Memory (Self) and Context Critic).
- Replicate Table 2 qualitative trend (DPO adds gains) — exact numbers may vary by data synthesis randomness.
- Demonstrate that SECOND ME outperforms a RAG baseline on Memory QA metrics.
