# A.F.O (All For One): AC/DC 3D Silicon for MoSKA + H3 LLM Inference

## 1. Abstract
A.F.O is a 3D-integrated inference chip architecture that combines (i) Apple-like unified compute, (ii) MoSKA shared/unique KV attention execution, and (iii) H3-style HBM+HBF hybrid memory tiering. The architecture targets long-context, decode-heavy large language model inference where runtime KV growth and memory bandwidth pressure dominate performance. A.F.O places read-mostly model weights and shared KV in HBF, runtime/hot KV in HBM, and layer-critical tiles in banked on-die SRAM with double-buffering and a latency-hiding buffer. The design introduces an expert-style chunk routing flow to turn shared KV processing from memory-bound GEMV streams into batched GEMM kernels. This report provides an implementable roadmap from simulator to RTL/FPGA/ASIC experiments, including address maps, module interfaces, runtime APIs, and validation methodology.

## 2. Introduction
Long-context LLM serving suffers from two coupled constraints:
1. KV cache growth scales with active requests and context length.
2. Decode attention becomes memory-bound with low arithmetic intensity.

Recent work suggests complementary paths:
- H3: pair high-bandwidth flash (HBF) with HBM to improve capacity efficiency for read-heavy inference.
- MoSKA: separate shared and unique KV, batch shared operations to shift toward compute-bound GEMM.

A.F.O unifies both principles in one hardware/software stack. Instead of treating memory as flat HBM, it introduces explicit tier-aware placement and prefetch policy to keep compute engines fed while minimizing latency penalties from HBF.

## 3. Background (MoSKA + H3)
### 3.1 H3 implications for chip design
H3 demonstrates that HBF provides much larger capacity with high bandwidth, but suffers higher access latency than HBM. Therefore, data placement must be semantic:
- Immutable, read-mostly tensors -> HBF
- latency-sensitive, write-heavy state -> HBM

### 3.2 MoSKA implications for chip design
MoSKA differentiates:
- Unique KV (request-private)
- Shared KV (reused across many requests)

Shared KV can be grouped and executed in a batched GEMM form, substantially improving utilization compared to naive GEMV per request.

## 4. A.F.O Architecture
### 4.1 3D package
```text
Layer 2 (Memory): HBM3 x8 + HBF x2 + H3 Address Router
      || Silicon Bridge (VN0/VN1/VN2 QoS virtual networks)
Layer 1 (Compute): CPU, GPU-like SIMT, NPU matrix cores,
                   Shared/Unique KV engines, DMA/Prefetch,
                   KV scheduler, MoE router, 768MB banked SRAM
```

### 4.2 Compute die microarchitecture
- CPU cluster: runtime orchestration, MMIO, scheduling decisions
- GPU-like SIMT array: elementwise and sparse operations
- Matrix accelerator: GEMM/FFN/attention tiles
- Shared KV attention engine: batched shared chunks
- Unique KV attention engine: low-latency per-request attention
- MoE router hardware assist: top-k chunk expert selection
- DMA + prefetch engines: layer lookahead data movement
- Unified memory controller: HBM/HBF/SRAM routing and QoS

## 5. Memory Hierarchy Design
### 5.1 H3 mapping
- HBM:
  - runtime KV
  - activations
  - hot metadata and hot shared chunk replicas
- HBF:
  - dense and expert weights (RO)
  - shared precomputed KV library (RO)
  - cold KV spill

### 5.2 Unified address map
Prefix-based decode:
- `0x0-0x3`: HBF
- `0x8-0xB`: HBM
- `0xF`: SRAM aperture

### 5.3 SRAM organization
- 32 banks, total 768MB
- ping-pong weight buffers (A/B)
- ping-pong KV buffers (A/B)
- activation ring buffer
- metadata bank
- latency hiding buffer (LHB)

## 6. KV Cache Strategy
### 6.1 Chunk model
Shared KV stored as chunk tensor units:
- tuple: `(layer, expert_id, head_group, token_range, chunk_id)`
- size: 64-256KB preferred window

Unique KV stored as append-only runtime pages in HBM.

### 6.2 Layer overlap
At Layer N:
- execute attention + FFN
- prefetch Layer N+1 weights/chunks/metadata to B-buffers

