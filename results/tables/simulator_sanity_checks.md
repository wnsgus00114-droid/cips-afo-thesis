# Simulator Sanity Validation

This report addresses reviewer concern: "How do we trust the simulator?"

## Validation Policy
- Anchor checks compare normalized baseline behavior against known system trends.
- Trend checks verify causal sweep direction under a fixed fairness contract.
- Analytical-vs-measured linkage checks bound model error.

## Summary: 9 PASS / 0 FAIL

| Check | Status | Evidence | Rationale |
|---|---|---|---|
| Anchor-1: AFO throughput exceeds HBM-only baseline | PASS | AFO=5.73 tok/s vs HBM-only=5.63 tok/s | Cross-tier routing + overlap contract should outperform plain HBM-only scheduling. |
| Anchor-2: AFO p99 latency lower than HBM-only baseline | PASS | AFO p99=178.058 ms vs HBM-only p99=181.122 ms | Route-aware prefetch and LHB should reduce exposed miss latency. |
| Anchor-3: vLLM/Flash/TRT-like trends are in expected normalized envelopes | PASS | vLLM_like=1.012x, Flash_like=1.009x, TensorRTLLM_like=1.013x (vs HBM-only=1.0x) | Synthetic baselines should follow known directional trends without implausible speedups. |
| Trend-bridge_bw_gbs: corr(bridge_bw_gbs, latency_p99_ms) negative | PASS | corr=-0.979; points=5 | Sensitivity should preserve expected direction under fixed constraints. |
| Trend-tsv_uplink_bw_gbs: corr(tsv_uplink_bw_gbs, latency_p99_ms) negative | PASS | corr=-0.975; points=5 | Sensitivity should preserve expected direction under fixed constraints. |
| Trend-prefetch_accuracy: corr(prefetch_accuracy, overlap_efficiency) positive | PASS | corr=1.000; points=5 | Sensitivity should preserve expected direction under fixed constraints. |
| Trend-shared_kv_ratio: corr(shared_kv_ratio, tokens_per_sec) positive | PASS | corr=1.000; points=4 | Sensitivity should preserve expected direction under fixed constraints. |
| Model-link sanity: mean analytical error below 35% | PASS | mean(model_error_pct)=24.47% | Cycle-inspired simulator remains first-order; error bound must stay moderate. |
| Stress check: TSV neck pressure worsens p99 tail | PASS | nominal p99=179.476 ms, tsv_neck_pressure p99=618.234 ms | Central TSV neck contention should increase tail under bursty multi-tenant load. |

## Interpretation
- If all checks pass, simulator outputs are directionally consistent with known-system behavior and internal equations.
- If failures appear, they indicate either unrealistic parameterization or missing mechanism terms requiring model revision.