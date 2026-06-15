# Pass 2 — Figures & Tables

### Figure  — (missing title)

Shows the L0/L1/L2 hybrid architecture with inner loop (seamless layer integration) and outer loop (LLM and internet resources under SECOND ME's guidance). Establishes the high-level system layout that the rest of the paper details. [Paper evidence, caption after §1]

### Figure  — (missing title)

Visualises the end-to-end training pipeline: raw data → entity/topic mining → memory data synthesis (self-location reinforcement, memory cognition enhancement) → context enhancement / critique data via simulated scenarios → five-level filtering → PEFT SFT → DPO data generation → evaluation. The 'LLM as Judge' and 'LLM as data synthesizer' labels emphasise automation. [Paper evidence, §3.1]

### Figure  — (missing title)

Side-by-side Weak / Multi-step / Strong COT responses to 'When you think of me, what do you see?'. Shows the increasing richness and stylistic constraint from Weak to Strong COT, and motivates the qualitative difference the authors report in §3.5. [Paper evidence, §3.2]

### Figure  — (missing title)

Concrete Case 1 example for the Context-Enhance task: query about beginner resources for two-stage model training. Compares Weak COT vs Strong COT, with bold-marked entities from the user's record. Used to argue for qualitative superiority of Strong COT. [Paper evidence, §3.5]

### Figure  — (missing title)

Shows how the trained L2 sits between the user and expert models (GPT-4o etc.), with arrows representing possible communications (user-expert arrows omitted for clarity). Supports the §4 Applications and §3.1 multi-agent narrative. [Paper evidence, Appendix D]

### Table  — (missing title)

Memory (Self) / Memory (Third-party) / Context Enhance / Context Critic scores under Strong / Multi-step / Weak COT. Reported numbers (mean, 0-1 scale): Strong 0.91/0.71/0.75/0.85; Multi-step 0.64/0.43/0.85/0.77; Weak 0.86/0.58/0.87/0.64. Strong COT wins on Memory (Self) and Context Critic; Multi-step underperforms Weak overall. [Paper evidence, Table 1 + §3.5]

### Table  — (missing title)

Referenced in §3.5 as showing DPO brings substantial improvements across all tasks. Specific cell values were not cleanly recovered by pdftotext -layout; extraction limitation. Authors' qualitative claim is that iterative COT refinement + DPO yields consistent gains. [Paper evidence, §3.5 reference] [Needs verification for exact numbers]

