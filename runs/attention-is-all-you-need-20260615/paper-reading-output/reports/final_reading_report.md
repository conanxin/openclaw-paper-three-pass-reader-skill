# Final Reading Report — Attention Is All You Need

## 1. What is this paper about?

Vaswani et al. (2017) introduce the Transformer, a sequence-transduction architecture built entirely on multi-head scaled dot-product self-attention with positional encodings, dropping recurrence and convolutions, and demonstrate 28.4 BLEU on WMT 2014 En→De and 41.8 BLEU on WMT 2014 En→Fr with substantially less training compute than the prior state of the art.

## 2. Is it worth reading deeper?

**CONTINUE_FULL** — 

## 3. Main contributions

- The Transformer architecture: an encoder–decoder model whose core operation is multi-head scaled dot-product self-attention, with no recurrence and no convolutions.
- Scaled dot-product attention and a justification for the √dₖ scaling factor, derived from the saturation behaviour of softmax at large dot-product magnitudes.
- Multi-head attention as a way to let the model jointly attend to information from different representation subspaces at the same position.
- Sinusoidal positional encodings as a way to inject order information into a permutation-invariant architecture, with empirical evidence that fixed and learned encodings perform comparably.
- Empirical demonstration of state-of-the-art BLEU on WMT 2014 En→De and En→Fr with substantially reduced training cost, plus generalisation evidence on English constituency parsing.

## 4. Where is the evidence strongest / weakest?

See `pass2_claims_evidence_map.md`. Filter by confidence in the HTML page.

## 5. What would I change if I were the author?

- The paper presents a single-configuration ablation table on number of heads (Table 4) that uses the base model on a development set; this is informative but not a full hyperparameter sweep, and the optimal number of heads on a different task or scale is not guaranteed to be 8.
- The training-time comparison in Table 2 mixes wall-clock and FLOPs depending on row, and the FLOPs accounting ignores implementation overhead; the comparison is broadly correct but not apples-to-apples.
- The attention-head visualisations (Figure 5) are informal and pick out cherry-picked heads that look interpretable; they are not a quantitative interpretability study.
- The paper does not discuss the O(n²) memory cost of self-attention; this becomes a binding constraint for very long sequences and is the explicit motivation for follow-ups like Longformer, Linformer, and FlashAttention.
- The English constituency parsing result (Table 3) is reported but not analysed in depth; the dataset choice (WSJ, BerkeleyParser) and the role of pre-training are not discussed.
- There is no failure-mode analysis: where does the Transformer actually lose to RNNs or CNNs? The paper frames the comparison as 'Transformer wins everywhere', which is an overstatement.
- Label smoothing of 0.1 is reported to help, but a sweep over the smoothing value is not provided; the choice is presented as a known good default rather than as a deliberate design choice.

## 6. Can I reproduce it?

See `pass3_reproduction_plan.md`.

## 7. What remains open?

- How can the quadratic memory wall of self-attention be broken without losing the parallelisability and the O(1) path length?
- What is the right number of attention heads for a given task and dataset size? Is there a principled way to choose it?
- Why does the Transformer generalise so well to constituency parsing with so little task-specific tuning? Is the inductive bias weaker than it appears, or is the data enough to overcome the bias?
- Do attention heads actually learn interpretable structure in tasks other than translation and parsing?
- What is the failure mode of attention-only models on tasks where strong structural priors are known to help (small data, very long contexts, arithmetic reasoning)?
- How does the Transformer behave under distribution shift in the input distribution (e.g., out-of-distribution source-side vocabulary, code-switching)?
- Could the multi-head structure be replaced by a single larger attention head, or by a structured attention operator with a learned structure?
