# Pass 3 — Method Reconstruction

1. Inputs: raw user data (text, interactions, preferences, bios, records) plus optional pre-trained LLM commonsense.
2. Stage A — Synthesis: extract entities / topics / relations; generate Memory-QA pairs via self-location reinforcement and memory-cognition enhancement; generate Context-Enhance and Context-Critic pairs via simulated scenarios and multi-agent interactions.
3. Stage B — Filtering: five-level quality filter (Taori-style) keeps only high-quality synthetic data.
4. Stage C — SFT: PEFT (Bitfit / LoRA-family) on Qwen2.5-7B-Instruct, with answer style drawn from one of three COT strategies (Weak / Multi-step / Strong, the last using Deepseek-R1 as expert).
5. Stage D — DPO: build preference pairs (~20% of SFT data) from the SFT model and run Direct Preference Optimization to refine preference alignment without injecting new knowledge.
6. Stage E — Orchestration: at inference, the trained L2 picks among three deployment modes — Memory QA (Self/Third-party), Context Enhance, Context Critic — and (for complex tasks) routes to an external expert model (GPT-4o, Deepseek-R1) while maintaining user context.
7. Outputs: contextually enriched queries, critiques, and direct answers that align with user identity, preferences, and history.
