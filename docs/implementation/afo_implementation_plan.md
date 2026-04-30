# A.F.O Implementation Roadmap (Concept -> Prototype)

## 1. System Overview
A.F.O is implemented as a co-designed stack:
- hardware microarchitecture (compute + H3 memory)
- runtime scheduler (MoSKA + prefetch)
- compiler graph pass (shared-KV batching + prefetch injection)
- simulators (analytical + cycle-ish)
- RTL prototypes for critical data movement path

Fixed packaging convention used in this roadmap:
- Layer 1 (top): compute die
- Layer 2 (bottom): memory die with inner HBM rectangular ring and outer HBF rectangular ring

Target artifacts are aligned to five prototype levels:
1. software simulator
2. cycle-level / analytical simulator
3. RTL block prototype
4. FPGA-feasible simplified prototype
5. ASIC-oriented flow (OpenROAD)

## 2. Block-level Architecture (Implementable Modules)

| Block | Role | Inputs/Outputs | Internal State | Interface | Difficulty | First Step |
|---|---|---|---|---|---|---|
| CPU Control Cluster | command/control, exception, orchestration | cmd in, status out | command queues, MMIO state | AXI-Lite MMIO | M | Sim-first |
| Tensor/Matrix Accelerator | GEMM/FFN compute | tiles in/out | tiling FSM, accumulators | AXI-Stream + local SRAM ports | H | RTL early |
| Shared KV Attention Engine | batched shared-KV attention | query batch + KV chunks | chunk-map, batching queues | AXI-Stream | H | Sim-first then RTL |
| Unique KV Attention Engine | per-request runtime-KV attention | query + runtime KV | sequence pointer tables | AXI-Stream | M | Sim-first |
| SRAM Scratchpad | unified staging/cache | DMA read/write + compute read/write | bank allocation, ECC | multi-port banked interface | H | RTL early |
| HBM Controller Model | model fast-tier memory service | req/resp | queue depth, timing model | transaction-level | M | Sim-first |
| HBF Controller Model | model capacity-tier memory service | req/resp | large latency pipeline, wear model (optional) | transaction-level | M | Sim-first |
| Unified Address Decoder | route by region tags | addr requests in, routed req out | region table registers | bus fabric sideband | L | RTL now |
| Silicon Bridge IF | bridge VN QoS and credits | packetized traffic | credit counters, VN arbiter | flit interface | H | Sim-first + RTL simplified |
| DMA Engine | bulk transfer HBM/HBF<->SRAM | descriptors in, completion out | desc ring, outstanding table | AXI-MM + AXI-Stream | H | RTL now |
| Prefetch Engine | layer+router-aware prefetch | graph hints + router hints | prefetch queue, confidence table | MMIO + DMA descriptor push | H | RTL now (reduced) |
| KV Cache Manager | KV lifecycle + hot/cold placement | KV events in, alloc/evict out | chunk refcount, hotness, LRU | runtime API | M | runtime first |
| MoE Router | query->top-k chunk experts | query embedding in, top-k out | centroid table/index | stream + SRAM table | H | sim-first, RTL-lite later |
| Global Scheduler | overlap compute/memory | task graph in/out | dependency DAG, token queues | runtime API + MMIO | H | runtime first |
| Perf Counters | observability | event taps | counters, histograms | MMIO read | L | RTL now |

## 3. RTL Module Hierarchy
```text
afo_top
 ├─ afo_ctrl_cluster
 ├─ afo_noc_lite
 ├─ afo_addr_decoder
 ├─ afo_dma_engine
 ├─ afo_prefetch_engine
 ├─ afo_kv_sched
 ├─ afo_sram_subsys
 │   ├─ afo_sram_bank[0..31]
 │   └─ afo_sram_allocator
 ├─ afo_matrix_accel
 ├─ afo_shared_kv_engine
 ├─ afo_unique_kv_engine
 ├─ afo_bridge_if
 ├─ afo_hbm_model_if
 ├─ afo_hbf_model_if
 └─ afo_perf_counters
```

## 4. Top-level Bus and MMIO Plan
- Control plane: AXI-Lite (32-bit addr, 64-bit data)
- Data plane: AXI4-like burst channels + lightweight stream fabric
- MMIO window (example):
  - `0x0000_0000` `CTRL_STATUS`
  - `0x0000_1000` `DMA_DESC_BASE`
  - `0x0000_2000` `PREFETCH_CFG`
  - `0x0000_3000` `KV_SCHED_CFG`
  - `0x0000_4000` `ROUTER_CFG`
  - `0x0000_5000` `PERF_COUNTER_BASE`

