# A.F.O (All For One)

Mechanism-driven 3D AI architecture study for LLM serving/training policy validation.

## One-Line Thesis
A.F.O enforces **tier-locality** and **descriptor-coupled overlap** so long-context LLM workloads remain stable under **finite bridge bandwidth** and **HBM/HBF latency asymmetry**.

## What Is New (Not Just a Combination)
- Enforced physical topology: **Top Layer (L1) = Compute**, **Bottom Layer (L2) = Memory Rings**
  - L2 inner ring: HBM rectangular continuous ring
  - L2 outer ring: HBF rectangular continuous ring
- Enforced memory semantics:
  - HBM: mutable runtime-hot state (runtime KV, activations, metadata)
  - HBF: high-capacity read-mostly state (weights, shared KV catalog, cold chunks)
- Enforced execution contract:
  - route-aware shared/unique KV split
  - layer-overlapped prefetch
  - SRAM A/B swap + LHB replay
- Stress-validated methodology:
  - tail latency / bottleneck migration / thermal coupling / process jitter

## Reviewer Quick Start (README-Only Review)
### 1) Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Reproduce Inference Experiments
```bash
python3 experiments/scripts/run_sweeps.py --config experiments/configs/base.json --num-tokens 256 --seeds 11,23,37
python3 experiments/scripts/gen_baselines.py
python3 experiments/scripts/plot_results.py
python3 experiments/scripts/make_summary.py
```

### 3) Reproduce Training-Policy Experiments
```bash
python3 experiments/scripts/run_training_experiments.py --config experiments/configs/training_base.json --num-steps 120 --seeds 11,23,37
python3 experiments/scripts/plot_training_results.py
```

## Key Results Snapshot
### Inference (Synthetic, Cycle-Inspired)
- Best baseline throughput: **AFO_full = 14.68 tok/s**
- Best baseline p99 latency: **69.235 ms**
- Worst stress tail: **worst_case_tail p99 = 804.009 ms**

Sources:
- `results/tables/baseline_comparison.md`
- `results/summary/simulation_summary.md`
- `results/sim/stress_scenarios.csv`

### Training Policy Extension (System SW)
- Best stability scenario: **lora_nominal stability = 66.78**
- Worst tail scenario: **lora_worst_tail p99 = 8,754,839.06 ms**
- OOM behavior explicitly tracked (`oom_hbm`, `oom_hbf`)

Sources:
- `results/training_tables/training_scenario_summary.md`
- `results/training_summary/training_summary.md`

## Evidence Artifacts (Direct Review Targets)
### Architecture and Design Docs
- `docs/architecture/afo_system_overview.md`
- `docs/implementation/afo_implementation_plan.md`
- `docs/implementation/memory_map.md`
- `docs/implementation/dataflow.md`
- `docs/implementation/runtime_software_design.md`

### Research/Validation Docs
- `docs/report/experimental_design.md`
- `docs/report/power_performance_model.md`
- `docs/report/training_design.md`
- `docs/report/reference_alignment.md`

### Core Code
- Inference simulator: `sim/afo_simulator.py`
- Training simulator: `sim/afo_training_simulator.py`
- Inference runtime mock: `runtime/afo_runtime.py`
- Training runtime mock: `runtime/afo_training_runtime.py`
- Inference experiment scripts: `experiments/scripts/run_sweeps.py`, `gen_baselines.py`, `plot_results.py`, `make_summary.py`
- Training experiment scripts: `experiments/scripts/run_training_experiments.py`, `plot_training_results.py`

### Result Tables/Plots
- Inference CSV/plots: `results/sim/`, `results/plots/`, `results/tables/`, `results/summary/`
- Training CSV/plots: `results/training/`, `results/training_plots/`, `results/training_tables/`, `results/training_summary/`

## 3D Visualization
- Python render: `3d/python/chip_3d_plot.py`, `3d/python/chip_3d_svg.py`
- Three.js interactive: `3d/threejs/index.html`, `3d/threejs/main.js`
- Visualization pipeline doc: `docs/visualization/visualization_pipeline.md`

## Paper Package (Local-Only)
- `result_paper/` is intentionally ignored from Git tracking.
- Thesis Word build script exists locally at `result_paper/scripts/build_word_paper.py`.

## Reproducibility Notes
- This repository is positioned as an **architecture-feasibility study**.
- Results are from **cycle-inspired synthetic simulation**, not taped-out silicon.
- Baselines labeled `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines.

## Repository Structure
See `docs/repository_structure.md`.

## License
Research prototype repository for architecture exploration and reviewer evaluation.
