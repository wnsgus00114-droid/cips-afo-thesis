# A.F.O Training Mechanism and Experiment Plan

## 1. Why Training Path is Different from Inference
A.F.O inference path is dominated by read-heavy KV and weight streaming. Training adds:
- activation storage/recompute
- gradient accumulation and optimizer state traffic
- stronger thermal coupling due to sustained compute duty cycle

Therefore, training optimization target is not only throughput but also stability (`tail`, `thermal throttle`, `convergence proxy`).

## 2. Training Modes Implemented
1. `full_finetune`
- all model parameters trainable
- optimizer states large, mostly HBF-resident
- aggressive checkpoint/offload required for long context

2. `lora_sft`
- base model frozen (HBF RO)
- small trainable adapter fraction in HBM
- higher token throughput and lower optimizer bandwidth pressure

## 3. Core Mechanisms
1. Activation checkpointing
- control: `activation_checkpoint_ratio`
- effect: memory footprint down, recompute ops up

2. Activation offload to HBF
- control: `activation_offload_ratio`
- effect: HBM pressure down, HBF/bridge traffic up

3. Layer-window prefetch
- controls: `prefetch_accuracy`, `weight_prefetch_depth`, `lhb_enable`
- effect: exposed memory wait and tail reduction

4. Expert/routing balance control
- controls: `top_k`, `num_experts`, `expert_capacity_factor`, `route_diversity`
- effect: imbalance down -> training stability up

5. Adaptive policy loop
- telemetry inputs: `step_p99_ms`, `sram_pressure`, `predicted_stall_ratio`
- policy outputs: adjust checkpoint/offload/prefetch depth

## 4. Simulator Outputs (Training)
Main outputs:
- throughput: `tokens_per_sec_train`
- step latency: `step_time_ms`, `step_p99_ms`, `step_max_ms`
- tail metric: `tail_ratio_p99_p50`
- memory/cross-tier: `hbm_util`, `hbf_util`, `bridge_util`, `sram_hit_ratio`
- quality proxies: `train_stability_score`, `convergence_proxy`, `expert_balance_score`
- thermal: `thermal_peak_c`, `thermal_throttle_ratio`

## 5. Experiments Added
Sweeps:
- `sequence_len`, `micro_batch_size`, `grad_accum_steps`
- `activation_checkpoint_ratio`, `activation_offload_ratio`
- `prefetch_accuracy`, `sram_capacity_mb`, `hbf_latency_us`, `bridge_bw_gbs`, `traffic_burst_factor`

Scenarios:
- `full_ft_nominal`
- `full_ft_longctx`
- `full_ft_thermal_hot`
- `lora_nominal`
- `lora_throughput`
- `lora_worst_tail`

## 6. Artifact Paths
- training simulator: `sim/afo_training_simulator.py`
- training sweeps runner: `experiments/scripts/run_training_experiments.py`
- training plots/tables: `experiments/scripts/plot_training_results.py`
- results:
  - `results/training/*.csv`
  - `results/training_plots/*.svg`
  - `results/training_tables/*.md`
  - `results/training_summary/training_summary.md`