At Layer N+1:
- consume prefetched B-buffers
- refill A-buffers for N+2

### 6.3 MoE-style routing
- query embedding -> top-k chunk experts
- chunk selection confidence controls dynamic top-k
- low-confidence paths increase prefetch depth and reserve LHB

## 7. Software-Hardware Co-design
### 7.1 Runtime responsibilities
- memory placement planner (HBM vs HBF)
- KV lifecycle manager (hot/warm/cold)
- prefetch planner (layer+router aware)
- execution scheduler (compute/memory overlap)

### 7.2 Compiler responsibilities
- split attention into shared/unique paths
- aggregate shared queries for GEMM
- inject prefetch pseudo-ops

### 7.3 Hardware assist boundaries
- router accel for top-k lookup
- prefetch assist FSM for descriptor emission
- perf counter block for adaptive scheduling feedback

## 8. Experimental Setup
### 8.1 Baselines
- HBM-only GPU
- MoSKA-only (no HBF)
- H3-only (no shared-KV batching)
- Apple-like UMA without chunk routing

### 8.2 Sweeps
- batch size
- context length
- expert count
- KV chunk size
- HBF share ratio
- prefetch accuracy
- LHB on/off

### 8.3 Metrics
- tokens/sec, ms/token
- HBM/HBF/bridge utilization
- SRAM hit ratio
- stall ratio and memory bottleneck %
- power and throughput/watt

## 9. Results (Synthetic Prototype)
Synthetic runs from the current analytical model show:
- Baseline comparison (`results/tables/baseline_comparison.md`):
  - AFO_full: 16.63 tokens/sec, 60.14 ms/token
  - HBM_only_GPU: 14.47 tokens/sec, 69.13 ms/token
  - MoSKA_only: 15.68 tokens/sec, 63.77 ms/token
  - H3_only: 12.91 tokens/sec, 77.47 ms/token
- Prefetch sweep:
  - prefetch accuracy 0.60 -> 14.05 tokens/sec
  - prefetch accuracy 0.95 -> 16.50 tokens/sec
- Context sweep:
  - 1K context -> 16.13 tokens/sec
  - 16K context -> 15.96 tokens/sec
- KV chunk sweep:
  - 64KB chunk is best in this prototype model, larger chunks show overfetch penalties

Representative result artifacts are generated under:
- `results/sim/*.csv`
- `results/plots/*.svg`
- `results/plots/*_summary.txt`

## 10. Discussion
A.F.O gains come from coordinated co-design, not a single component:
1. Capacity efficiency from HBF placement
2. Utilization uplift from shared-KV GEMM batching
3. Latency control from SRAM staging and LHB emergency refill

Failure modes:
- high routing entropy -> larger active chunk set
- bridge congestion -> memory/compute overlap collapse
- insufficient SRAM partitioning -> prefetch eviction thrash

## 11. Limitations
- analytical simulator uses first-order latency/bandwidth approximations
- no full NAND endurance and firmware effects in current model
- router hardware cost modeled abstractly before full RTL/ANN implementation

## 12. Future Work
- cycle-accurate bridge arbitration model
- quantized router index accelerator RTL
- real kernel trace integration from serving runtime
- thermal-aware 3D floorplan optimization

## 13. Conclusion
A.F.O provides a concrete path to build a practical long-context LLM inference chip by fusing MoSKA execution strategy with H3 memory tiering and a unified compute die. The architecture is implementation-oriented: explicit memory map, prefetch policies, block interfaces, and staged prototype milestones are defined so development can begin immediately from simulator and RTL-critical path blocks.

## References
1. Minho Ha, Euiseok Kim, Hoshik Kim, "H3: Hybrid Architecture Using High Bandwidth Memory and High Bandwidth Flash for Cost-Efficient LLM Inference," IEEE Computer Architecture Letters, 2026, doi:10.1109/LCA.2026.3660969.
2. Myunghyun Rhee et al., "MoSKA: Mixture of Shared KV Attention for Efficient Long-Sequence LLM Inference," IEEE Computer Architecture Letters, 2025, doi:10.1109/LCA.2025.3627539.
