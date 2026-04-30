# A.F.O: Enforcing Cross-Tier Execution Contracts for 3D HBM+HBF LLM Inference Under Finite Bridge Bandwidth

## 1. Abstract
This work presents A.F.O (All For One), a mechanism-driven 3D inference architecture for long-context LLM serving. A.F.O is not presented as a loose composition of MoSKA, H3, and unified compute; it enforces three contracts: (i) tier-local memory semantics (runtime-hot mutable state in HBM, read-mostly state in HBF), (ii) descriptor-coupled overlap (Layer-N compute with Layer-(N+1) route-aware prefetch), and (iii) SRAM A/B + latency-hiding replay invariants under finite bridge bandwidth. We validate architectural feasibility with multi-seed cycle-inspired simulation, stress scenarios, fairness-constrained baselines, and model-to-metric traceability. Results show consistent directional gains and explicit tail-risk exposure under burst traffic and thermal coupling. The repository targets policy-level validation, not tape-out claims.

## 2. Problem Statement
Long-context decode is constrained by memory traffic rather than peak FLOPS. Two failures dominate in existing systems:
1. Runtime KV growth increases latency variance in multi-tenant service.
2. Memory tiers are often treated as capacity pools, not execution contracts.

A.F.O hypothesis:
- If tier semantics are enforced physically and the prefetch schedule is tied to routing descriptors, then overlap remains deterministic enough to control tail latency under finite bridge bandwidth.

## 3. Contributions
1. Contracted 3D topology model:
- Top compute die, bottom ringed memory tier (inner HBM rectangular ring, outer HBF ring).
2. Mechanism-level execution design:
- Shared/unique KV split + route-aware chunk staging + descriptor-coupled prefetch.
3. Fairness-constrained evaluation protocol:
- Baselines share identical workload/capacity/BW constraints, only policy knobs vary.
4. Trust and traceability package:
- sanity checks, causal-chain report, tail root-cause, thermal impact report, model-error bounds.

## 4. Why Prior Systems Are Not Enough
### 4.1 Component-optimized systems
- FlashAttention-like kernels improve local attention kernels but do not enforce cross-tier placement.
- vLLM-like paged KV improves allocator/runtime behavior but does not guarantee physical-tier execution semantics.

### 4.2 Tiering-only systems
- H3-style tiering provides capacity economics, but can still fail under burst because bridge contention and miss exposure are not contract-driven.

### 4.3 MoSKA-only systems
- Shared/unique KV separation improves reuse, but without tier-local contracts and deterministic overlap rules, multi-tenant burst can still trigger unstable tails.

## 5. Architecture
### 5.1 Physical contract
- Layer1 (top): compute (CPU + SIMT + matrix + SRAM + router/scheduler).
- Layer2 (bottom): memory rings (HBM inner, HBF outer).
- Silicon bridge fabric: high-bandwidth but finite and contention-prone.

### 5.2 Memory contract
- HBM: runtime KV, activations, routing metadata, mutable hot state.
- HBF: model weights, shared KV catalog, cold chunks, read-mostly state.

### 5.3 Execution contract
- Route-aware chunk selection determines prefetch descriptors.
- During Layer N, prefetch Layer N+1 weights/chunks/metadata.
- SRAM A/B swap + LHB replay is mandatory for miss containment.

This is critical because it converts a best-effort prefetch policy into a deterministic scheduling contract.

## 6. Equations and Observable Mapping
Equation (1):
\[
T_{layer}=\max(T_{compute}, T_{mem}) + T_{router}
\]
Equation (2):
\[
T_{mem}=\max\left(\frac{B_{hbm}}{BW_{hbm}},\;\frac{B_{hbf}}{BW_{hbf}}+\Delta_{miss},\;\frac{B_{bridge}}{BW_{bridge}}\right)
\]
Equation (3):
\[
\Delta_{miss}=(1-p_{pref})(L_{hbf}+\alpha\cdot B_{hbf}/BW_{hbf})
\]
Equation (4):
\[
\mathrm{TPS}=\frac{B}{\sum_{l=1}^{L}T_{layer}^{(l)}}
\]

Metric bindings:
- Eq. (2)-(3) -> `bridge_contention_ms_total`, `hbf_miss_penalty_ms_total`.
- Eq. (1) -> `overlap_efficiency`, `latency_p99_ms`.
- Eq. (4) -> `tokens_per_sec`.

