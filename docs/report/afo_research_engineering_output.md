# A.F.O End-to-End Research + Engineering Output

## 1. 3D Visualization Pipeline
- Chip-level 3D (Top compute / Bottom memory-ring tier):
  - compute die + inner HBM rectangular ring + outer HBF rectangular ring + silicon bridge lanes
- System-level 3D:
  - package + board + cooling + IO interconnect
- Implementations:
  - Python/Matplotlib: `3d/python/chip_3d_plot.py`
  - Three.js interactive: `3d/threejs/index.html`, `3d/threejs/main.js`
  - Blender scene script: `3d/blender/build_scene.py`
- Artifacts:
  - static SVG/PNG under `results/visualization/`
  - browser-interactive viewer via Three.js

## 2. Experiment Framework (Updated)
- Sweep driver (multi-seed, raw+agg): `experiments/scripts/run_sweeps.py`
- Baseline generator (expanded set): `experiments/scripts/gen_baselines.py`
- Plot generator (tail/bridge/thermal aware): `experiments/scripts/plot_results.py`
- Summary builder: `experiments/scripts/make_summary.py`
- Training sweeps: `experiments/scripts/run_training_experiments.py`
- Training plots/tables: `experiments/scripts/plot_training_results.py`

### Covered metrics
- Throughput, mean latency, p90/p99/p999/max tail latency
- Bridge/HBM/HBF utilization and contention time
- SRAM hit, overlap efficiency, LHB hit, HBF miss penalty
- Shared-KV reuse ratio and batch gain
- Thermal peak/avg/throttle ratio, throughput per watt
- Analytical prediction vs measured latency error

### Covered scenarios
- Parameter sweeps: batch/context/experts/chunk/prefetch/shared ratio/SRAM size/HBF latency/multi-tenant/burst/bridge BW
- Stress scenarios: nominal, peak_traffic, bridge_saturation, thermal_hot, worst_case_tail
- Training scenarios: full_ft_nominal, full_ft_longctx, full_ft_thermal_hot, lora_nominal, lora_throughput, lora_worst_tail

## 3. Reproducibility and Results
- Full parameter snapshot: `results/sim/parameter_snapshot.json`
- Reproducibility table: `results/tables/reproducibility_params.md`
- Sweep CSV (aggregated): `results/sim/sweep_*.csv`
- Sweep CSV (raw seeds): `results/sim/sweep_*_raw.csv`
- Stress CSV: `results/sim/stress_scenarios.csv`
- Baseline table: `results/tables/baseline_comparison.md`
- Sweep table: `results/tables/sweep_summary.md`
- Plot catalog: `results/tables/plot_index.md`
- Executive summary: `results/summary/simulation_summary.md`
- Training summary: `results/training_summary/training_summary.md`

## 4. Paper and Word Output
- Research draft markdown: `paper/afo_paper_draft.md`
- Archive-style Word manuscript (local-only):
  - `result_paper/docs/AFO_Archive_Thesis_JunHyeonBeak_v4_ring_topology.docx`

## 5. Current Limitation Statement
- `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines in this stage.
- Hardware-in-the-loop and silicon-measured thermal transients are future work items.
