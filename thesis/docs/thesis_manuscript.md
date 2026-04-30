# A.F.O (All For One): 3D Integrated AC/DC Silicon for MoSKA + H3 LLM Inference

## Abstract
A.F.O는 장문맥 LLM 추론에서 가장 병목이 되는 KV cache 메모리 접근을 해결하기 위해 설계된 3D 통합 AI 칩 아키텍처다. 본 설계는 (1) Apple Silicon 유사 통합 Compute SoC, (2) MoSKA 기반 Shared/Unique KV 분리 실행, (3) H3형 HBM+HBF 하이브리드 메모리 계층을 단일 패키지로 결합한다. A.F.O는 Shared KV를 chunk 단위로 HBF에 저장하고, runtime KV를 HBM에 유지하며, Layer-N 계산 중 Layer-(N+1) weight/KV/routing metadata를 SRAM A/B 버퍼와 LHB로 선적재한다. 이를 통해 메모리 바운드 GEMV 경로를 Shared-KV GEMM 경로로 전환하고, 브리지/메모리 지연을 계산과 오버랩한다.

---

## 1. Introduction
### 1.1 Problem Setting
LLM serving의 decode 단계는 토큰 생성마다 attention을 반복 수행하므로 다음 두 문제가 누적된다.
1. KV cache 용량이 요청 수와 문맥 길이에 비례해 폭증
2. attention이 메모리 바운드로 고착되어 GPU/NPU 연산 유휴 구간 증가

A.F.O는 이를 하드웨어/런타임/컴파일러 공동 설계 문제로 정의하고, 메모리 위치 결정 자체를 연산 스케줄링의 일부로 취급한다.

### 1.2 Design Objective
A.F.O의 설계 목적은 다음 세 가지를 동시에 만족하는 것이다.
1. **Capacity scaling**: 장문맥에서도 HBM 용량 한계 회피
2. **Bandwidth efficiency**: shared context 재사용 극대화
3. **Latency hiding**: HBF 고지연을 사전적재+LHB로 은닉

---

## 2. System Architecture

## 2.1 3D Package
A.F.O 패키지는 2-layer 3D 적층 구조다.

- Layer 1 (Top): Compute SoC
  - CPU cluster
  - GPU-like SIMT array
  - NPU/matrix array
  - Unified SRAM (scratchpad + cache-like staging)
  - DMA/prefetch complex
  - KV scheduler
  - MoE router hardware

- Layer 2 (Bottom): H3 memory
  - Inner rectangular HBM3 ring (low-latency, full compute-footprint surround)
  - Outer rectangular HBF ring (high-capacity NAND-based memory, surrounds HBM ring)
  - Address decode/router macro

- Interconnect:
  - Silicon Bridge (EMIB-like)
  - VN0/VN1/VN2 QoS virtual network

참조 피겨:
- ![chip](./assets/figures/fig_chip_3d_annotated.png)
- ![system](./assets/figures/fig_system_3d_annotated.png)

## 2.2 Unified Compute Data Path
A.F.O는 두 attention 경로를 분리한다.
1. Shared KV path: batched GEMM
2. Unique KV path: per-request GEMV

이후 FFN/MoE compute가 NPU matrix pipeline으로 이어진다.

---

## 3. Memory Hierarchy and Addressing

## 3.1 Tier Roles
- HBM:
  - runtime KV hot pages
  - activation tensors
  - routing metadata cache
- HBF:
  - dense/expert model weights (RO)
  - shared precomputed KV chunks (RO)
  - cold KV spill

## 3.2 Unified Address Space
A.F.O는 prefix decode 방식의 unified physical map을 사용한다.

\[
\text{target}(A)=
\begin{cases}
\text{HBF}, & A[51:48]\in\{0,1,2,3\}\\
\text{HBM}, & A[51:48]\in\{8,9,A,B\}\\
\text{SRAM}, & A[51:48]=F\\
\text{FAULT}, & \text{otherwise}
\end{cases}
\]

