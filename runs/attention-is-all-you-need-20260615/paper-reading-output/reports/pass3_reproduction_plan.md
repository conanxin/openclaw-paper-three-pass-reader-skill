# Pass 3 — Reproduction Plan

- **Dataset:** WMT 2014 En→De and WMT 2014 En→Fr (newstest2014 for evaluation); BPE tokenisation.
- **Baseline:** GNMT + RL Ensemble (En→De), ConvS2S (En→Fr), GNMT + RL (En→Fr).
- **Hardware:** 8 NVIDIA P100 GPUs (paper); equivalently 8 A100 or V100 GPUs. Inference fits on a single 16 GB GPU.

## Steps

1. Download WMT 2014 corpus and apply BPE tokenisation with ~37 000 merges for En→De or ~32 000 for En→Fr.
2. Implement token embedding (vocab × d_model) with weight tying and the √d_model scaling factor.
3. Implement sinusoidal positional encoding of dimension d_model.
4. Implement Scaled Dot-Product Attention: softmax(QKᵀ / √dₖ) V, optionally with mask.
5. Implement Multi-Head Attention: h parallel heads with learned projections, concatenated and projected.
6. Implement encoder layer: multi-head self-attention → add & norm → position-wise FFN → add & norm.
7. Implement decoder layer: masked multi-head self-attention → add & norm → cross multi-head attention → add & norm → FFN → add & norm.
8. Stack N = 6 encoder layers and N = 6 decoder layers; final linear projection from d_model to vocab_size with weight tying.
9. Train with Adam (β₁ = 0.9, β₂ = 0.98, ε = 10⁻⁹), warmup-then-decay learning-rate schedule (warmup = 4000 steps), dropout 0.1, label smoothing 0.1.
10. Train base model for ~100 000 steps with batch size ~25 000 tokens; expect ~12 hours on 8 P100 GPUs.
11. Evaluate on newstest2014 with sacrebleu.

## Sanity checks

- After warmup the loss decreases monotonically until ~50 % of training; divergence indicates wrong √dₖ or learning-rate schedule.
- Single-head vs multi-head: multi-head ≥ single-head by ≥ 0.5 BLEU on the development set.
- Sinusoidal vs learned positional encodings: BLEU differs by ≤ 0.2.
- Removing residual connections: training diverges or plateaus at much lower BLEU.
- Inference: output length is sensible (not collapsed, not unbounded).
- At least one attention head shows an interpretable pattern on a curated example.

## Success criteria

- Transformer-base ≥ 27.3 BLEU on WMT 2014 En→De within 100 000 steps.
- Transformer-big ≥ 28.4 BLEU on WMT 2014 En→De within 300 000 steps.
- Reproduce Table 2 within ± 0.5 BLEU on En→Fr.
- Halving the number of heads drops BLEU by ≥ 0.5.
- Attention visualisation shows at least one syntactic-dependency head.
