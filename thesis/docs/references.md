# Reference List and Rationale

## 필수 참조(사용자 제공)
1. Ha et al., H3, IEEE CAL 2026, doi:10.1109/LCA.2026.3660969
2. Rhee et al., MoSKA, IEEE CAL 2025, doi:10.1109/LCA.2025.3627539

## 고인용/핵심 배경 논문
1. Vaswani et al., Attention Is All You Need, NeurIPS 2017
2. Dao et al., FlashAttention, NeurIPS 2022
3. Shoeybi et al., Megatron-LM, SC 2019
4. Narayanan et al., Efficient Large-Scale LM Training, SC 2021
5. Lepikhin et al., GShard, ICLR 2021
6. Fedus et al., Switch Transformers, JMLR 2022
7. Kwon et al., PagedAttention/vLLM, SOSP 2023
8. Shazeer et al., Sparsely-Gated MoE, ICLR 2017

## 본 프로젝트와의 연결
- Transformer 기본식: Vaswani et al.
- IO 최적화 attention 커널: FlashAttention
- 대규모 병렬 학습/실행 시스템: Megatron 계열
- sparse expert routing 설계 근거: GShard/Switch/MoE
- serving memory virtualization: PagedAttention
- HBM+HBF tiering, shared/unique KV 분리: H3 + MoSKA
