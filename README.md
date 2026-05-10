# A.F.O (All For One)

Bridge-Sensitive Hierarchical Memory Staging for Bandwidth-Constrained LLM Inference

- Author: JunHyeon Beak
- Contact: wnsgus00114@gmail.com

---

## 1. Project Goal

This repository studies **where LLM inference bottlenecks actually come from** and how they move across memory paths under stress.

Core message:

- A.F.O is **not** positioned as a universal peak-throughput winner.
- A.F.O is a **bridge-sensitive hierarchical staging + bottleneck attribution/control framework**.
- "Bridge bottleneck" in this repo means an **internal package-path bottleneck inside the modeled A.F.O architecture envelope**.

---

## 2. Repository Policy (Important)

The following folders are local writing/template workspaces and are excluded from remote uploads:

- `paper22/`
- `paper!!!!!!/`
- `elsarticle/`

---

## 3. Experiment Tracks

| Track | Purpose | Main Outputs |
|---|---|---|
| Synthetic 3-axis | Fast sensitivity scan | `results/tables/sweep_summary.md` |
| Full gem5 3-axis | Single-device baseline/sweep/tech comparison | `results/gem5_eval_3axis/tables/jsa_paper_summary.md` |
| Datacenter scale-out | Model-derived cluster projection | `results/gem5_eval_datacenter_full/tables/datacenter_summary.md` |
| Profile-guided replay | Serving-profile-log-derived replay validation | `results/paper_tables/profile_replay_summary.md` |
| Distribution-matched synthetic | ShareGPT/vLLM-style length distribution mapping | `results/distribution_matched_large/distribution_matched_summary.md` |
| Stress validation | Tail amplification and attribution movement | `results/paper_tables/stress_validation_summary.md` |
| RTL-to-physical feasibility | Timing/signoff-readiness evidence tracking | `reports/final_feasibility_report.md` |

---

## 4. Code Layout

- `sim/`: A.F.O cycle-inspired simulator core
- `runtime/`: runtime policy logic
- `experiments/`: experiment entrypoints/configs
- `experiments/scripts/`: analysis/summary/plot generation scripts
- `rtl/`: contract-control RTL and implementation helper scripts
- `tools/`: timing parser, Fmax sweep, readiness/checklist generators
- `results/`: experiment outputs (csv/json/md/figures)
- `reports/`: feasibility/signoff-oriented summaries

Key scripts:

- `experiments/run_all.py`
- `experiments/run_all_gem5.py`
- `experiments/run_all_gem5_datacenter.py`
- `experiments/run_profile_trace_replay.py`
- `experiments/scripts/run_distribution_matched_synthetic.py`
- `experiments/scripts/summarize_profile_replay_results.py`
- `experiments/scripts/plot_profile_replay_validation.py`
- `scripts/run_full_analysis.sh`

---

## 5. How We Run Experiments

### 5.1 Synthetic 3-axis

```bash
python3 experiments/run_all.py \
  --config experiments/configs/base.json \
  --seeds 5 \
  --out-root results/eval_3axis
```

### 5.2 Full gem5 3-axis

```bash
python3 experiments/run_all_gem5.py \
  --gem5-bin third_party/gem5/build/ARM/gem5.opt \
  --out-root results/gem5_eval_3axis \
  --only-axis all
```

### 5.3 Datacenter model-derived projection

```bash
python3 experiments/run_all_gem5_datacenter.py \
  --gem5-bin third_party/gem5/build/ARM/gem5.opt \
  --dc-config experiments/configs/datacenter_eval.json \
  --out-root results/gem5_eval_datacenter_full
```

### 5.4 Profile-guided replay

```bash
python3 experiments/run_profile_trace_replay.py \
  --profile-input <profile.jsonl> \
  --out-root results/gem5_eval_profile_replay_small_sweep_tight_v2 \
  --time-scale 0.02 \
  --only-axis all
```

Post-processing:

```bash
python3 experiments/scripts/summarize_profile_replay_results.py \
  --results-root results \
  --out-dir results/paper_tables

python3 experiments/scripts/plot_profile_replay_validation.py \
  --results-root results \
  --out-dir results/figures
```

