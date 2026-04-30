# A.F.O (All For One)
## Enforcing Cross-Tier Execution Contracts for 3D HBM+HBF LLM Inference Under Finite Bridge Bandwidth

## Abstract
본 연구는 장문맥 LLM 추론에서 발생하는 메모리 벽(memory wall)과 tail latency 문제를 해결하기 위해 A.F.O(3D 통합 AI 칩 아키텍처)를 제안한다. 핵심은 단순 조합이 아니라 **교차 계층 실행 계약(cross-tier execution contract)** 의 강제다. A.F.O는 (1) Top compute die / Bottom memory-tier ring 물리 계약, (2) HBM/HBF tier-locality 메모리 의미론, (3) descriptor-coupled prefetch + SRAM A/B swap + LHB replay 실행 계약을 동시에 강제한다. 본 저장소는 cycle-inspired 시뮬레이터 기반 정책 검증을 제공하며, baseline 공정성 계약, sanity 검증, 민감도 분석, tail root-cause, thermal 영향 분석을 포함한다. 본 결과는 tape-out 성능 주장보다 **아키텍처 실현 가능성 및 메커니즘 검증**에 초점을 둔다.

## 1. Problem Definition
LLM decode 경로는 토큰당 attention 반복으로 인해 다음 문제가 누적된다.
1. runtime KV cache 급증으로 HBM 용량/대역폭 압박 증가
2. shared context 재사용 미흡 시 GEMV 중심의 memory-bound 실행 고착
3. 멀티테넌트 burst 상황에서 bridge 경합으로 p99/p999 tail 급등

기존 접근의 공통 한계:
- 커널 최적화(FlashAttention 계열): 로컬 커널 효율은 개선하나 tier 강제 규칙 부재
- 런타임 페이징(vLLM 계열): 할당 효율 개선은 가능하나 물리 tier-locality를 보장하지 않음
- 메모리 tiering(H3 계열): 용량 효율은 개선하나 burst 시 contention 완화가 자동으로 보장되지 않음

## 2. One-Line Thesis and Contributions
### 2.1 One-Line Thesis
**Prior works optimize components; A.F.O enforces cross-tier execution contracts that make overlap deterministic under bandwidth constraints.**

### 2.2 Main Contributions
1. 물리 계약:
- Layer1(top)=Compute, Layer2(bottom)=Memory
- Layer2는 inner HBM rectangular ring + outer HBF rectangular ring

2. 메모리 의미론 계약:
- HBM: runtime-hot mutable state (runtime KV, activation, metadata)
- HBF: read-mostly state (weights, shared KV catalog, cold chunks)

3. 실행 계약:
- route-aware chunk selection -> descriptor-coupled prefetch
- Layer N compute 중 Layer N+1 데이터 사전 적재
- SRAM A/B swap + LHB miss replay

4. 검증 계약:
- fairness-locked baseline 설계
- simulator sanity checks
- causal chain 분석
- tail root-cause + thermal 영향 분석

## 3. A.F.O Architecture
## 3.1 3D Package Contract
- Top layer (Compute Die): CPU cluster, GPU-like SIMT, NPU/matrix, unified SRAM, DMA/prefetch, KV scheduler, MoE router
- Bottom layer (Memory Tier): HBM inner ring + HBF outer ring + address router
- Interconnect: silicon bridge (finite bandwidth)

참조 경로:
- `docs/implementation/memory_map.md`
- `docs/implementation/dataflow.md`
- `thesis/docs/figure_atlas.md`

## 3.2 Dataflow Contract
\[
\text{HBM/HBF} \rightarrow \text{Bridge} \rightarrow \text{SRAM} \rightarrow \text{Compute}
\]

Shared KV attention은 query batch를 aggregate하여 GEMM화하고, unique KV attention은 per-request GEMV 성격으로 유지한다. 이 분리를 통해 reuse 높은 경로를 compute-bound로 이동시킨다.

## 4. Analytical Model and Traceability
수식은 설명용이 아니라 결과와 직접 연결된다.

\[
T_{layer}=\max(T_{compute}, T_{mem})+T_{router} \tag{1}
\]

\[
T_{mem}=\max\left(\frac{B_{hbm}}{BW_{hbm}},\frac{B_{hbf}}{BW_{hbf}}+\Delta_{miss},\frac{B_{bridge}}{BW_{bridge}}\right) \tag{2}
\]

\[
\Delta_{miss}=(1-p_{pref})(L_{hbf}+\alpha\cdot B_{hbf}/BW_{hbf}) \tag{3}
\]

\[
TPS=\frac{B}{\sum_{l=1}^{L}T_{layer}^{(l)}} \tag{4}
\]

Equation-to-metric 매핑:
- (2),(3) -> `hbf_miss_penalty_ms_total`, `bridge_contention_ms_total`
- (1) -> `overlap_efficiency`, `latency_p99_ms`
- (4) -> `tokens_per_sec`

검증 경로:
- `results/tables/simulator_sanity_checks.md`
- `results/summary/causal_chain_analysis.md`

## 5. Experimental Design (Reviewer-Critical)
## 5.1 Fairness Contract
모든 baseline은 아래 항목을 동일하게 고정한다.
- workload: `batch_size`, `context_len`, `kv_chunk_size_kb`
- capacity: `hbm_capacity_gb`, `hbf_capacity_gb`, `sram_capacity_mb`
- bandwidth/latency: `hbm_bw_gbs`, `hbf_bw_gbs`, `bridge_bw_gbs`, `hbf_latency_us`

