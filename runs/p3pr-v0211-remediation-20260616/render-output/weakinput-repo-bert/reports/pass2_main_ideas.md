# Pass 2 — Main Ideas

1. Pre-training a deep bidirectional Transformer on large unlabelled text, then fine-tuning on downstream tasks, gives strong performance across many NLP benchmarks.
2. Masked language modeling (MLM) is the key pre-training objective: 15% of input tokens are masked and the model predicts them, conditioned on both left and right context.
3. Next-sentence prediction (NSP) is a small but useful secondary objective that helps the model learn sentence-pair relationships for tasks like NLI and QA.
4. The fine-tuning recipe is unusually simple: one additional output layer, 2–3 epochs, all parameters updated. This makes downstream adaptation cheap.
5. Bidirectionality matters: ablation against a left-to-right-only BERT (the 'LTR' ablation in §5.1) drops GLUE score by a large margin.
