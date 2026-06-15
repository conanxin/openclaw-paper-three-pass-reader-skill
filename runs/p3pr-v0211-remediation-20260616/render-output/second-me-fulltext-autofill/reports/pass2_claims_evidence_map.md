# Pass 2 — Claims → Evidence Map

- **C-001** — SECOND ME parameterises a user's memory into L2 model weights, layered above L0 (raw data) and L1 (natural-language memory).  
  Evidence: [Paper evidence] (§2.1 (LPM 1.0 recap) + §2.2 (Overall Design))  
  Confidence: high
- **C-002** — SECOND ME serves as a 'context provider' rather than a task executor, aligning with the user's perspective.  
  Evidence: [Author claim] (§2.2 — 'we position SECOND ME as a context provider aligned with the user's perspective, rather than a task executor.')  
  Confidence: high
- **C-003** — The training pipeline is fully automated and comprises data synthesis, five-level filtering, PEFT SFT, and DPO.  
  Evidence: [Paper evidence] (§3.1 (Training Pipeline) + Figure 2)  
  Confidence: high
- **C-004** — The base model is Qwen2.5-7B-Instruct and training starts with PEFT.  
  Evidence: [Paper evidence] (§3.1 — 'Our base model, Qwen2.5-7B-Instruct (Qwen et al., 2025), undergoes automatic training and evaluation.')  
  Confidence: high
- **C-005** — Three answer-style COT strategies are used during training: Weak, Multi-step, and Strong (the last using Deepseek-R1 with strict format constraints).  
  Evidence: [Paper evidence] (§3.2 (Answer Style: COT or Not?))  
  Confidence: high
- **C-006** — DPO does not introduce new knowledge but refines preference alignment on approximately 20% of the SFT data.  
  Evidence: [Paper evidence] (§3.3 — 'Preference pairs constitute approximately 20% of the total SFT training data.')  
  Confidence: high
- **C-007** — Evaluation uses four metrics: Memory (Self), Memory (Third-party), Context Enhance, and Context Critic.  
  Evidence: [Paper evidence] (§3.4 + Appendix C)  
  Confidence: high
- **C-008** — Strong COT significantly improves Memory (Self) and Context Critic performance; Multi-step COT often underperforms Weak COT.  
  Evidence: [Paper evidence] (Table 1 (extracted): Strong Memory (Self) = 0.91 vs Weak = 0.86 vs Multi-step = 0.64.)  
  Confidence: high
- **C-009** — DPO brings substantial improvements across all tasks when combined with iterative COT refinement.  
  Evidence: [Paper evidence] (§3.5 — 'Table 2 demonstrates that DPO brings substantial improvements'.)  
  Confidence: medium
- **C-010** — Human evaluation reports Strong-COT-with-DPO scores close to 1 and Strong-COT-without-DPO at ~0.95 average.  
  Evidence: [Author claim] (§3.5 — 'Human evaluation shows Strong COT without DPO achieves an average score of 0.95, while Strong COT with DPO scores close to 1.')  
  Confidence: medium
- **C-011** — SECOND ME drives a 3 to 5 orders of magnitude network-efficiency gain via Metcalfe's Law in human-AI networks.  
  Evidence: [Author claim] (§4 — 'integration of human and AI nodes increases network efficiency by 3 to 5 orders of magnitude.')  
  Confidence: low
- **C-012** — The full system is open-sourced at github.com/Mindverse/Second-Me (note: Mindverse, not mindhive).  
  Evidence: [Paper evidence] (Abstract + §4 — 'https://github.com/Mindverse/Second-Me'.)  
  Confidence: high
