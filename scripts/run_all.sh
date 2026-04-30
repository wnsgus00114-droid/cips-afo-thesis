#!/usr/bin/env bash
set -euo pipefail

python3 experiments/scripts/run_sweeps.py
python3 experiments/scripts/plot_results.py

echo "A.F.O experiment pipeline completed."