## 5. DMA + Prefetch Datapath
1. runtime/compiler writes descriptor rings
2. prefetch engine expands layer hints into DMA descriptors
3. DMA classifies request class:
- class 0: urgent (LHB refill)
- class 1: next-layer critical
- class 2: background warmup
4. descriptor completion triggers scheduler event

Descriptor format (128-bit):
- src_addr[51:0]
- dst_sram_bank[7:0]
- size_bytes[19:0]
- qos[1:0]
- layer_id[7:0]
- tensor_kind[3:0]
- checksum/parity

## 6. SRAM Banking Strategy
- 32 banks x 24 MB = 768 MB
- Interleave granularity: 256B line
- Static partition plus elastic steal:
  - banks 0-15: weight A/B
  - banks 16-23: KV A/B
  - banks 24-27: activations
  - bank 28: metadata
  - banks 29-31: LHB / overflow
- allocator can borrow up to 4 banks across partitions under low pressure

## 7. HBM/HBF Address Region Mapping
See `[memory_map.md](./memory_map.md)` for full table.
Core routing logic:
- `addr[51:48] in {0x0,0x1,0x2,0x3}` -> HBF path
- `addr[51:48] in {0x8,0x9,0xA}` -> HBM path
- `addr[51:48] == 0xF` -> on-die SRAM aperture

## 8. Software Simulator Design
`sim/afo_simulator.py` models:
- HBM/HBF bandwidth/latency and queueing
- bridge VN bandwidth share
- SRAM capacity and hit ratio
- layer pipeline overlap
- MoSKA shared KV batching
- router top-k and prefetch accuracy
- stall cycles and OOM conditions
- throughput-per-watt approximation

Input knobs:
- model size, layers, hidden size, experts
- kv chunk size, batch size, context length
- HBM/HBF/SRAM capacities
- per-tier bandwidth/latency values

Outputs:
- csv per run
- utilization metrics
- memory bottleneck %

## 9. Runtime / Compiler Plan
Runtime packages:
- model loader
- placement planner
- HBM/HBF allocator
- KV manager
- prefetch planner
- execution scheduler

Compiler pass goals:
- detect shared-KV opportunities
- cluster query sets for batched GEMM
- inject `prefetch_to_sram()` pseudo-ops

API surface (initial):
- `allocate_hbm(tensor)`
- `allocate_hbf(tensor)`
- `prefetch_to_sram(tensor_id, layer_id)`
- `route_kv_chunks(query, top_k)`
- `execute_shared_kv_attention(batch_queries, kv_chunks)`
- `execute_unique_attention(query, runtime_kv)`
- `evict_kv_chunk(chunk_id)`

## 10. One-token Inference Flow (Runtime)
1. load model/metadata into HBF/HBM index
2. receive request batch and update runtime KV pointers
3. router selects top-k shared KV chunks
4. issue Layer N+1 prefetch descriptors while computing Layer N
5. run shared-KV attention (batched GEMM path)
6. run unique-KV attention (GEMV path)
7. run expert FFN compute and write new runtime KV
8. emit next token and advance sequence state

## 11. Milestones
### Phase 0 - Spec freeze
- Deliverables: architecture spec + memory map + interfaces
- Success: no unresolved interface ambiguity

### Phase 1 - Python analytical simulator
- Deliverables: `sim/afo_simulator.py`, configs, tests
- Success: reproduces monotonic trends vs batch/context

### Phase 2 - Runtime mock
- Deliverables: `runtime/afo_runtime.py`, scheduler model
- Success: can execute token loop with synthetic workload

### Phase 3 - RTL critical path
- Deliverables: address decoder, DMA, prefetch, SRAM, simple matrix accel
- Success: Verilator passes directed tests

### Phase 4 - Verilator system sim
- Deliverables: `rtl/tb` integration tests, VCD traces
- Success: overlap pipeline visible, no deadlock

### Phase 5 - FPGA simplified prototype
- Deliverables: reduced SRAM, DDR model, build scripts
- Success: end-to-end token demo on board

### Phase 6 - OpenROAD experiment
- Deliverables: synthesized netlist + PPA snapshot
- Success: timing closure at target frequency for reduced block set

## 12. First Coding Task List
1. implement simulator core timing model and CSV writer
2. implement runtime APIs as executable stubs
3. build RTL stubs with consistent interface types
4. add directed tests for address decode and DMA descriptor flow
5. add experiment scripts to sweep chunk size and top-k