## 3.3 SRAM Partition
- WEIGHT\_BUF\_A/B
- KV\_BUF\_A/B
- ACT\_RING
- META\_BUF
- LHB (Latency Hiding Buffer)

Double buffering과 emergency LHB refill을 결합해 prefetch miss의 직접 stall 전파를 방지한다.

---

## 4. MoSKA + H3 Integration

## 4.1 Shared/Unique KV Separation
각 query에 대해 attention 입력을 다음으로 분해한다.

\[
\mathrm{Attn}(Q, K, V) = \mathrm{Fuse}\left(
\underbrace{\mathrm{Attn}_{\text{shared}}(Q, K_s, V_s)}_{\text{batched GEMM}},
\underbrace{\mathrm{Attn}_{\text{unique}}(Q, K_u, V_u)}_{\text{GEMV-like}}
\right)
\]

Shared KV는 chunk catalog에서 top-k routing으로 선택되고, 동일 chunk signature를 갖는 요청들을 모아 GEMM 타일로 실행한다.

## 4.2 Chunk Routing
MoE-style router는 query embedding과 chunk centroid 간 유사도를 계산한다.

\[
\mathcal{C}_{top-k}(q)=\operatorname{TopK}_{c\in\mathcal{C}}
\left(\frac{q\cdot e_c}{\|q\|\|e_c\|}\right)
\]

여기서 \(e_c\)는 chunk \(c\)의 대표 임베딩이다.

## 4.3 Tiered Placement
- \(K_s,V_s\): HBF 저장, hot subset은 SRAM/HBM mirror
- \(K_u,V_u\): HBM append arena

---

## 5. Layer Pipeline and Prefetch

## 5.1 Overlap Schedule
Layer \(N\) 계산 중 동시에 Layer \(N+1\) 데이터를 선적재한다.

1. weight tile prefetch (HBF→SRAM-B)
2. shared KV chunk prefetch (HBF/HBM→SRAM-B)
3. runtime KV page prefetch (HBM→SRAM-B)
4. routing metadata prefetch (HBM→META-B)

다음 레이어 시작 시 B를 소비하고 A를 refill한다.

## 5.2 Timing Model
레이어 시간은 다음과 같이 모델링한다.

\[
T_{layer}=\max(T_{compute}, T_{mem}) + T_{router}
\]

\[
T_{mem}=\max\left(\frac{B_{hbm}}{BW_{hbm}},\;\frac{B_{hbf}}{BW_{hbf}}+\Delta_{miss},\;\frac{B_{bridge}}{BW_{bridge}}\right)
\]

\[
\Delta_{miss}= (1-p_{pref})\cdot(L_{hbf}+\alpha\cdot\frac{B_{hbf}}{BW_{hbf}})
\]

---

## 6. Detailed 3D Figure Explanation

## 6.1 Chip-level 3D Figure
`fig_chip_3d_annotated`는 다음을 동시에 표시한다.
1. Layer-1 compute floorplan (CPU/GPU/NPU/SRAM)
2. Layer-2 nested rectangular ring placement (inner HBM, outer HBF)
3. silicon bridge slab
4. data critical path callout
5. latency hiding buffer 역할

각 색상 규칙:
- 파랑: compute die/CPU
- 보라: GPU-SIMT
- 주황: NPU/HBF
- 청록: SRAM/KV staging
- 녹색: HBM
- 갈색: bridge

## 6.2 System-level 3D Figure
`fig_system_3d_annotated`는 칩을 포함한 전체 하드웨어를 보여준다.
1. main board
2. A.F.O package and socket
3. VRM phase array
4. heatsink + fan
5. CXL/PCIe extension slots
6. host-side memory modules

이 피겨는 연구자뿐 아니라 시스템 엔지니어/투자자 관점에서도 병목 위치(전력, 열, 인터커넥트)를 직관적으로 읽을 수 있게 설계했다.

---

## 7. Performance and Power Modeling

## 7.1 Throughput
\[
\mathrm{TPS}=\frac{B}{\sum_{l=1}^{L} T_{layer}^{(l)}}
\]

