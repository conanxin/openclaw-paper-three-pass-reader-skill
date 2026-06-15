# Pass 3 — Method Reconstruction

1. Implement a multi-layer bidirectional Transformer encoder using a standard Transformer implementation (e.g. tensor2tensor or HuggingFace transformers).
2. BERT_BASE hyperparameters: L=12 layers, H=768 hidden, A=12 heads, ~110M parameters; BERT_LARGE: L=24, H=1024, A=16, ~340M parameters.
3. Tokenise input with WordPiece tokenisation (30 000 token vocabulary, cased for BERT_BASE_CASED).
4. Build the input representation as the sum of three embeddings: token embeddings, segment embeddings (0 or 1 for sentence A vs B), and learned position embeddings (max 512).
5. Pre-training objective 1 — Masked Language Modeling (MLM): randomly mask 15% of WordPiece tokens; of those, 80% replaced with [MASK], 10% replaced with a random token, 10% kept unchanged. Loss is cross-entropy on the masked positions only.
6. Pre-training objective 2 — Next-Sentence Prediction (NSP): given a (A, B) pair, predict whether B follows A. 50% of training pairs are actual next sentences; 50% are random pairs.
7. Pre-train on a large corpus (BERT_BASE was trained on BooksCorpus 800M words + English Wikipedia 2.5B words).
8. Pre-train for 1M steps with batch size 256 sequences of length 128 (first 90% of steps) then 512 (last 10%). Adam optimiser with LAMB warmup; L=0.0001 dropout; gelu activation.
9. Fine-tuning: replace the pre-training output layers with task-specific ones. For GLUE: classification head. For SQuAD: span-start and span-end classifiers over the sequence. Train all parameters for 2–3 epochs with a learning rate in {2e-5, 3e-5, 5e-5} and batch size in {16, 32}.
10. Evaluate: GLUE test set via the official evaluation server; SQuAD v1.1 / v2.0 via the official scripts; expect numbers close to Table 1 / Table 2 within a small margin.
