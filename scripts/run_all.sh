#!/usr/bin/env bash
set -euo pipefail

python3 experiments/scripts/run_sweeps.py --config experiments/configs/base.json --num-tokens 256 --seeds 11,23,37
python3 experiments/scripts/gen_baselines.py
python3 experiments/scripts/plot_results.py
python3 experiments/scripts/sanity_validate.py
python3 experiments/scripts/analyze_results.py
python3 experiments/scripts/make_summary.py

echo "A.F.O full experiment pipeline completed."
