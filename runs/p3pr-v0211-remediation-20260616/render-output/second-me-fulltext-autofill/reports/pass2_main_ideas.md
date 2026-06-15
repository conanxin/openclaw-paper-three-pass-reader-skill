# Pass 2 — Main Ideas

1. AI-native memory should live in three coordinated layers: L0 (raw data / RAG-style), L1 (natural-language summaries, tags, bios), and L2 (neural-network parameter memory). [Paper evidence, §2.1]
2. SECOND ME is an evolved LPM whose L2 acts as an orchestrator that bridges the user to external expert models (e.g. GPT-4o, Deepseek-R1) rather than executing tasks itself. [Paper evidence, §2.2]
3. An automated training pipeline — data synthesis, five-level filtering, PEFT SFT on Qwen2.5-7B-Instruct, then DPO — produces a personalised L2 with strong preference alignment. [Paper evidence, §3.1]
4. Answer style is generated under three COT strategies (Weak / Multi-step / Strong), with Strong using Deepseek-R1 reasoning and strict format constraints; DPO refines preferences further. [Paper evidence, §3.2-§3.3]
5. Evaluation is decomposed into Memory (Self), Memory (Third-party), Context Enhance, and Context Critic, with explicit scoring rubrics (Appendix C) and human evaluation as ground truth. [Paper evidence, §3.4-§3.5]
