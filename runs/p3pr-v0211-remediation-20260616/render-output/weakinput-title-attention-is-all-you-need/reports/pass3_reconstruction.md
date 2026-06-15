# Pass 3 — Method Reconstruction

1. Define hyperparameters: N = 6 encoder layers, N = 6 decoder layers, d_model = 512 (base) or 1024 (big), d_ff = 4 × d_model, h = 8 heads, d_k = d_v = d_model / h = 64, dropout = 0.1.
2. Build the input embedding: a learned matrix E of shape (vocab_size × d_model) mapping tokens to vectors; multiply by √d_model to compensate for the embedding's variance in the residual stream.
3. Add sinusoidal positional encodings PE(pos, 2i) = sin(pos / 10000^(2i/d_model)), PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model)), of the same dimension d_model; sum elementwise with the token embeddings.
4. Build the encoder layer: a multi-head self-attention sub-layer followed by a position-wise feed-forward sub-layer; each sub-layer is wrapped in residual connection (x + Sublayer(x)) and layer normalisation (LayerNorm(x + Sublayer(x))).
5. Implement Scaled Dot-Product Attention: Attention(Q, K, V) = softmax(QKᵀ / √dₖ) V. Concatenate over multiple queries at once via batched matmul.
6. Implement Multi-Head Attention: project Q, K, V into h subspaces with learned matrices Wᵢᴼ, Wᵢᴷ, Wᵢⱽ; run h parallel Attention heads; concatenate and project with Wᴼ.
7. Build the decoder layer: same as encoder, plus a third sub-layer that performs multi-head attention over the encoder stack output (cross-attention). The self-attention sub-layer uses masking to preserve autoregressive property: set attention scores to −∞ for positions ahead of the current one.
8. Add a final linear projection from d_model to vocab_size, sharing weights with the input embedding (tie weights); compute token probabilities with softmax.
9. Train with Adam (β₁ = 0.9, β₂ = 0.98, ε = 10⁻⁹) and a custom learning-rate schedule: lrate = d_model^(-0.5) · min(step^(-0.5), step · warmup^(-1.5)) with warmup = 4000 steps. Apply residual dropout 0.1 and label smoothing 0.1.
10. Train on WMT 2014 En→De (or En→Fr) with BPE tokenisation (shared source–target vocabulary of ~37 000 tokens for En→De, ~32 000 for En→Fr); batch size chosen so each training step processes ~25 000 source and ~25 000 target tokens; base model trains in ~12 hours on 8 P100 GPUs, big model in ~3.5 days.
11. Evaluate on newstest2014 with sacrebleu; expect ~28.4 BLEU for Transformer-big on En→De and ~41.8 BLEU on En→Fr.
