# A.F.O Artifact (Anonymous Review Ready)

Bridge-Sensitive Hierarchical Memory Staging for Bandwidth-Constrained LLM Inference

---

## 1) Anonymity Policy (Critical)

This repository is prepared for **double-blind artifact evaluation**.

- Do **not** expose personal identity in artifact links, release notes, or README text.
- Publish through:
  - `https://anonymous.4open.science/`, or
  - a neutral artifact account/org.
- Keep local manuscript folders out of public artifact pushes:
  - `paper22/`
  - `paper!!!!!!/`
  - `paper!@!/`
  - `elsarticle/`

---

## 2) What This Artifact Shows

This artifact is designed to evaluate **bridge-sensitive bottleneck attribution/control** in hierarchical LLM memory paths.

Main comparison target:
- `AFO_Proposed`
- `HBM_GPU-class_Server_Baseline` (host + system memory + host-device path + GPU-local HBM class-level baseline)

The goal is **not** to claim universal peak throughput.  
The goal is to show how bottlenecks migrate across bridge/inter-tier/queue/fabric paths and how A.F.O control hooks respond.

---

## 3) Environment

Required:
- Python 3.10+
- gem5 binary: `third_party/gem5/build/ARM/gem5.opt`
- Python packages: `matplotlib`, `protobuf`

Optional (feasibility track):
- OpenROAD / OpenSTA / Yosys
- Magic / Netgen

Install Python deps:

```bash
python3 -m pip install --user --break-system-packages matplotlib protobuf
```

---

## 4) 1-Minute Smoke Test

```bash
./scripts/run_artifact_smoke.sh
```

This runs:
- profile JSONL -> tiered CSV trace
- CSV -> gem5 proto traces
- gem5 replay baseline
- replay summary generation

Expected outputs:
- `results/gem5_eval_profile_replay_smoke_artifact/eval/raw/baseline_comparison.csv`
- `results/paper_tables/profile_replay_summary.md`

One-command reviewer bundle (recommended):

```bash
# quick: smoke + baseline + replay summary/plots
./scripts/run_reviewer_bundle.sh --profile quick

# full: all major tracks in this README
./scripts/run_reviewer_bundle.sh --profile full
```

---

## 5) Core Repro Commands (Reviewer-Facing)

Set gem5 binary once:

```bash
export GEM5_BIN="$(pwd)/third_party/gem5/build/ARM/gem5.opt"
```

### A. gem5 3-axis main run (A.F.O vs HBM GPU-class server baseline)

```bash
python3 experiments/run_all_gem5.py \
  --gem5-bin "$GEM5_BIN" \
  --baseline-mode afo_hbm_server \
  --only-axis all \
  --out-root results/gem5_eval_3axis_afo_vs_hbm_server
```

Outputs:
- `results/gem5_eval_3axis_afo_vs_hbm_server/raw/baseline_comparison.csv`
- `results/gem5_eval_3axis_afo_vs_hbm_server/raw/sweep_bridge_bw_gbs.csv`
- `results/gem5_eval_3axis_afo_vs_hbm_server/raw/sweep_tsv_uplink_bw_gbs.csv`
- `results/gem5_eval_3axis_afo_vs_hbm_server/raw/interconnect_tech_comparison.csv`
- `results/gem5_eval_3axis_afo_vs_hbm_server/tables/jsa_paper_summary.md`

### B. Bridge-wise baseline-vs-baseline sweep/tech comparison

```bash
python3 experiments/run_all_gem5.py \
  --gem5-bin "$GEM5_BIN" \
  --baseline-mode afo_hbm_server \
  --compare-baselines-on-sweeps \
  --only-axis all \
  --out-root results/gem5_eval_3axis_afo_vs_hbm_server_bridgewise
```

Use this run when you want A.F.O and HBM GPU-class server baseline shown side-by-side across bridge/inter-tier/technology axes.

### C. Context-length hero sweep (4K~128K, optional tech profiles)

```bash
python3 experiments/run_context_hero_gem5.py \
  --gem5-bin "$GEM5_BIN" \
  --baseline-mode afo_hbm_server \
  --include-tech-profiles \
  --out-root results/gem5_eval_context_hero_afo_vs_hbm_server_bridgewise
```

Outputs:
- `results/gem5_eval_context_hero_afo_vs_hbm_server_bridgewise/raw/context_len_hero.csv`
- `results/gem5_eval_context_hero_afo_vs_hbm_server_bridgewise/raw/context_len_hero_preview.md`

### D. Profile-guided replay validation

```bash
python3 experiments/run_profile_trace_replay.py \
  --profile-input experiments/fixtures/profile_smoke_events.jsonl \
  --gem5-bin "$GEM5_BIN" \
  --baseline-mode afo_hbm_server \
  --only-axis all \
  --out-root results/gem5_eval_profile_replay_small
```

High-load/time-compressed replay variant (more bursty):

```bash
python3 experiments/run_profile_trace_replay.py \
  --profile-input experiments/fixtures/profile_smoke_events.jsonl \
  --gem5-bin "$GEM5_BIN" \
  --baseline-mode afo_hbm_server \
  --only-axis sweep \
  --time-scale 0.02 \
  --out-root results/gem5_eval_profile_replay_small_sweep_tight_v2
```

