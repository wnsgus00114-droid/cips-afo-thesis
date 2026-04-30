# Causal Chain Analysis

This file explicitly links mechanism -> intermediate metric -> final performance.

## Chain A: Prefetch Accuracy -> Overlap -> Tail Latency
- prefetch_accuracy `0.60 -> 0.95`
- overlap_efficiency delta: `+0.0108`
- p99 latency delta: `-6.966 ms`
- corr(prefetch, overlap) = `1.000`
- corr(prefetch, p99) = `-1.000` (expected negative)
- Causal statement: prefetch coverage increase raises overlap and reduces exposed HBF/bridge wait.

## Chain B: KV Reuse -> Batch Gain -> Throughput
- shared_kv_ratio `0.30 -> 0.85`
- shared_kv_reuse_ratio delta: `+0.2471`
- batch_gain delta: `+1.0515`
- throughput delta: `+0.014 tok/s`
- corr(shared_kv_ratio, throughput) = `1.000`
- Causal statement: chunk reuse increases effective GEMM batch formation and improves compute utilization.

## Chain C: Bridge Bandwidth -> Contention -> Tail
- bridge_bw `3200 -> 6400 GB/s`
- bridge_contention_ms_total delta: `-2731.645 ms`
- p99 latency delta: `-56.023 ms`
- corr(bridge_bw, p99) = `-0.966` (expected negative)
- Causal statement: wider bridge reduces contention residency and shrinks long-tail queuing exposure.

## Primary Causal Claims for Paper
1. KV reuse up -> batch_gain up -> shared-path GEMM utilization up.
2. Prefetch accuracy up -> overlap_efficiency up -> p99/p999 latency down.
3. HBF tiering + staging contract -> bridge contention migration down under equal BW constraints.