# Pass 2 — Main Ideas

1. Attention alone — without recurrence or convolution — is sufficient to build a state-of-the-art sequence-transduction encoder–decoder, provided the attention is multi-head and scaled.
2. Self-attention connects all positions in a sequence with O(1) path length, compared with O(n) for recurrent layers, which directly improves both parallelisability (training) and long-range dependency modelling.
3. Multi-head attention is more expressive than single-head attention because it lets the model attend to information from different representation subspaces at the same position; ablations show that ablations on head count cost BLEU.
4. Scaled dot-product attention (softmax(QKᵀ / √dₖ) V) is necessary: without the √dₖ factor the softmax saturates for large dₖ and training fails. The paper proves this both empirically (a variant without the scaling diverges) and intuitively (dot products grow with √dₖ).
5. Positional information is reintroduced via fixed sinusoidal encodings added to the input embeddings; the paper shows that learned positional embeddings perform comparably, suggesting that the exact choice is not critical.
6. A two-stage learning-rate schedule (linear warmup then inverse-square-root decay) plus residual dropout and label smoothing gives stable training of the deep stack.
7. The architectural inductive bias is weak (no locality prior, no order prior) — this is a deliberate trade-off. The paper argues the trade-off is worth it for sequence length ≤ a few hundred because of the parallelisability and the O(1) path length.
