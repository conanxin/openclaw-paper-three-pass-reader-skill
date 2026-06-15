# Pass 1 — Five Cs

| C | Answer |
|---|---|
| **Category** | Methods paper proposing a new general-purpose sequence-transduction architecture (encoder–decoder, attention-only) with empirical evaluation on machine translation and constituency parsing. |
| **Context** | Sits at the intersection of three threads: encoder–decoder RNN/LSTM sequence models (Sutskever et al. 2014, Bahdanau et al. 2015); neural attention mechanisms as an addition to RNNs (Bahdanau, Cho, Bengio 2015; Luong, Pham, Manning 2015); and convolutional sequence models such as ByteNet and ConvS2S (Kalchbrenner et al. 2016, Gehring et al. 2017). The Transformer replaces both the recurrence and the convolution with attention. |
| **Correctness** | Methodologically sound. The paper states the inductive bias, provides the mathematical formulation of attention, runs controlled ablations (number of heads, attention key dimension, dropout, positional encoding type), and reports results on standard benchmarks against strong baselines. Empirically the claims about BLEU and training cost have been broadly replicated across thousands of follow-up works. The attention-head visualisation is informal but illustrative rather than load-bearing. |
| **Contributions** | - The Transformer architecture: an encoder–decoder model whose core operation is multi-head scaled dot-product self-attention, with no recurrence and no convolutions.
- Scaled dot-product attention and a justification for the √dₖ scaling factor, derived from the saturation behaviour of softmax at large dot-product magnitudes.
- Multi-head attention as a way to let the model jointly attend to information from different representation subspaces at the same position.
- Sinusoidal positional encodings as a way to inject order information into a permutation-invariant architecture, with empirical evidence that fixed and learned encodings perform comparably.
- Empirical demonstration of state-of-the-art BLEU on WMT 2014 En→De and En→Fr with substantially reduced training cost, plus generalisation evidence on English constituency parsing. |
| **Clarity** | Exceptional. The paper is well-organised (Abstract → Introduction → Background → Model Architecture → Why Self-Attention → Training → Results → Conclusion), the equations are typeset and numbered, every hyperparameter is named, and the ablations explicitly isolate the contribution of each design choice. The reader does not need to consult the supplementary material to understand the main claims. |
