#!/usr/bin/env bash
set -euo pipefail

python3 sim/afo_simulator.py --num-tokens 4 --out results/sim/afo_ci_smoke.csv
python3 runtime/afo_runtime.py >/dev/null
python3 experiments/scripts/run_sweeps.py >/dev/null
python3 experiments/scripts/plot_results.py >/dev/null
python3 experiments/scripts/gen_baselines.py >/dev/null
python3 experiments/scripts/make_summary.py >/dev/null

echo "A.F.O smoke checks passed"
