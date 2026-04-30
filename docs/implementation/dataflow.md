# A.F.O LLM Token Decode Dataflow (MoSKA + H3)

Topology assumption:
- Layer-2 memory is nested rectangular rings (`HBM inner`, `HBF outer`) around Layer-1 compute.

## 1. End-to-end Path
```text
HBF/HBM -> H3 Address Router -> Silicon Bridge VN -> DMA -> SRAM Stage Buffers ->
[Shared KV Engine | Unique KV Engine | Matrix Engine] -> HBM runtime KV append
```

## 2. Layer N / N+1 Overlap Timeline

| Time Slot | Compute Path | Memory Path | Buffer State |
|---|---|---|---|
| T0 | Execute Layer N attention/FFN | Prefetch Layer N+1 weight tiles from HBF to WEIGHT_BUF_B | WEIGHT_BUF_A consumed, WEIGHT_BUF_B filling |
| T1 | Continue Layer N | Prefetch shared KV chunks and runtime KV pages to KV_BUF_B | KV_BUF_A consumed, KV_BUF_B filling |
| T2 | Finalize Layer N | Load routing metadata for Layer N+1 to META_BUF_B | META_BUF_A consumed, META_BUF_B filling |
| T3 | Execute Layer N+1 from *_B | Start prefetch for Layer N+2 into *_A | A/B swap |

## 3. Shared vs Unique Attention Split
- Shared KV path (MoSKA):
  - route query -> top-k chunk group
  - aggregate requests with identical chunk signature
  - launch batched GEMM tile
- Unique KV path:
  - directly gather request-local runtime KV pages
  - execute GEMV-like attention

## 4. Runtime KV Append
- after each layer/token:
  - write K/V vectors to HBM runtime arena (`0x8*` region)
  - update per-request page table pointer
  - hotness counter increments for chunk reuse prediction

## 5. Failure and Recovery Path
- if prefetch miss (chunk not ready by layer boundary):
  - issue QoS `Q0` emergency fetch into LHB
  - allow compute to read from LHB alias mapping
  - increment `prefetch_miss_counter` and adapt next prefetch distance
