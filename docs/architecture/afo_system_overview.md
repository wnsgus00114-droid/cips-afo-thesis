# A.F.O (All For One) AC/DC Silicon Chip - System Overview

## 1. Design Point (Concrete Target)
- Workload: MoE LLM decode-heavy serving + long-context prefilling
- Process target: 5nm-class compute die + 3D memory layer
- Package: 3.5D hybrid package (`Active Base Die + central 3D compute bonding + periphery 2.5D memory ring`)
- Aggregate memory:
  - HBM3: 8 stacks x 24 GB = 192 GB, peak 6.4 TB/s
  - HBF (NAND-based high-capacity): 2 TB, prototype assumption peak 4.8 TB/s, 4-8 us read latency
- On-die SRAM: 768 MB banked unified SRAM
- Main objective: move shared/cold KV and static weights to HBF while keeping runtime/hot KV in HBM/SRAM

## 2. Full Architecture Diagram (Text)
```text
+--------------------------------------------------------------------------------+
|                           A.F.O 3D PACKAGE (Top View)                         |
|                                                                                |
|   [Compute Layer (Top): Apple-like Unified SoC]                               |
|   +--------------------------------------------------------------------------+ |
|   | CPU Cluster | MoE Router HW | Prefetch Engine | Unified Memory Ctrl     | |
|   | GPU-SIMT Array | NPU/Matrix Array | Shared KV Attention Engine          | |
|   | Unique KV Attention Engine | DMA Complex | KV Cache Scheduler           | |
|   |                  768MB Banked Unified SRAM + LHB                         | |
|   +------------------------Silicon Bridge / EMIB-like Fabric----------------+ |
|                                                                                |
|   [Layer2 Active Base Die (Bottom): logic interposer + HBM/HBF ring mount]    |
|   +--------------------------------------------------------------------------+ |
|   | Outer Ring: HBF (RO weights/shared KV/cold KV)                          | |
|   | Inner Ring: HBM3 (runtime KV/activations/hot metadata)                  | |
|   |          both rectangular rings fully surround Layer-1 compute          | |
|   +--------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------+
```

## 3. 3D Chip Layout Description
- Layer 1 (Top, compute):
  - Central crossbar/NoC ring around unified SRAM banks
  - North: CPU + command processor + runtime microcontroller
  - East/West: GPU-like SIMT clusters and NPU matrix clusters
  - South: DMA/prefetch/KV scheduler + memory interface PHY
- Layer 2 (Bottom, memory):
  - Active Base Die includes metadata routing, LHB emergency path, and VN arbitration logic
  - Inner rectangular ring: HBM surrounds entire Layer-1 compute footprint
  - Outer rectangular ring: HBF surrounds the HBM ring
  - This nested ring topology regularizes ingress distance and simplifies bridge lane planning
  - Memory stacks are mounted on periphery through 2.5D micro-bumps while compute is centrally bonded by 3D hybrid TSV
  - Silicon bridge lanes segmented into 3 virtual networks:
    - VN0: latency-critical runtime KV/activations
    - VN1: bulk read-only weights/shared KV
    - VN2: metadata/prefetch control

## 4. Memory Hierarchy
- L0: register files and local SRAM in compute clusters (64 KB-512 KB per cluster)
- L1: unified on-die SRAM (768 MB, 32 banks, ECC)
- L2a: HBM3 (runtime KV, activations, hot chunks)
- L2b: HBF (model weights, shared KV, cold chunks)
- Address space: single 52-bit virtual physical map with H3 decode bits

### H3 placement policy
- HBM (fast tier):
  - per-request runtime KV
  - current/next layer activations
  - hot shared KV chunk replicas
- HBF (capacity tier):
  - full model weights (RO)
  - shared precomputed KV library (RO)
  - cold/evicted KV chunks

## 5. MoSKA + H3 Integration (Concrete)
- Shared KV (read-only):
  - Stored in HBF as chunked tensor blocks: `(chunk_id, layer, head_group, token_block, d_k)`
  - Chunk index table mirrored in HBM for fast lookup
