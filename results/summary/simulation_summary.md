# A.F.O Simulation Summary (Reviewer-Driven Update)

## 1. Physical Topology Constraint
- `Top (Layer1) = Compute Chipset`
- `Bottom (Layer2) = Memory Ring Tier (inner HBM ring + outer HBF ring)`
- Silicon bridge links memory ring tier to compute-side SRAM staging windows

## 2. Reliability Upgrade
- Multi-seed aggregated sweeps and baselines are used (`seed_count` embedded in CSV).
- Stress scenarios now include burst traffic, bridge saturation, and thermal-hot workload.
- Reproducibility parameters are exported to `results/tables/reproducibility_params.md`.
- Baseline fairness contract is explicit in `results/tables/baseline_fairness.md`.
- Simulator sanity checks: `PASS=7` / `FAIL=0` (`results/tables/simulator_sanity_checks.md`).

## 3. Baseline Coverage
- Best throughput baseline: `AFO_full` = `12.74` tokens/sec
- Lowest p99 baseline: `AFO_full` = `80.004` ms
- Highest p99 baseline: `Apple_like_UMA` = `85.277` ms
- Baseline set includes: `HBM_only_GPU`, `MoSKA_only`, `H3_only`, `Apple_like_UMA`, `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like`.

## 4. Tail Latency / Worst-Case
- Worst stress p99: `worst_case_tail` -> `804.009` ms
- Worst stress bridge contention: `worst_case_tail` -> `133816.345` ms
- Worst stress thermal peak: `peak_traffic` -> `125.00` C

## 5. Why Bottleneck Changes
- `bottleneck_hbm_pct`, `bottleneck_hbf_pct`, `bottleneck_bridge_pct` are now exported per point.
- Review interpretation should track whether gain came from: `HBF miss penalty↓`, `bridge contention↓`, or `SRAM hit / overlap↑`.
- Causal chain report: `results/summary/causal_chain_analysis.md`.

## 6. Model vs Experiment Link
- Each point reports `model_predicted_token_ms`, `model_measured_token_ms`, `model_error_pct`.
- This directly connects analytical equations to observed simulation outputs.

## 7. Shared-KV Reuse / Prefetch Evidence
- Exported metrics: `shared_kv_reuse_ratio`, `batch_gain`, `prefetch_coverage_ratio`, `overlap_efficiency`, `lhb_hit_ratio`.
- These metrics quantify whether MoSKA reuse and layer-overlap actually materialize.
- Dedicated sensitivity panel table: `results/tables/key_sensitivity_panels.md`.

## 8. Key Sweep Highlights
- `batch_size` best throughput: `16` -> `24.62` tokens/sec; worst p99: `256` -> `83.723` ms
- `bridge_bw_gbs` best throughput: `6400.0` -> `15.30` tokens/sec; worst p99: `3200.0` -> `121.793` ms
- `context_len` best throughput: `1024` -> `12.59` tokens/sec; worst p99: `16384` -> `83.066` ms
- `hbf_latency_us` best throughput: `4.0` -> `12.53` tokens/sec; worst p99: `12.0` -> `81.424` ms
- `kv_chunk_size_kb` best throughput: `64` -> `12.69` tokens/sec; worst p99: `512` -> `87.811` ms
- `multi_tenant_users` best throughput: `32` -> `14.99` tokens/sec; worst p99: `384` -> `239.295` ms
- `num_experts` best throughput: `16` -> `12.52` tokens/sec; worst p99: `128` -> `81.410` ms
- `prefetch_accuracy` best throughput: `0.95` -> `12.68` tokens/sec; worst p99: `0.6` -> `87.381` ms
- `shared_kv_ratio` best throughput: `0.85` -> `12.53` tokens/sec; worst p99: `0.3` -> `81.471` ms
- `sram_capacity_mb` best throughput: `1024.0` -> `12.78` tokens/sec; worst p99: `256.0` -> `86.483` ms
- `traffic_burst_factor` best throughput: `1.0` -> `12.52` tokens/sec; worst p99: `3.0` -> `107.699` ms

## 9. Artifacts
- Sweep CSV (agg/raw): `results/sim/sweep_*.csv`, `results/sim/sweep_*_raw.csv`
- Stress scenarios: `results/sim/stress_scenarios.csv`
- Baselines: `results/tables/baseline_comparison.csv`
- Baseline fairness: `results/tables/baseline_fairness.md`
- Simulator sanity checks: `results/tables/simulator_sanity_checks.md`
- Sweep tables: `results/tables/sweep_summary.md`
- Plot index: `results/tables/plot_index.md`
- Parameter disclosure: `results/tables/reproducibility_params.md`
- Causal/tail/thermal analyses: `results/summary/causal_chain_analysis.md`, `results/summary/tail_latency_root_cause.md`, `results/summary/thermal_impact_analysis.md`