Equation-to-result consistency is validated in `results/tables/simulator_sanity_checks.md` and `results/summary/causal_chain_analysis.md`.

## 7. Experimental Method
### 7.1 Fairness policy
All baselines share identical:
- batch/context/chunk
- HBM/HBF/SRAM capacity
- HBM/HBF/bridge bandwidth and HBF latency

Only mechanism knobs vary. Full disclosure: `results/tables/baseline_fairness.md`.

### 7.2 Baselines
- AFO_full
- HBM_only_GPU
- MoSKA_only
- H3_only
- Apple_like_UMA
- vLLM_like / FlashAttn_like / TensorRTLLM_like (policy-level synthetic)

### 7.3 Stress and sensitivity
- batch/context/experts/chunk/prefetch/shared-KV/sram/hbf-latency/bridge-bw sweeps
- burst/bridge/thermal worst-case scenarios

## 8. Results
### 8.1 Baseline comparison
From `results/tables/baseline_comparison.md`:
- AFO_full: 12.74 tok/s, p99 80.004 ms
- HBM_only_GPU: 12.30 tok/s, p99 82.918 ms

### 8.2 Causal chain validation
From `results/summary/causal_chain_analysis.md`:
- prefetch 0.60 -> 0.95: overlap +0.0108, p99 -6.966 ms
- shared KV ratio 0.30 -> 0.85: reuse +0.2471, batch_gain +1.0515
- bridge BW 3200 -> 6400 GB/s: p99 -56.023 ms, contention -2731.645 ms

Equation (3) predicts lower miss exposure as prefetch rises, which matches the observed p99 reduction in the prefetch sweep.

### 8.3 Tail behavior
From `results/summary/tail_latency_root_cause.md`:
- worst-case tail p99: 804.009 ms
- dominant cause: bridge saturation (100% bottleneck attribution in that scenario)

This is critical because average latency alone hides service-breaking burst behavior.

### 8.4 Thermal coupling
From `results/summary/thermal_impact_analysis.md`:
- thermal_hot and worst_case_tail reach 125 C peak in this policy model
- throughput degrades with thermal throttling and queue amplification

### 8.5 RTL contract-level validation
From `results/rtl/rtl_contract_tb_summary.md`:
- Verilator lint warnings: 0
- Assertion TB status: PASS
- Saturation proxy (backpressure-driven) peak queue depth: 12
- Saturation proxy drain cycles: 13

Interpretation:
- By forcing `i_dma_ready=0`, the RTL queue behavior reproduces the same direction as simulator tail analysis: contention increases queue residency, then drain latency extends after release.
- This is critical because it anchors the causal chain (bridge contention -> tail growth) at the interface-contract level, not only in analytical equations.

## 9. Discussion
A.F.O does not claim that any single primitive is new. The novelty is enforceable cross-tier behavior under constrained interconnect.
- Not composition, but enforced mechanism.
- Not best-effort overlap, but descriptor-coupled overlap.
- Not memory pooling, but tier-local execution semantics.

## 10. Limitations
- Not silicon-ready: no post-layout timing closure, no package-signoff thermal simulation.
- Not production-grade runtime: no full kernel-level integration with vendor stacks.
- Policy-level validation only: simulator is cycle-inspired first-order, and current RTL checks are contract-level proxies rather than full cycle-exact DRAM/NAND timing models.

## 11. Feasibility Roadmap
- Phase 0: architecture specification
- Phase 1: analytical simulator
- Phase 2: runtime mock
- Phase 3: RTL critical-path blocks
- Phase 4: Verilator checks
- Phase 5: FPGA simplification
- Phase 6: OpenROAD ASIC exploration

## 12. Conclusion
A.F.O should be understood as a mechanism-enforcement architecture: it binds placement, routing, and prefetch into a cross-tier execution contract so that overlap remains stable under finite bridge bandwidth. Prior works optimize components; A.F.O enforces system-level contracts.

## 13. References (Core)
1. Ha et al., H3 (IEEE CAL, 2026).
2. Rhee et al., MoSKA (IEEE CAL, 2025).
3. Vaswani et al., Attention Is All You Need (NeurIPS, 2017).
4. Dao et al., FlashAttention (NeurIPS, 2022).
5. Kwon et al., PagedAttention/vLLM (SOSP, 2023).
