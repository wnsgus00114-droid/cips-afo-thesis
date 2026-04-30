# Reference Alignment: H3 + MoSKA -> A.F.O Decisions

## Paper 1: H3 (IEEE CAL 2026, doi:10.1109/LCA.2026.3660969)
Key takeaway used in A.F.O:
- HBF provides high capacity and high bandwidth but higher latency than HBM.
- Best use is read-mostly, large-footprint data in HBF while latency-sensitive mutable data remains in HBM.

A.F.O decisions mapped:
1. Weights and shared precomputed KV in HBF (`0x0-0x3` regions)
2. Runtime KV and activations in HBM (`0x8-0xB` regions)
3. HBF latency hidden by next-layer prefetch and LHB emergency path
4. Layer-2 physical ring topology fixed as inner HBM rectangular ring + outer HBF rectangular ring

## Paper 2: MoSKA (IEEE CAL 2025, doi:10.1109/LCA.2025.3627539)
Key takeaway used in A.F.O:
- Separate shared vs unique KV.
- Shared KV path can be batched and executed as GEMM, reducing memory-bound behavior.
- Sparse, MoE-like routing reduces unnecessary KV access.

A.F.O decisions mapped:
1. Dedicated Shared KV Attention Engine and Unique KV Attention Engine
2. Chunk-level top-k routing metadata and expert-wise chunk placement
3. Shared-KV batch aggregation stage before matrix execution
4. Router confidence-driven prefetch depth and dynamic top-k policy

## Integrated Co-design Implication
- H3 alone improves capacity efficiency but not necessarily decode compute utilization.
- MoSKA alone improves attention utilization but may still be capacity-limited.
- A.F.O combines both to shift the memory/compute balance while sustaining long context.
