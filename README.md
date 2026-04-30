# A.F.O (All For One)

Mechanism-driven 3D AI architecture study for long-context LLM inference under finite bridge bandwidth.

## One-Line Contribution
Prior works optimize components; **A.F.O enforces cross-tier execution contracts that make overlap deterministic under bandwidth constraints**.

## Positioning
This repository is an **architecture-feasibility study**.
- Not silicon-ready
- Not production-grade serving stack
- Policy-level validation through cycle-inspired simulation + stress sweeps

## Physical Contract (Fixed)
- Top / Layer1: compute die
- Bottom / Layer2: memory tier
  - inner rectangular HBM ring around compute footprint
  - outer rectangular HBF ring around HBM ring
- Interconnect: silicon-bridge-like finite-bandwidth fabric

## Reviewer Quick Start
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
python3 experiments/scripts/sanity_validate.py
python3 experiments/scripts/analyze_results.py
python3 experiments/scripts/make_summary.py
```

### 3) Reproduce Training-Policy Experiments
```bash
python3 experiments/scripts/run_training_experiments.py --config experiments/configs/training_base.json --num-steps 120 --seeds 11,23,37
python3 experiments/scripts/plot_training_results.py
```

### 4) Reproduce RTL Contract TB (Verilator)
```bash
make -C rtl contract_tb
```

## Key Inference Results (Current Run)
- AFO baseline: `12.74 tok/s`, `p99=80.004 ms`
- HBM-only baseline: `12.30 tok/s`, `p99=82.918 ms`
- Worst stress tail: `worst_case_tail p99=804.009 ms`
- Worst stress bridge contention: `133816.345 ms`
- Simulator sanity: `7 PASS / 0 FAIL`

## RTL Contract Validation (Current Run)
- Lint warning: `0`
- Assertion TB: `PASS`
- Saturation proxy queue peak: `12`
- Saturation proxy drain cycles: `13`

Primary artifacts:
- [baseline_comparison.md](results/tables/baseline_comparison.md)
- [baseline_fairness.md](results/tables/baseline_fairness.md)
- [simulator_sanity_checks.md](results/tables/simulator_sanity_checks.md)
- [simulation_summary.md](results/summary/simulation_summary.md)
- [causal_chain_analysis.md](results/summary/causal_chain_analysis.md)
- [tail_latency_root_cause.md](results/summary/tail_latency_root_cause.md)
- [thermal_impact_analysis.md](results/summary/thermal_impact_analysis.md)
- [rtl_contract_tb_summary.md](results/rtl/rtl_contract_tb_summary.md)
- [rtl_contract_validation.md](docs/report/rtl_contract_validation.md)

## Why A.F.O Wins (Causal Chain)
- KV reuse up -> batch_gain up -> shared-path GEMM efficiency up
- Prefetch accuracy up -> overlap efficiency up -> p99 latency down
- HBF tier separation + staging -> bridge contention migration down

Evidence files:
- [key_sensitivity_panels.md](results/tables/key_sensitivity_panels.md)
- [bridge_bw_gbs_tail_p99.svg](results/plots/bridge_bw_gbs_tail_p99.svg)
- [prefetch_accuracy_overlap_eff.svg](results/plots/prefetch_accuracy_overlap_eff.svg)
- [shared_kv_ratio_throughput.svg](results/plots/shared_kv_ratio_throughput.svg)

## Baseline Fairness Policy
All baselines use identical:
- workload: batch/context/chunk size
- capacity: HBM/HBF/SRAM
- bandwidth and latency: HBM BW, HBF BW, bridge BW, HBF latency

Only mechanism knobs vary:
- shared KV ratio
- HBF weight fraction
- prefetch accuracy
- routing diversity
- LHB and prefetch depth
- matrix efficiency

See [baseline_fairness.md](results/tables/baseline_fairness.md) for full disclosure.

## Repository Map
- Architecture docs: `docs/architecture/`, `docs/implementation/`
- Report docs: `docs/report/`
- Reviewer closure matrix: [reviewer_feedback_closure.md](docs/report/reviewer_feedback_closure.md)
- Simulator: `sim/afo_simulator.py`, `sim/afo_training_simulator.py`
- Runtime mock: `runtime/afo_runtime.py`, `runtime/afo_training_runtime.py`
- Experiments: `experiments/scripts/`
- Results: `results/`
- Thesis package: [thesis/README.md](thesis/README.md)

## 3D Visualization
- Python render: `3d/python/chip_3d_plot.py`, `3d/python/chip_3d_svg.py`
- Three.js viewer: [3d/threejs/index.html](3d/threejs/index.html)

## Reproducibility Notes
- Baselines labeled `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are synthetic policy-level approximations.
- They are included for directional comparison under the same simulator constraints.
- For hardware publication claims, additional RTL/FPGA/silicon measurements are still required.

## License
Research prototype repository for architecture exploration and reviewer evaluation.
