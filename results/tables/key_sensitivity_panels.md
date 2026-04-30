# Key Sensitivity Panels (Reviewer Critical)

| Sweep | X range | Y metric | corr(X,Y) | slope(dY/dX) | Expected direction |
|---|---|---|---:|---:|---|
| `bridge_bw_gbs` | `3200.000 -> 6400.000` | `latency_p99_ms` | -0.979 | -0.001559 | negative |
| `tsv_uplink_bw_gbs` | `2800.000 -> 5800.000` | `latency_p99_ms` | -0.975 | -0.024667 | negative |
| `prefetch_accuracy` | `0.600 -> 0.950` | `overlap_efficiency` | 1.000 | 0.013205 | positive |
| `shared_kv_ratio` | `0.300 -> 0.850` | `tokens_per_sec` | 1.000 | 0.011760 | positive |

Related plots:
- `results/plots/bridge_bw_gbs_tail_p99.svg`
- `results/plots/tsv_uplink_bw_gbs_tail_p99.svg`
- `results/plots/prefetch_accuracy_overlap_eff.svg`
- `results/plots/shared_kv_ratio_throughput.svg`