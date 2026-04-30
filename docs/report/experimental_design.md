# A.F.O Experimental Design (Reviewer Feedback Integrated)

## 0. Physical Topology Constraint
- Top (Layer1): compute chipset
- Bottom (Layer2): memory ring tier
  - inner rectangular HBM ring fully surrounding compute footprint
  - outer rectangular HBF ring fully surrounding HBM ring
- Conformance knobs fixed in runs:
  - `layer1_role=compute_top`
  - `layer2_role=memory_bottom`
  - `hbm_ring_coverage=1.0`
  - `hbf_outer_ring_coverage=1.0`

## 1. Evaluation Metrics
- Throughput/latency: `tokens_per_sec`, `latency_ms_per_token`
- Tail latency: `latency_p90_ms`, `latency_p99_ms`, `latency_p999_ms`, `latency_max_ms`, `tail_ratio_p99_p50`
- Bandwidth and contention: `hbm_util`, `hbf_util`, `bridge_util`, `bridge_contention_ms_total`
- Miss penalties: `hbf_miss_penalty_ms_total`, `prefetch_coverage_ratio`, `lhb_hit_ratio`
- Cache and overlap: `sram_hit_ratio`, `overlap_efficiency`
- Bottleneck attribution: `bottleneck_compute_pct`, `bottleneck_hbm_pct`, `bottleneck_hbf_pct`, `bottleneck_bridge_pct`, `bottleneck_router_pct`
- KV effectiveness: `shared_kv_reuse_ratio`, `batch_gain`
- Thermal/process and power: `thermal_peak_c`, `thermal_avg_c`, `throttling_ratio`, `power_w`, `throughput_per_watt`
- Model linkage: `model_predicted_token_ms`, `model_measured_token_ms`, `model_error_pct`

## 2. Baselines
- `AFO_full`
- `HBM_only_GPU`
- `MoSKA_only`
- `H3_only`
- `Apple_like_UMA`
- `vLLM_like` (policy-level synthetic)
- `FlashAttn_like` (policy-level synthetic)
- `TensorRTLLM_like` (policy-level synthetic)

### 2.1 Baseline Fairness Contract
- Equal workload across baselines:
  - same `batch_size`, `context_len`, `kv_chunk_size_kb`
- Equal bandwidth/latency constraints across baselines:
  - same `hbm_bw_gbs`, `hbf_bw_gbs`, `bridge_bw_gbs`, `hbf_latency_us`
- Equal capacity constraints across baselines:
  - same `hbm_capacity_gb`, `hbf_capacity_gb`, `sram_capacity_mb`
- Only mechanism/policy knobs vary:
  - `shared_kv_ratio`, `weight_hbf_fraction`, `prefetch_accuracy`, `matrix_efficiency`, `routing_diversity`, `LHB`, `prefetch_depth`
- Disclosure artifact:
  - `results/tables/baseline_fairness.md`

## 3. Sweep Experiments
- `batch_size`: `[16, 32, 64, 128, 256]`
- `context_len`: `[1024, 2048, 4096, 8192, 16384]`
- `num_experts`: `[16, 32, 64, 128]`
- `kv_chunk_size_kb`: `[64, 128, 256, 512]`
- `prefetch_accuracy`: `[0.60, 0.70, 0.80, 0.90, 0.95]`
- `shared_kv_ratio`: `[0.30, 0.50, 0.70, 0.85]`
- `sram_capacity_mb`: `[256, 384, 512, 768, 1024]`
- `hbf_latency_us`: `[4, 6, 8, 10, 12]`
- `multi_tenant_users`: `[32, 64, 128, 256, 384]`
- `traffic_burst_factor`: `[1.0, 1.5, 2.0, 2.5, 3.0]`
- `bridge_bw_gbs`: `[3200, 4000, 4800, 5600, 6400]`

## 4. Stress Scenarios (Worst-case/Tail)
- `nominal`
- `peak_traffic`
- `bridge_saturation`
- `thermal_hot`
- `worst_case_tail`

These scenarios jointly vary: concurrent users, burst probability, jitter, bridge bandwidth, prefetch accuracy, HBF latency, and ambient/hotspot thermal parameters.

## 5. Statistical Method
- Multi-seed aggregation per point (default 3 seeds; baseline table uses 5 seeds)
- Output for each point:
  - mean metrics
  - standard deviation (`*_std`)
  - worst markers (`latency_p99_worst_ms`, `latency_max_worst_ms`)
  - throughput percentiles (`tokens_per_sec_p05`, `tokens_per_sec_p95`)

## 6. Simulator Trust / Sanity Validation
- Anchor checks:
  - `AFO_full` must outperform `HBM_only_GPU` in throughput and p99 under same constraints
  - normalized `vLLM_like` / `FlashAttn_like` / `TensorRTLLM_like` trends are bounded to plausible envelopes
- Directional trend checks:
  - `bridge_bw_gbs` vs `latency_p99_ms` (negative correlation expected)
  - `prefetch_accuracy` vs `overlap_efficiency` (positive correlation expected)
  - `shared_kv_ratio` vs `tokens_per_sec` (positive correlation expected)
- Model linkage checks:
  - bound mean `model_error_pct` to avoid unbounded analytical drift
- Artifact:
  - `results/tables/simulator_sanity_checks.md`

## 7. Reproducibility and Artifacts
- Parameter disclosure:
  - `results/sim/parameter_snapshot.json`
  - `results/tables/reproducibility_params.md`
- Raw + aggregated sweep outputs:
  - `results/sim/sweep_*.csv`
  - `results/sim/sweep_*_raw.csv`
- Stress outputs:
  - `results/sim/stress_scenarios.csv`
  - `results/sim/stress_scenarios_raw.csv`
- Training outputs:
  - `results/training/training_sweeps.csv`
  - `results/training/training_scenarios.csv`
  - `results/training_tables/training_sweep_summary.md`
  - `results/training_summary/training_summary.md`
- Tables and summaries:
  - `results/tables/baseline_comparison.md`
  - `results/tables/baseline_fairness.md`
  - `results/tables/simulator_sanity_checks.md`
  - `results/tables/key_sensitivity_panels.md`
  - `results/tables/sweep_summary.md`
  - `results/summary/simulation_summary.md`
  - `results/summary/causal_chain_analysis.md`
  - `results/summary/tail_latency_root_cause.md`
  - `results/summary/thermal_impact_analysis.md`
  - Training design doc: `docs/report/training_design.md`