오직 정책/메커니즘 변수만 변경한다.
- `shared_kv_ratio`, `weight_hbf_fraction`, `prefetch_accuracy`, `routing_diversity`, `matrix_efficiency`, `lhb_enable`, `prefetch_depth`

증빙:
- `results/tables/baseline_fairness.md`

## 5.2 Simulator Trust Validation
- Anchor checks: AFO vs HBM-only 상대 성능/지연 관계
- Trend checks: bridge BW/latency, prefetch/overlap, shared KV/throughput 방향성 검증
- Model-link checks: `model_error_pct` 평균 bound

증빙:
- `results/tables/simulator_sanity_checks.md` (현재 `7 PASS / 0 FAIL`)

## 5.3 Stress and Tail Protocol
- stress scenarios: `nominal`, `peak_traffic`, `bridge_saturation`, `thermal_hot`, `worst_case_tail`
- tail metrics: `latency_p99_ms`, `latency_p999_ms`, `latency_max_ms`, `tail_ratio_p99_p50`
- root-cause metrics: `bridge_contention_ms_total`, `hbf_miss_penalty_ms_total`, bottleneck attribution

## 6. Results and Interpretation
## 6.1 Baseline Snapshot
`results/tables/baseline_comparison.md` 기준:
- AFO_full: 12.74 tok/s, p99 80.004 ms
- HBM_only_GPU: 12.30 tok/s, p99 82.918 ms

## 6.2 Causal Chain (Mechanism -> Outcome)
`results/summary/causal_chain_analysis.md`:
1. Prefetch accuracy 0.60 -> 0.95
- overlap_efficiency +0.0108
- p99 latency -6.966 ms

2. shared KV ratio 0.30 -> 0.85
- shared reuse +0.2471
- batch_gain +1.0515

3. bridge BW 3200 -> 6400 GB/s
- bridge contention -2731.645 ms
- p99 latency -56.023 ms

핵심 해석:
- KV reuse 증가 -> batch_gain 증가 -> GEMM 경로 유효성 증가
- prefetch 정확도 증가 -> 오버랩 증가 -> 지연 노출 감소
- bridge BW 증가 -> contention 체류 시간 감소 -> tail 완화

## 6.3 Tail Latency Root Cause
`results/summary/tail_latency_root_cause.md`:
- worst-case tail: p99 804.009 ms
- dominant cause: bridge saturation
- nominal 대비 bridge contention +130174.152 ms

이 결과는 "평균 성능"만으로는 시스템 안정성을 평가할 수 없음을 보여준다.

## 6.4 Thermal Coupling
`results/summary/thermal_impact_analysis.md`:
- thermal hotspot에서 throttle 비율 상승
- throughput 하락 및 p99 증가 동반

이는 3D 적층 구조에서 thermal 변수가 큐/타이밍을 직접 흔드는 1차 요인임을 시사한다.

## 7. Related Work Gap (What Fails and Why)
- MoSKA: shared/unique KV 분리라는 중요한 연산 아이디어 제공, 그러나 물리 tier 강제 및 bridge-constrained overlap 계약까지는 확장되지 않음
- H3: HBM+HBF 용량-비용 구조 제시, 그러나 burst 상황의 deterministic overlap 보장 메커니즘 부재
- vLLM/PagedAttention: allocator/runtime 효율 우수, 하지만 3D tier-local execution contract 자체를 강제하지 않음
- FlashAttention: kernel-level 효율 우수, 하지만 multi-tier placement + prefetch contract까지 포함하지 않음

즉 기존 연구는 component를 최적화하고, A.F.O는 cross-tier contract를 강제한다.

## 8. Implementation Feasibility
- SW/analytical prototype: 완료 (`sim/`, `experiments/scripts/`)
- runtime mock: 진행 (`runtime/`)
- RTL critical path 블록: 주소 디코더, DMA, prefetch, SRAM buffer 중심 구현 계획
- FPGA/ASIC flow: OpenROAD 실험 단계로 확장 가능

## 9. Limitations (Strong Form)
1. **Not silicon-ready**
- post-layout timing closure / package-level signoff 없음

2. **Not production-grade**
- vendor kernel + serving stack 통합 검증 미완료

3. **Policy-level validation only**
- simulator는 cycle-inspired 근사 모델이며 cycle-exact RTL 모델이 아님

4. **Thermal model abstraction**
- RC 수준 thermal coupling 모델로 CFD/FEM 기반 정밀 열해석은 future work

## 10. Conclusion
A.F.O의 신규성은 "무엇을 합쳤는가"가 아니라 "무엇을 강제했는가"에 있다. 본 설계는 memory tier, routing descriptor, prefetch schedule, SRAM staging을 단일 계약으로 묶어 finite bandwidth 환경에서 overlap을 결정론적으로 유지하도록 설계되었다. 본 저장소는 그 계약이 실험적으로 어떻게 검증되는지 재현 가능한 형태로 제공한다.

## References (Selected)
1. Vaswani et al., Attention Is All You Need, NeurIPS 2017.
2. Dao et al., FlashAttention, NeurIPS 2022.
3. Kwon et al., PagedAttention / vLLM, SOSP 2023.
4. Ha et al., H3: Hybrid Architecture Using HBM and HBF, IEEE CAL 2026.
5. Rhee et al., MoSKA: Mixture of Shared KV Attention, IEEE CAL 2025.