여기서 \(B\)는 decode batch size, \(L\)은 layer 수다.

## 7.2 Power
\[
P_{total}=P_{compute}+P_{hbm}+P_{hbf}+P_{sram}+P_{bridge}
\]

\[
P_{compute}=P^{peak}_{compute}\cdot U_{compute}
\]
\[
P_{hbm}=P^{peak}_{hbm}\cdot U_{hbm},\quad
P_{hbf}=P^{peak}_{hbf}\cdot U_{hbf}
\]

## 7.3 Throughput per Watt
\[
\mathrm{TPW}=\frac{\mathrm{TPS}}{P_{total}}
\]

---

## 8. Experimental Protocol

## 8.1 Baselines
1. HBM-only GPU baseline
2. MoSKA-only baseline
3. H3-only baseline
4. Apple-like UMA baseline

## 8.2 Sweeps
1. Batch size scaling
2. Context length scaling
3. Number of experts scaling
4. KV chunk size sweep
5. HBF usage ratio sweep
6. Prefetch accuracy sweep
7. LHB on/off ablation

## 8.3 Metrics
- tokens/sec
- latency(ms/token)
- HBM/HBF/bridge utilization
- SRAM hit ratio
- memory bottleneck %
- stall ratio
- throughput per watt

---

## 9. Hardware/RTL Implementation Notes

1. Address decoder는 prefix decode와 fault gating을 통해 invalid prefetch issue를 차단
2. DMA queue는 enqueue/dequeue 동시 처리에서 qcount 일관성 보장
3. TB assertion은 descriptor order/주소/레이어/fault/no-enqueue-on-invalid를 검증
4. Verilator trace로 VCD 파형을 생성해 스케줄 동작을 파형 레벨로 검토 가능

---

## 10. 3D Interactive Delivery for GitHub
GitHub에서 마우스로 회전하며 볼 수 있도록 OBJ/STL를 함께 제공한다.

- Chip package model
  - `thesis/docs/assets/models/afo_chip_package_3d.obj`
  - `thesis/docs/assets/models/afo_chip_package_3d.stl`

- Full hardware system model
  - `thesis/docs/assets/models/afo_hardware_system_3d.obj`
  - `thesis/docs/assets/models/afo_hardware_system_3d.stl`

또한 로컬/웹에서 더 자세한 인터랙션을 위해 Three.js 뷰어 페이지를 제공한다.

---

## 11. Limitations
1. 현재 모델은 analytical + cycle-inspired 하이브리드이며 full NAND firmware model은 미포함
2. router ANN microarchitecture는 기능 모델 중심
3. thermal transient 및 package warpage 연동은 future work

---

## 12. Conclusion
A.F.O는 단순 메모리 증설이 아니라, **shared/unique KV 계산 경로 분할 + H3 계층 배치 + 선적재 파이프라인**을 묶어 메모리 병목을 연산 스케줄링 문제로 재정의한 구조다. 본 문서와 코드/모델/3D 자산은 논문 제출과 오픈소스 공개를 동시에 만족하도록 구성되어 있다.

---

## References (selected)
상세 BibTeX는 `thesis/paper/references.bib` 참조.

1. Vaswani et al., "Attention Is All You Need," NeurIPS 2017.
2. Dao et al., "FlashAttention," NeurIPS 2022.
3. Lepikhin et al., "GShard," ICLR 2021.
4. Fedus et al., "Switch Transformers," JMLR 2022.
5. Shoeybi et al., "Megatron-LM," SC 2019.
6. Narayanan et al., "Efficient Large-Scale LM Training on GPU Clusters," SC 2021.
7. Kwon et al., "PagedAttention with vLLM," SOSP 2023.
8. Kim et al., "A Neural Cache Model for Long-Context Serving" (context systems references).
9. Ha, Kim, Kim, "H3: Hybrid Architecture Using HBM and HBF," IEEE CAL 2026.
10. Rhee et al., "MoSKA: Mixture of Shared KV Attention," IEEE CAL 2025.
