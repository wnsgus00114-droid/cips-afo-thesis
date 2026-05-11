#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GEM5_BIN="${GEM5_BIN:-$ROOT_DIR/third_party/gem5/build/ARM/gem5.opt}"
PROFILE="${PROFILE:-quick}"   # quick | full
RESULTS_PREFIX="${RESULTS_PREFIX:-results}"

usage() {
  cat <<'EOF'
Run reviewer-oriented reproducibility bundle.

Usage:
  scripts/run_reviewer_bundle.sh [--profile quick|full] [--gem5-bin PATH] [--results-prefix DIR]

Examples:
  ./scripts/run_reviewer_bundle.sh
  ./scripts/run_reviewer_bundle.sh --profile full
  GEM5_BIN=/path/to/gem5.opt ./scripts/run_reviewer_bundle.sh --profile full

Profiles:
  quick:
    - 1-minute smoke replay
    - baseline-only gem5 comparison (AFO vs HBM GPU-class server baseline)
    - replay table/figure summary
  full:
    - full 3-axis gem5 run + bridge-wise comparisons
    - context hero sweep
    - profile-guided replay (baseline/sweep)
    - replay summarize/plot
    - distribution-matched validation
    - stress table/figure assets
    - datacenter model-derived scale-out
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"; shift 2;;
    --gem5-bin)
      GEM5_BIN="$2"; shift 2;;
    --results-prefix)
      RESULTS_PREFIX="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "[error] unknown arg: $1"
      usage
      exit 1;;
  esac
done

if [[ ! -x "$GEM5_BIN" ]]; then
  echo "[error] gem5 binary not found/executable: $GEM5_BIN"
  echo "Set --gem5-bin or GEM5_BIN and retry."
  exit 1
fi

echo "[info] root: $ROOT_DIR"
echo "[info] gem5: $GEM5_BIN"
echo "[info] profile: $PROFILE"
echo "[info] results-prefix: $RESULTS_PREFIX"

run_smoke() {
  echo "[step] smoke replay"
  GEM5_BIN="$GEM5_BIN" OUT_ROOT="$ROOT_DIR/$RESULTS_PREFIX/gem5_eval_profile_replay_smoke_artifact" \
    "$ROOT_DIR/scripts/run_artifact_smoke.sh"
}

run_quick() {
  run_smoke

  echo "[step] gem5 baseline-only (AFO vs HBM GPU-class server baseline)"
  python3 experiments/run_all_gem5.py \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --only-axis baseline \
    --out-root "$RESULTS_PREFIX/gem5_eval_3axis_afo_vs_hbm_server_quick"

  echo "[step] replay summarize + plot"
  python3 experiments/scripts/summarize_profile_replay_results.py \
    --results-root "$RESULTS_PREFIX" \
    --out-dir "$RESULTS_PREFIX/paper_tables"

  python3 experiments/scripts/plot_profile_replay_validation.py \
    --results-root "$RESULTS_PREFIX" \
    --out-dir "$RESULTS_PREFIX/figures"
}

run_full() {
  run_smoke

  echo "[step] gem5 3-axis (all)"
  python3 experiments/run_all_gem5.py \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --only-axis all \
    --out-root "$RESULTS_PREFIX/gem5_eval_3axis_afo_vs_hbm_server"

  echo "[step] gem5 3-axis bridge-wise baseline-vs-baseline"
  python3 experiments/run_all_gem5.py \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --compare-baselines-on-sweeps \
    --only-axis all \
    --out-root "$RESULTS_PREFIX/gem5_eval_3axis_afo_vs_hbm_server_bridgewise"

  echo "[step] context hero (with technology profiles)"
  python3 experiments/run_context_hero_gem5.py \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --include-tech-profiles \
    --out-root "$RESULTS_PREFIX/gem5_eval_context_hero_afo_vs_hbm_server_bridgewise"

  echo "[step] profile-guided replay (all axes)"
  python3 experiments/run_profile_trace_replay.py \
    --profile-input experiments/fixtures/profile_smoke_events.jsonl \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --only-axis all \
    --out-root "$RESULTS_PREFIX/gem5_eval_profile_replay_small"

  echo "[step] profile-guided replay (high-load/time-compressed sweep)"
  python3 experiments/run_profile_trace_replay.py \
    --profile-input experiments/fixtures/profile_smoke_events.jsonl \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --only-axis sweep \
    --time-scale 0.02 \
    --out-root "$RESULTS_PREFIX/gem5_eval_profile_replay_small_sweep_tight_v2"

  echo "[step] replay summarize + plot"
  python3 experiments/scripts/summarize_profile_replay_results.py \
    --results-root "$RESULTS_PREFIX" \
    --out-dir "$RESULTS_PREFIX/paper_tables"

  python3 experiments/scripts/plot_profile_replay_validation.py \
    --results-root "$RESULTS_PREFIX" \
    --out-dir "$RESULTS_PREFIX/figures"

  echo "[step] distribution-matched synthetic validation"
  python3 experiments/scripts/run_distribution_matched_synthetic.py \
    --out-dir "$RESULTS_PREFIX/distribution_matched_large" \
    --baselines AFO_Proposed,HBM_GPU-class_Server_Baseline \
    --requests-per-profile 96 \
    --window-size 24 \
    --seed 2026

  echo "[step] stress-validation assets"
  python3 experiments/scripts/build_stress_validation_assets.py \
    --results-root "$RESULTS_PREFIX" \
    --table-out-dir "$RESULTS_PREFIX/paper_tables" \
    --figure-out "$RESULTS_PREFIX/figures/fig13_stress_validation_panels.png"

  echo "[step] datacenter model-derived scale-out"
  python3 experiments/run_all_gem5_datacenter.py \
    --gem5-bin "$GEM5_BIN" \
    --baseline-mode afo_hbm_server \
    --only-axis all \
    --out-root "$RESULTS_PREFIX/gem5_eval_datacenter_afo_vs_hbm_server"
}

case "$PROFILE" in
  quick) run_quick ;;
  full) run_full ;;
  *)
    echo "[error] PROFILE must be quick or full, got: $PROFILE"
    exit 1
    ;;
esac

echo "[done] reviewer bundle completed (profile=$PROFILE)"