### 5.5 Distribution-matched synthetic (ShareGPT/vLLM-style)

```bash
python3 experiments/scripts/run_distribution_matched_synthetic.py \
  --profiles-config experiments/configs/distribution_matched_profiles.json \
  --requests-per-profile 240 \
  --window-size 24 \
  --seed 2026 \
  --out-dir results/distribution_matched_large
```

### 5.6 Stress validation

- Axes: burst intensity, tenant count, shared-prefix ratio, prefetch accuracy, SRAM capacity, HBF latency, bridge-congestion stress
- Outputs:
  - `results/paper_tables/stress_validation_summary.md`
  - `results/paper_tables/stress_hbm_delta.csv`

### 5.7 RTL-to-physical feasibility track

```bash
source ./scripts/setup_eda_env.sh
./scripts/run_full_analysis.sh
```

---

## 6. Key Results Snapshot

### 6.1 gem5 single-device baseline

- A.F.O: `1811.31 tok/s`
- HBM-only: `1756.96 tok/s`
- Throughput delta: `+3.09%`
- p99 modeled memory-path service latency: near-equal (`0.01112 ms` vs `0.01111 ms`)

### 6.2 Fairness-locked synthetic baseline

- A.F.O: `534.60 tok/s`, `p99 245.280 ms`
- HBM baseline: `497.53 tok/s`, `p99 267.473 ms`
- Delta: `+7.45% tok/s`, `-8.30% p99`

### 6.3 Distribution-matched synthetic (new)

Source table:

- `results/distribution_matched_large/distribution_matched_summary.md`

Observed weighted aggregates:

- ShareGPT/vLLM-style profile:
  - A.F.O `532.29 tok/s`, p99 `249.524863 ms`
  - HBM-only `497.31 tok/s`, p99 `268.830467 ms`
  - Delta: `+7.03% tok/s`, `-7.18% p99`
- DistServe-style profile:
  - A.F.O `529.50 tok/s`, p99 `251.061060 ms`
  - HBM-only `493.83 tok/s`, p99 `271.640952 ms`
  - Delta: `+7.22% tok/s`, `-7.58% p99`

Interpretation:

- Even after mapping paper-anchored request-length/arrival distributions, the main direction remains consistent.
- This remains **distribution-matched synthetic validation**, not end-to-end production serving benchmarking.

### 6.4 Feasibility status snapshot

- 1.0 ns (1 GHz) MCMM proxy closure: `NOT_CLOSED`
- First passing relaxed point in sweep: `4.0 ns (~250 MHz)`
- Scope: timing-aware feasibility evidence, not silicon-proven closure

---

## 7. High-Value Output Files

- `results/gem5_eval_3axis/tables/jsa_paper_summary.md`
- `results/tables/baseline_comparison.md`
- `results/paper_tables/profile_replay_summary.md`
- `results/distribution_matched_large/distribution_matched_summary.md`
- `results/paper_tables/stress_validation_summary.md`
- `reports/timing_summary.md`
- `reports/signoff_checklist.md`
- `reports/final_feasibility_report.md`

---

## 8. Dependencies

- Python 3.10+
- gem5 (`third_party/gem5/build/ARM/gem5.opt`)
- OpenROAD / OpenSTA / Yosys (feasibility track)
- Magic / Netgen (DRC/LVS proxy flow)
- matplotlib (plot scripts)

Example:

```bash
python3 -m pip install matplotlib
```

---

## 9. Claim Boundary (Reviewer-safe)

Use:

- timing-aware feasibility study
- bridge/inter-tier bottleneck attribution/control evidence
- model-derived scale-out sensitivity
- profile-guided replay validation
- serving-profile-log-derived replay

Avoid:

- silicon-proven
- production-ready chip
- end-to-end production serving validation
- universal superiority

Notes:

- `p50/p95/p99` values here are modeled memory-path service metrics in this methodology.
- Datacenter results are model-derived projections, not distributed runtime benchmark measurements.

