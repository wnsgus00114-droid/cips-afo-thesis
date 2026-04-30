# A.F.O Runtime and Compiler Stack

Physical convention:
- Layer 1 (Top): compute die
- Layer 2 (Bottom): memory die with inner HBM ring and outer HBF ring

## 1. Inference Runtime Components
1. Model Loader
- Loads dense/expert weights to HBF RO regions
- Loads shared precomputed KV catalog to HBF
- Mirrors compact indices to HBM metadata region

2. Memory Placement Planner
- Decides tensor/chunk placement across HBM/HBF/SRAM
- Objective: minimize HBF-latency impact on critical path

3. HBM/HBF Allocator
- Maintains separate allocators with unified virtual address assignment
- Supports pinned, hot, warm, and cold allocation classes

4. MoSKA Router Runtime
- Maintains centroid/embedding tables per layer
- Computes top-k shared chunk candidates

5. KV Chunk Manager
- Tracks shared chunk refcounts and runtime KV lifecycle
- Handles eviction from SRAM and warm/cold migration

6. Prefetch Planner
- Uses layer graph + router confidence to issue prefetch hints
- Adjusts prefetch depth (`+1` / `+2`) dynamically

7. Execution Scheduler
- Overlaps compute kernels and DMA operations
- Builds shared-KV batch groups before launching GEMM

8. Graph Compiler Pass
- Rewrites attention subgraphs into shared/unique split
- Injects prefetch pseudo-ops and chunk routing hooks

9. Profiling Tools
- Collects counters (stall, utilization, hit ratio)
- Exports per-layer traces and bottleneck summaries

## 2. Training Runtime Components
1. Weight/Optimizer Tier Planner
- Full FT mode: weights + optimizer states mostly in HBF, hot window staged into HBM/SRAM
- LoRA/PEFT mode: base weights RO in HBF, trainable adapters + grads HBM-hot

2. Activation Manager
- Controls checkpoint ratio and activation offload ratio
- Writes cold activations to HBF and reloads on backward recompute

3. Gradient Accumulation Engine
- Handles micro-batch loop and delayed optimizer step
- Exposes gradient buffer pressure and accumulation depth telemetry

4. Training Prefetch Planner
- Issues forward/backward window prefetch for `W_l`, `W_{l+1}`, optimizer states
- Raises/decreases prefetch depth based on tail/stall feedback

5. Optimizer Step Orchestrator
- Prefetches optimizer state tiles into SRAM/HBM
- Applies fused update and commits to HBF/HBM by priority

6. Adaptive Policy Controller
- Input: tail (`p99`), SRAM pressure, bridge contention, thermal throttle
- Output: updated checkpoint/offload/prefetch policy for next window

## 3. Runtime API Contract (Inference)
```python
allocate_hbm(tensor: TensorDesc) -> Handle
allocate_hbf(tensor: TensorDesc) -> Handle
prefetch_to_sram(tensor_id: str, layer_id: int) -> bool
route_kv_chunks(query: Tensor, top_k: int) -> list[str]
execute_shared_kv_attention(batch_queries: list[Tensor], kv_chunks: list[str]) -> Tensor
execute_unique_attention(query: Tensor, runtime_kv: Tensor) -> Tensor
evict_kv_chunk(chunk_id: str) -> bool
```

## 4. Runtime API Contract (Training)
```python
register_weight(tensor_id: str, size_bytes: int, layer_id: int) -> bool
register_trainable_param(tensor_id: str, size_bytes: int, layer_id: int, peft: bool=False) -> bool
plan_prefetch_layers(current_layer: int, total_layers: int) -> list[int]
prefetch_weight_window(current_layer: int, total_layers: int) -> int
stage_activation(step_id: int, micro_id: int, size_bytes: int, layer_id: int) -> str
offload_activation(tid: str) -> bool
run_micro_step(step_id: int, micro_id: int, layer_id: int, total_layers: int, act_size_bytes: int) -> StepTelemetry
optimizer_step(step_id: int) -> dict
adapt_policy() -> dict
```

## 5. Scheduler State Machine (Training)
- `T_FETCH`: prefetch weight/optimizer window for next micro-step
- `T_FWD`: forward micro-step with checkpoint boundary tagging
- `T_ACT_OFFLOAD`: offload activation shards by policy
- `T_BWD`: backward + recompute for checkpointed nodes
- `T_ACCUM`: gradient accumulation bookkeeping
- `T_OPT`: optimizer state prefetch + fused update
- `T_TUNE`: policy adaptation from telemetry

## 6. Compiler Transform (Training)
Original training graph:
- `Forward -> Backward -> OptimizerStep`

Rewritten graph:
- `checkpoint_region = partition(graph, checkpoint_ratio)`
- `prefetch(W_l+1, opt_l+1)`
- `forward_micro(batch_i, checkpoint_region)`
- `offload_activation(cold_set, offload_ratio)`
- `backward_recompute(checkpoint_region)`
- `grad_accumulate(i)`
- `if i == accum_end: optimizer_step_fused(); tune_policy()`
