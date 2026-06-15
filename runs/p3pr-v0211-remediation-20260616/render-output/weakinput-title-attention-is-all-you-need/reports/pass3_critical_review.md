# Pass 3 — Critical Review

- The paper presents a single-configuration ablation table on number of heads (Table 4) that uses the base model on a development set; this is informative but not a full hyperparameter sweep, and the optimal number of heads on a different task or scale is not guaranteed to be 8.
- The training-time comparison in Table 2 mixes wall-clock and FLOPs depending on row, and the FLOPs accounting ignores implementation overhead; the comparison is broadly correct but not apples-to-apples.
- The attention-head visualisations (Figure 5) are informal and pick out cherry-picked heads that look interpretable; they are not a quantitative interpretability study.
- The paper does not discuss the O(n²) memory cost of self-attention; this becomes a binding constraint for very long sequences and is the explicit motivation for follow-ups like Longformer, Linformer, and FlashAttention.
- The English constituency parsing result (Table 3) is reported but not analysed in depth; the dataset choice (WSJ, BerkeleyParser) and the role of pre-training are not discussed.
- There is no failure-mode analysis: where does the Transformer actually lose to RNNs or CNNs? The paper frames the comparison as 'Transformer wins everywhere', which is an overstatement.
- Label smoothing of 0.1 is reported to help, but a sweep over the smoothing value is not provided; the choice is presented as a known good default rather than as a deliberate design choice.
