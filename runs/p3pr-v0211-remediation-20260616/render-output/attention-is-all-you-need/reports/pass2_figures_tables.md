# Pass 2 — Figures & Tables

### Figure 1 — Figure 1 (full architecture): shows the encoder (left half) and decoder (right half) as stacked blocks, with N = 6 ident

Figure 1 (full architecture): shows the encoder (left half) and decoder (right half) as stacked blocks, with N = 6 identical layers, Multi-Head Attention boxes, Feed-Forward boxes, Add & Norm boxes, and the cross-attention arrows from encoder to decoder.

### Figure 2 — Figure 2 (left): Scaled Dot-Product Attention diagram showing the Q, K, V matrices, the MatMul(Q, Kᵀ), the Scale by 1/√d

Figure 2 (left): Scaled Dot-Product Attention diagram showing the Q, K, V matrices, the MatMul(Q, Kᵀ), the Scale by 1/√dₖ, the Mask (opt.), the SoftMax, and the MatMul with V.

### Figure 3 — Figure 2 (right): Multi-Head Attention diagram showing h parallel attention heads with separate linear projections, conc

Figure 2 (right): Multi-Head Attention diagram showing h parallel attention heads with separate linear projections, concatenated and projected.

### Table 4 — Table 1 (encoder/decoder architectural hyperparameters): lists N=6, d_model=512, d_ff=2048, h=8, d_k=d_v=64, P_drop=0.1,

Table 1 (encoder/decoder architectural hyperparameters): lists N=6, d_model=512, d_ff=2048, h=8, d_k=d_v=64, P_drop=0.1, base vs big models side by side.

### Figure 5 — Table 2 (machine translation BLEU and training cost): reports training time in FLOPs, and BLEU on WMT 2014 En→De and En→

Table 2 (machine translation BLEU and training cost): reports training time in FLOPs, and BLEU on WMT 2014 En→De and En→Fr for Transformer-base, Transformer-big, and a long list of baselines (ByteNet, Deep-Att + PosUnk, GNMT + RL, ConvS2S, MoE, GNMT+RL Ensemble). The Transformer-big beats or matches every baseline on En→Fr and beats the best ensemble on En→De by >2 BLEU at a fraction of the training cost.

### Figure 6 — Table 3 (English constituency parsing F1): shows the Transformer beats or matches strong LSTM and CNN baselines on WSJ a

Table 3 (English constituency parsing F1): shows the Transformer beats or matches strong LSTM and CNN baselines on WSJ and is competitive on extra training data (BerkeleyParser).