- Unique KV (per request):
  - Appended in HBM runtime KV arena
  - Active pages staged in SRAM by KV scheduler
- Routing:
  - MoE router computes top-k chunk experts per query
  - Shared KV attention engine batches requests with identical chunk sets to run GEMM tiles
  - Unique KV attention engine runs GEMV-like path with low batching overhead

## 6. KV Cache Pipeline (Layer N -> N+1)
```text
Time t0 (Layer N compute)
  - Matrix/NPU executes Layer N attention + FFN
  - Prefetch Engine issues DMA descriptors for Layer N+1:
    * weights tiles (HBF->SRAM buffer B)
    * shared KV chunks top-k (HBF/HBM->SRAM KV buffer B)
    * runtime KV pages (HBM->SRAM KV buffer B)
    * routing metadata (HBM->SRAM META B)

Time t1 (Layer N finalize)
  - KV scheduler commits new runtime KV to HBM append log
  - Hotness counters updated

Time t2 (Layer N+1 start)
  - Compute consumes SRAM buffer B immediately
  - Buffer A becomes refill target for Layer N+2
```

## 7. SRAM Double Buffer + LHB Design
- SRAM partition (768 MB):
  - Weight Tile Buffers: 2 x 192 MB (A/B ping-pong)
  - KV Stage Buffers: 2 x 96 MB (A/B ping-pong)
  - Activation Ring: 3 x 32 MB (triple-buffer)
  - Metadata + Routing: 32 MB
  - Latency Hiding Buffer (LHB): 64 MB (urgent miss absorb)
- LHB usage:
  - If predicted chunks miss deadline, emergency DMA fills LHB first
  - Compute can read from LHB while normal KV bank fill continues

## 8. Dataflow Diagram
```text
HBF/HBM -> H3 Addr Router -> Silicon Bridge VN1/VN0 -> DMA -> SRAM(A/B) ->
Shared KV Engine + Unique KV Engine + Matrix Engine -> output activations/runtime KV -> HBM
```

## 9. Address Map (Unified)
- Address width: 52-bit
- Region tags use `[51:48]`

| Region | Prefix | Capacity | Primary Contents | Placement |
|---|---|---:|---|---|
| Dense Weights | 0x0 | 768 GB | attention/MLP base weights | HBF |
| Expert Weights | 0x1 | 768 GB | MoE expert FFN weights | HBF |
| Shared KV RO | 0x2 | 384 GB | precomputed shared KV chunks | HBF |
| Runtime KV Hot | 0x8 | 128 GB | active per-request KV | HBM |
| Activations | 0x9 | 32 GB | layer activations/intermediates | HBM |
| Runtime KV Warm | 0xA | 32 GB | less-active KV pages | HBM |
| Cold KV Spill | 0x3 | 128 GB | cold/evicted KV snapshots | HBF |
| SRAM window | 0xF | 768 MB | mapped on-die SRAM banks | SRAM |

## 10. Bottleneck Analysis (First-order)
- HBF latency (4-8 us) is dominant for mispredicted shared-KV fetch
- Silicon bridge saturation occurs before HBM peak when VN0/VN1 contention rises
- Central TSV neck can dominate tail latency under bursty multi-tenant traffic
- SRAM pressure spikes with large context + high expert entropy
- Router overhead grows with chunk catalog size (ANN search cost)

### Typical per-token limiting mode
- Small batch: latency-bound by HBF misses + routing
- Medium batch: bridge-bandwidth-bound
- Large batch: compute-bound in shared KV GEMM and NPU FFN

## 11. Optimization Knobs
- KV chunk size: 64-256 KB
  - <64 KB: too much metadata/dispatch
  - >256 KB: overfetch and SRAM fragmentation
- Router top-k: dynamic k (2->6) based on confidence threshold
- SRAM budget split:
  - decode-heavy: increase KV stage buffers
  - prefill-heavy: increase weight tile buffers
- Prefetch distance:
  - default +1 layer, adaptive +2 for HBF-only regions
- Bridge virtual network QoS:
  - reserve 35% VN0 for runtime KV and urgent LHB refill
