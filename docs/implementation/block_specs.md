# A.F.O Block Specification (RTL/Sim Priority)

## 1. CPU Control Cluster
- Role: boot, command submission, MMIO setup, exception handling
- Inputs: host commands, interrupt lines, perf counter read requests
- Outputs: scheduler commands, DMA descriptor base pointers, routing policy registers
- Internal state: command ring head/tail, fault status, watchdog
- Protocol: AXI-Lite MMIO + doorbell registers
- Difficulty: Medium
- Priority: simulate first, RTL later (microcontroller stub first)

## 2. Tensor/Matrix Accelerator
- Role: dense/FFN GEMM tiles, fused bias+activation
- Inputs: weight/activation tiles from SRAM, control micro-ops
- Outputs: output tiles to SRAM, done events
- Internal state: tile descriptors, accumulator banks, micro-op PC
- Protocol: local SRAM read/write + command FIFO
- Difficulty: High
- Priority: RTL early (simplified systolic tile)

## 3. Shared KV Attention Engine
- Role: shared-KV attention batched GEMM path
- Inputs: query batches, selected shared-KV chunk descriptors
- Outputs: attention outputs and partial logits
- Internal state: batch aggregation table, chunk reuse counters
- Protocol: AXI-Stream to matrix backend + metadata sideband
- Difficulty: High
- Priority: simulator first, RTL after scheduler stabilization

## 4. Unique KV Attention Engine
- Role: per-request runtime-KV attention GEMV-like path
- Inputs: single-query vectors, runtime KV pages
- Outputs: per-request attention output
- Internal state: sequence pointer cache, page walker state
- Protocol: AXI-Stream + HBM pointer indirection reads
- Difficulty: Medium
- Priority: simulator first

## 5. SRAM Scratchpad Subsystem
- Role: unified staging/caching for weights/KV/activations
- Inputs: DMA writes, compute writes
- Outputs: compute reads, DMA reads (for writeback)
- Internal state: bank allocator bitmap, ECC status, partition ownership map
- Protocol: banked multi-port local bus
- Difficulty: High
- Priority: RTL early

## 6. HBM Controller Model
- Role: high-bandwidth, low-latency memory service timing
- Inputs: read/write bursts
- Outputs: completion events and data timing
- Internal state: channel queue depths, FR-FCFS scheduler model
- Protocol: transaction-level simulator interface
- Difficulty: Medium
- Priority: simulator first

## 7. HBF Controller Model
- Role: high-capacity NAND-backed memory with higher latency
- Inputs: mostly read bursts, sparse writes
- Outputs: delayed completions
- Internal state: read pipeline delay line, outstanding map
- Protocol: transaction-level simulator interface
- Difficulty: Medium
- Priority: simulator first

## 8. Unified Address Decoder
- Role: route accesses by region prefix to HBM/HBF/SRAM
- Inputs: physical address + transaction attributes
- Outputs: target select + fault code
- Internal state: region map registers (optional remap)
- Protocol: fabric sideband
- Difficulty: Low
- Priority: RTL now

## 9. Silicon Bridge Interface
- Role: packetize and arbitrate VN0/VN1/VN2 traffic over bridge
- Inputs: routed requests from UMC
- Outputs: flits to memory layer, completions back
- Internal state: credit counters, QoS token bucket
- Protocol: custom flit protocol
- Difficulty: High
- Priority: sim first + RTL-lite model

## 10. DMA Engine
- Role: descriptor-driven HBM/HBF<->SRAM transfer
- Inputs: descriptor ring entries
- Outputs: SRAM writes, completion interrupts
- Internal state: descriptor queue, outstanding burst table
- Protocol: AXI-MM master + completion queue
- Difficulty: High
- Priority: RTL now

## 11. Prefetch Engine
- Role: issue next-layer prefetch (weights + KV + metadata)
- Inputs: layer graph hints + router hints + perf counters
- Outputs: DMA descriptors with QoS tags
- Internal state: prefetch confidence table, layer window pointer
- Protocol: MMIO config + descriptor push
- Difficulty: High
- Priority: RTL-lite now, full policy in runtime first

## 12. KV Cache Manager
- Role: lifecycle and tiering of shared/unique KV chunks
- Inputs: allocation events, hit/miss events, eviction pressure
- Outputs: placement/eviction actions, hotness updates
- Internal state: refcount table, hotness histogram, LRU queues
- Protocol: runtime software API + hardware event taps
- Difficulty: Medium
- Priority: runtime first

## 13. MoE Router
- Role: top-k relevant chunk expert selection per query
- Inputs: query embeddings, chunk centroid table
- Outputs: top-k chunk IDs + confidence
- Internal state: ANN index cache, quantized centroid memory
- Protocol: stream input/output + SRAM metadata reads
- Difficulty: High
- Priority: simulator first, RTL accelerator later

## 14. Global Scheduler
- Role: overlap compute and memory movement at layer granularity
- Inputs: completion events, queue occupancy, router outputs
- Outputs: kernel launch order, prefetch trigger
- Internal state: dependency DAG, ready queues
- Protocol: runtime scheduler API + MMIO for HW assist
- Difficulty: High
- Priority: runtime first

## 15. Performance Counters
- Role: observability for utilization and stall diagnosis
- Inputs: event pulses from each block
- Outputs: counter snapshots
- Internal state: saturating counters, histogram bins
- Protocol: MMIO read window
- Difficulty: Low
- Priority: RTL now
