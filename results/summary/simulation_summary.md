# A.F.O Simulation Summary (Reviewer-Driven Update)

## 1. Physical Topology Constraint
- `Top (Layer1) = Compute Chiplet (3D hybrid bonding on central base-die zone)`
- `Bottom (Layer2) = Active Base Die (logic interposer with metadata/LHB/router fabric)`
- `Periphery` of Layer2 mounts `inner HBM ring + outer HBF ring` via 2.5D micro-bumps
- Data path is explicitly modeled as `ring ingress -> base-die lateral route -> central TSV neck -> SRAM staging`

## 2. Reliability Upgrade
- Multi-seed aggregated sweeps and baselines are used (`seed_count` embedded in CSV).
- Stress scenarios now include burst traffic, bridge saturation, and thermal-hot workload.
- Reproducibility parameters are exported to `results/tables/reproducibility_params.md`.
- Baseline fairness contract is explicit in `results/tables/baseline_fairness.md`.
- Simulator sanity checks: `PASS=9` / `FAIL=0` (`results/tables/simulator_sanity_checks.md`).

## 3. Baseline Coverage
- Best throughput baseline: `AFO_full` = `4.16` tokens/sec
- Lowest p99 baseline: `AFO_full` = `244.814` ms
- Highest p99 baseline: `Apple_like_UMA` = `257.329` ms
- Baseline set includes: `HBM_only_GPU`, `MoSKA_only`, `H3_only`, `Apple_like_UMA`, `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like`.

## 4. Tail Latency / Worst-Case
- Worst stress p99: `worst_case_tail` -> `1579.098` ms
- Worst stress bridge contention: `worst_case_tail` -> `133816.345` ms
- Worst stress thermal peak: `peak_traffic` -> `125.00` C

## 5. Why Bottleneck Changes
- `bottleneck_hbm_pct`, `bottleneck_hbf_pct`, `bottleneck_bridge_pct`, `bottleneck_tsv_pct` are exported per point.
- Review interpretation should track whether gain came from: `HBF miss penalty↓`, `bridge contention↓`, `TSV contention↓`, or `SRAM hit / overlap↑`.
- Causal chain report: `results/summary/causal_chain_analysis.md`.

## 6. Model vs Experiment Link
- Each point reports `model_predicted_token_ms`, `model_measured_token_ms`, `model_error_pct`.
- This directly connects analytical equations to observed simulation outputs.

## 7. Shared-KV Reuse / Prefetch Evidence
- Exported metrics: `shared_kv_reuse_ratio`, `batch_gain`, `prefetch_coverage_ratio`, `overlap_efficiency`, `lhb_hit_ratio`.
- These metrics quantify whether MoSKA reuse and layer-overlap actually materialize.
- Dedicated sensitivity panel table: `results/tables/key_sensitivity_panels.md`.

## 8. Key Sweep Highlights
- `base_die_xbar_bw_gbs` best throughput: `6800.0` -> `4.25` tokens/sec; worst p99: `4200.0` -> `279.961` ms
- `batch_size` best throughput: `16` -> `8.07` tokens/sec; worst p99: `256` -> `255.475` ms
- `bridge_bw_gbs` best throughput: `6400.0` -> `4.47` tokens/sec; worst p99: `3200.0` -> `288.777` ms
- `context_len` best throughput: `1024` -> `4.13` tokens/sec; worst p99: `16384` -> `253.464` ms
- `hbf_latency_us` best throughput: `4.0` -> `4.11` tokens/sec; worst p99: `12.0` -> `248.404` ms
- `kv_chunk_size_kb` best throughput: `64` -> `4.16` tokens/sec; worst p99: `512` -> `267.989` ms
- `multi_tenant_users` best throughput: `32` -> `4.93` tokens/sec; worst p99: `384` -> `666.322` ms
- `num_experts` best throughput: `16` -> `4.11` tokens/sec; worst p99: `128` -> `248.391` ms
- `prefetch_accuracy` best throughput: `0.95` -> `4.15` tokens/sec; worst p99: `0.6` -> `263.534` ms
- `shared_kv_ratio` best throughput: `0.85` -> `4.11` tokens/sec; worst p99: `0.3` -> `248.589` ms
- `sram_capacity_mb` best throughput: `1024.0` -> `4.19` tokens/sec; worst p99: `256.0` -> `263.952` ms
- `traffic_burst_factor` best throughput: `1.0` -> `4.11` tokens/sec; worst p99: `3.0` -> `301.631` ms
- `tsv_uplink_bw_gbs` best throughput: `5800.0` -> `4.45` tokens/sec; worst p99: `2800.0` -> `308.378` ms

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