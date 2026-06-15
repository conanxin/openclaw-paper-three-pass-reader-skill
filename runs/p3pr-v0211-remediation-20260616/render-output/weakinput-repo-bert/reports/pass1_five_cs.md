# Pass 1 — Five Cs

|| C | Answer |
||---|---|
|| **Category** | Methods paper proposing a new pre-trained language representation model, with empirical results on a wide range of NLP tasks. |
|| **Context** | Sits between ELMo (Peters et al., 2018; feature-based, shallow bidirectionality via concatenation) and OpenAI GPT (Radford et al., 2018; fine-tuning, unidirectional left-to-right Transformer). BERT is the first fine-tuning approach that is deeply bidirectional in all layers. |
|| **Correctness** | High. Empirical claims have been replicated thousands of times since. Ablations isolate the contribution of MLM, NSP, and bidirectionality. Numbers on GLUE / MultiNLI / SQuAD match independent re-implementations. |
|| **Contributions** | - The BERT model: a deeply bidirectional pre-trained Transformer encoder.
- Two pre-training objectives: masked language modeling (MLM) and next-sentence prediction (NSP).
- A unified fine-tuning recipe: pre-train once, fine-tune with one additional output layer for many downstream tasks.
- State-of-the-art results on eleven NLP tasks at publication, with strong gains on GLUE, MultiNLI, SQuAD v1.1, SQuAD v2.0, and SWAG.
- Two model sizes released: BERT_BASE (110M params) and BERT_LARGE (340M params). |
|| **Clarity** | Excellent. The paper is well-organised (Abstract → Introduction → Related Work → BERT → Pre-training BERT → Fine-tuning BERT → Experiments → Ablations → Conclusion → Appendix). Hyperparameters are explicit. Figures illustrate pre-training inputs and fine-tuning model architectures. Tables are cleanly separated by task family. |
