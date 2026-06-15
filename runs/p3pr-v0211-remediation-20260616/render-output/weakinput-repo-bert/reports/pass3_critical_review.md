# Pass 3 — Critical Review

- The 80% / 10% / 10% masking strategy is presented as a design choice without strong justification; ablation tables show it's better than 100% [MASK] but not by much.
- NSP has since been shown (e.g. by RoBERTa) to contribute little or nothing to downstream performance; the paper reports an ablation in §5.1 but does not promote this insight strongly.
- The paper does not ablate the position of [MASK] tokens in fine-tuning data — later work shows that pre-training/fine-tune mismatch contributes a small but real loss.
- Sequence length is capped at 512 by the learned position embeddings — a real limitation for long-document tasks.
- Numbers on GLUE / SQuAD / etc. are impressive but heavily depend on the pre-training corpus; the paper does not ablate corpus size or domain mix.
- The paper does not discuss ethical considerations: large pre-trained models can encode biases from the training data. (This becomes a major topic in later BERT-era work.)