Summarize + plot replay outputs:

```bash
python3 experiments/scripts/summarize_profile_replay_results.py \
  --results-root results \
  --out-dir results/paper_tables

python3 experiments/scripts/plot_profile_replay_validation.py \
  --results-root results \
  --out-dir results/figures
```

### E. Distribution-matched synthetic validation (ShareGPT/vLLM-style)

```bash
python3 experiments/scripts/run_distribution_matched_synthetic.py \
  --out-dir results/distribution_matched_large \
  --baselines AFO_Proposed,HBM_GPU-class_Server_Baseline \
  --requests-per-profile 96 \
  --window-size 24 \
  --seed 2026
```

Outputs:
- `results/distribution_matched_large/distribution_matched_summary.csv`
- `results/distribution_matched_large/distribution_matched_summary.md`
- `results/distribution_matched_large/distribution_matched_summary.json`

### F. Stress-validation assets (table + figure)

```bash
python3 experiments/scripts/build_stress_validation_assets.py \
  --results-root results \
  --table-out-dir results/paper_tables \
  --figure-out results/figures/fig13_stress_validation_panels.png
```

Outputs:
- `results/paper_tables/stress_validation_summary.csv`
- `results/paper_tables/stress_validation_summary.md`
- `results/paper_tables/stress_validation_table.tex`
- `results/figures/fig13_stress_validation_panels.png`

### G. Datacenter model-derived scale-out

```bash
python3 experiments/run_all_gem5_datacenter.py \
  --gem5-bin "$GEM5_BIN" \
  --baseline-mode afo_hbm_server \
  --only-axis all \
  --out-root results/gem5_eval_datacenter_afo_vs_hbm_server
```

Outputs:
- `results/gem5_eval_datacenter_afo_vs_hbm_server/raw/datacenter_cluster_summary.csv`
- `results/gem5_eval_datacenter_afo_vs_hbm_server/tables/datacenter_summary.md`

### H. Feasibility-track report bundle (optional)

```bash
./scripts/run_full_analysis.sh
```

Outputs:
- `reports/final_feasibility_report.md`
- `reports/timing_summary.md`
- `reports/signoff_checklist.md`

---

## 6) Script-to-Output Map

| Entry point | Primary output(s) | Purpose |
|---|---|---|
| `scripts/run_artifact_smoke.sh` | `results/gem5_eval_profile_replay_smoke_artifact/...` | 1-minute E2E sanity path |
| `scripts/run_reviewer_bundle.sh` | `results/*` (profile-dependent) | one-command reviewer reproducibility bundle (`quick` / `full`) |
| `experiments/run_all_gem5.py` | `results/gem5_eval_3axis_*/raw/*.csv` | core single-device baseline/sweep/tech |
| `experiments/run_context_hero_gem5.py` | `results/gem5_eval_context_hero_*/raw/context_len_hero.csv` | context-length trend map |
| `experiments/run_profile_trace_replay.py` | `results/gem5_eval_profile_replay_*/` | profile-guided replay layer |
| `experiments/scripts/summarize_profile_replay_results.py` | `results/paper_tables/profile_replay_summary.{csv,md,tex}` | replay table material |
| `experiments/scripts/plot_profile_replay_validation.py` | `results/figures/profile_replay_*.png` | replay figures |
| `experiments/scripts/run_distribution_matched_synthetic.py` | `results/distribution_matched_*/distribution_matched_summary.*` | distribution-matched validation |
| `experiments/scripts/build_stress_validation_assets.py` | `results/paper_tables/stress_validation_*`, `results/figures/fig13_*.png` | stress table + panel |
| `experiments/run_all_gem5_datacenter.py` | `results/gem5_eval_datacenter_*/tables/datacenter_summary.md` | model-derived multi-device scale-out |

---

## 7) Metric Interpretation (Important)

- `p50/p95/p99` in this repository are **modeled memory-path service metrics**, not end-to-end user request latency.
- `tok/s` and `p99 mpath` are different abstraction levels and should be interpreted together.
- Datacenter numbers are **model-derived scale-out projections** from single-device measurements + explicit fabric assumptions, not distributed runtime benchmark traces.

---

## 8) Claim Boundaries

Safe:
- bridge/inter-tier bottleneck attribution/control
- profile-guided replay validation layer
- distribution-matched synthetic robustness
- model-derived scale-out sensitivity
- timing-aware feasibility study (reports track)

Avoid:
- silicon-proven
- production-ready chip
- end-to-end production-serving benchmark
- universal superiority claim

---

## 9) Local-Only Directories (Do Not Push)

- `paper22/`
- `paper!!!!!!/`
- `paper!@!/`
- `elsarticle/`

---

## 10) Troubleshooting

- If gem5 binary is missing:
  - set `GEM5_BIN` to your built `gem5.opt`
- If protobuf import fails:
  - `python3 -m pip install --user --break-system-packages protobuf`
- If replay summary is empty:
  - verify profile input path and `results/gem5_eval_profile_replay_*/eval/raw/` contents
