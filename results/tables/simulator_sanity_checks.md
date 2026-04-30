# Simulator Sanity Validation

This report addresses reviewer concern: "How do we trust the simulator?"

## Validation Policy
- Anchor checks compare normalized baseline behavior against known system trends.
- Trend checks verify causal sweep direction under a fixed fairness contract.
- Analytical-vs-measured linkage checks bound model error.

## Summary: 7 PASS / 0 FAIL

| Check | Status | Evidence | Rationale |
|---|---|---|---|
| Anchor-1: AFO throughput exceeds HBM-only baseline | PASS | AFO=12.74 tok/s vs HBM-only=12.30 tok/s | Cross-tier routing + overlap contract should outperform plain HBM-only scheduling. |
| Anchor-2: AFO p99 latency lower than HBM-only baseline | PASS | AFO p99=80.004 ms vs HBM-only p99=82.918 ms | Route-aware prefetch and LHB should reduce exposed miss latency. |
| Anchor-3: vLLM/Flash/TRT-like trends are in expected normalized envelopes | PASS | vLLM_like=1.026x, Flash_like=1.019x, TensorRTLLM_like=1.029x (vs HBM-only=1.0x) | Synthetic baselines should follow known directional trends without implausible speedups. |
| Trend-bridge_bw_gbs: corr(bridge_bw_gbs, latency_p99_ms) negative | PASS | corr=-0.966; points=5 | Sensitivity should preserve expected direction under fixed constraints. |
| Trend-prefetch_accuracy: corr(prefetch_accuracy, overlap_efficiency) positive | PASS | corr=1.000; points=5 | Sensitivity should preserve expected direction under fixed constraints. |
| Trend-shared_kv_ratio: corr(shared_kv_ratio, tokens_per_sec) positive | PASS | corr=1.000; points=4 | Sensitivity should preserve expected direction under fixed constraints. |
| Model-link sanity: mean analytical error below 35% | PASS | mean(model_error_pct)=27.23% | Cycle-inspired simulator remains first-order; error bound must stay moderate. |

## Interpretation
- If all checks pass, simulator outputs are directionally consistent with known-system behavior and internal equations.
- If failures appear, they indicate either unrealistic parameterization or missing mechanism terms requiring model revision.