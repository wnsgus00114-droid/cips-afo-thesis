#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = ROOT / "results" / "sim"
PLOT_DIR = ROOT / "results" / "plots"
TABLE_DIR = ROOT / "results" / "tables"
SUMMARY_DIR = ROOT / "results" / "summary"


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v: str) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def best_by(rows: list[dict], key: str) -> dict:
    return max(rows, key=lambda r: to_float(r.get(key, "0")))


def worst_by(rows: list[dict], key: str) -> dict:
    return max(rows, key=lambda r: to_float(r.get(key, "0")))


def min_by(rows: list[dict], key: str) -> dict:
    return min(rows, key=lambda r: to_float(r.get(key, "0")))


def load_sweeps() -> dict[str, list[dict]]:
    data: dict[str, list[dict]] = {}
    for path in sorted(SIM_DIR.glob("sweep_*.csv")):
        if path.stem.endswith("_raw"):
            continue
        key = path.stem.replace("sweep_", "")
        data[key] = read_rows(path)
    return data


def load_sanity_counts() -> tuple[int, int]:
    path = TABLE_DIR / "simulator_sanity_checks.csv"
    if not path.exists():
        return (0, 0)
    rows = read_rows(path)
    passed = sum(1 for r in rows if r.get("status", "").upper() == "PASS")
    failed = sum(1 for r in rows if r.get("status", "").upper() == "FAIL")
    return (passed, failed)


def write_sweep_table(sweeps: dict[str, list[dict]]) -> None:
    lines = [
        "# Sweep Summary Tables (Synthetic, Multi-Seed)",
        "",
        "Topology assumption: `Top=Compute (Layer1)`, `Bottom=HBM/HBF (Layer2)`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.",
        "",
    ]

    for param, rows in sweeps.items():
        rows = sorted(rows, key=lambda r: to_float(r.get(param, "0")))
        b = best_by(rows, "tokens_per_sec")
        w = min_by(rows, "tokens_per_sec")
        wp99 = worst_by(rows, "latency_p99_ms")

        lines.extend(
            [
                f"## {param}",
                "",
                f"- Best throughput: `{param}={b[param]}` -> `{to_float(b['tokens_per_sec']):.2f}` tokens/sec",
                f"- Worst throughput: `{param}={w[param]}` -> `{to_float(w['tokens_per_sec']):.2f}` tokens/sec",
                f"- Worst p99 tail: `{param}={wp99[param]}` -> `{to_float(wp99['latency_p99_ms']):.3f}` ms",
                "",
                f"| {param} | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |",
                "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )

        for r in rows:
            lines.append(
                "| {x} | {tps:.2f} | {p99:.3f} | {tail:.3f} | {mb:.2f} | {bru:.3f} | {sram:.3f} | {ov:.3f} | {reuse:.3f} | {th:.2f} |".format(
                    x=r[param],
                    tps=to_float(r.get("tokens_per_sec", "0")),
                    p99=to_float(r.get("latency_p99_ms", "0")),
                    tail=to_float(r.get("tail_ratio_p99_p50", "0")),
                    mb=to_float(r.get("mem_bottleneck_pct", "0")),
                    bru=to_float(r.get("bridge_util", "0")),
                    sram=to_float(r.get("sram_hit_ratio", "0")),
                    ov=to_float(r.get("overlap_efficiency", "0")),
                    reuse=to_float(r.get("shared_kv_reuse_ratio", "0")),
                    th=to_float(r.get("thermal_peak_c", "0")),
                )
            )
        lines.append("")

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    (TABLE_DIR / "sweep_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_plot_index() -> None:
    lines = [
        "# Plot Index (Results Visualization)",
        "",
        "Topology assumption: `Top=Compute`, `Bottom=HBM/HBF rings`.",
        "",
        "| Plot File |",
        "|---|",
    ]

    for svg in sorted(PLOT_DIR.glob("*.svg")):
        lines.append(f"| `results/plots/{svg.name}` |")

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    (TABLE_DIR / "plot_index.md").write_text("\n".join(lines), encoding="utf-8")


def write_reproducibility(snapshot: dict) -> None:
    cfg = snapshot.get("config", {})
    seeds = snapshot.get("seeds", [])
    num_tokens = snapshot.get("num_tokens", 0)

    lines = [
        "# Reproducibility Parameters",
        "",
        f"- Seeds: `{seeds}`",
        f"- Tokens per run: `{num_tokens}`",
        "",
        "| Parameter | Value |",
        "|---|---:|",
    ]

    ordered_keys = [
        "hbm_bw_gbs",
        "hbf_bw_gbs",
        "bridge_bw_gbs",
        "hbf_latency_us",
        "sram_capacity_mb",
        "hbm_capacity_gb",
        "hbf_capacity_gb",
        "compute_tops_int8",
        "matrix_efficiency",
        "batch_size",
        "context_len",
        "num_experts",
        "kv_chunk_size_kb",
        "prefetch_accuracy",
        "shared_kv_ratio",
        "multi_tenant_users",
        "traffic_burst_factor",
        "burst_probability",
        "tail_jitter_sigma",
        "thermal_hotspot_gain",
        "ambient_temp_c",
        "process_slowdown_sigma",
    ]
    for k in ordered_keys:
        if k in cfg:
            lines.append(f"| `{k}` | `{cfg[k]}` |")

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    (TABLE_DIR / "reproducibility_params.md").write_text("\n".join(lines), encoding="utf-8")


def write_main_summary(sweeps: dict[str, list[dict]], baselines: list[dict], stress: list[dict], snapshot: dict) -> None:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    b_best = best_by(baselines, "tokens_per_sec")
    b_low_tail = min_by(baselines, "latency_p99_ms")
    b_high_tail = worst_by(baselines, "latency_p99_ms")

    stress_worst_tail = worst_by(stress, "latency_p99_ms") if stress else {}
    stress_worst_bridge_contention = worst_by(stress, "bridge_contention_ms_total") if stress else {}
    stress_worst_thermal = worst_by(stress, "thermal_peak_c") if stress else {}
    sanity_pass, sanity_fail = load_sanity_counts()

    lines = [
        "# A.F.O Simulation Summary (Reviewer-Driven Update)",
        "",
        "## 1. Physical Topology Constraint",
        "- `Top (Layer1) = Compute Chipset`",
        "- `Bottom (Layer2) = Memory Ring Tier (inner HBM ring + outer HBF ring)`",
        "- Silicon bridge links memory ring tier to compute-side SRAM staging windows",
        "",
        "## 2. Reliability Upgrade",
        "- Multi-seed aggregated sweeps and baselines are used (`seed_count` embedded in CSV).",
        "- Stress scenarios now include burst traffic, bridge saturation, and thermal-hot workload.",
        "- Reproducibility parameters are exported to `results/tables/reproducibility_params.md`.",
        "- Baseline fairness contract is explicit in `results/tables/baseline_fairness.md`.",
        "- Simulator sanity checks: `PASS={}` / `FAIL={}` (`results/tables/simulator_sanity_checks.md`).".format(
            sanity_pass, sanity_fail
        ),
        "",
        "## 3. Baseline Coverage",
        f"- Best throughput baseline: `{b_best.get('baseline', '-')}` = `{to_float(b_best.get('tokens_per_sec', '0')):.2f}` tokens/sec",
        f"- Lowest p99 baseline: `{b_low_tail.get('baseline', '-')}` = `{to_float(b_low_tail.get('latency_p99_ms', '0')):.3f}` ms",
        f"- Highest p99 baseline: `{b_high_tail.get('baseline', '-')}` = `{to_float(b_high_tail.get('latency_p99_ms', '0')):.3f}` ms",
        "- Baseline set includes: `HBM_only_GPU`, `MoSKA_only`, `H3_only`, `Apple_like_UMA`, `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like`.",
        "",
        "## 4. Tail Latency / Worst-Case",
        f"- Worst stress p99: `{stress_worst_tail.get('scenario', '-')}` -> `{to_float(stress_worst_tail.get('latency_p99_ms', '0')):.3f}` ms",
        f"- Worst stress bridge contention: `{stress_worst_bridge_contention.get('scenario', '-')}` -> `{to_float(stress_worst_bridge_contention.get('bridge_contention_ms_total', '0')):.3f}` ms",
        f"- Worst stress thermal peak: `{stress_worst_thermal.get('scenario', '-')}` -> `{to_float(stress_worst_thermal.get('thermal_peak_c', '0')):.2f}` C",
        "",
        "## 5. Why Bottleneck Changes",
        "- `bottleneck_hbm_pct`, `bottleneck_hbf_pct`, `bottleneck_bridge_pct` are now exported per point.",
        "- Review interpretation should track whether gain came from: `HBF miss penalty↓`, `bridge contention↓`, or `SRAM hit / overlap↑`.",
        "- Causal chain report: `results/summary/causal_chain_analysis.md`.",
        "",
        "## 6. Model vs Experiment Link",
        "- Each point reports `model_predicted_token_ms`, `model_measured_token_ms`, `model_error_pct`.",
        "- This directly connects analytical equations to observed simulation outputs.",
        "",
        "## 7. Shared-KV Reuse / Prefetch Evidence",
        "- Exported metrics: `shared_kv_reuse_ratio`, `batch_gain`, `prefetch_coverage_ratio`, `overlap_efficiency`, `lhb_hit_ratio`.",
        "- These metrics quantify whether MoSKA reuse and layer-overlap actually materialize.",
        "- Dedicated sensitivity panel table: `results/tables/key_sensitivity_panels.md`.",
        "",
        "## 8. Key Sweep Highlights",
    ]

    for k in sorted(sweeps.keys()):
        rows = sweeps[k]
        best_tps = best_by(rows, "tokens_per_sec")
        worst_p99 = worst_by(rows, "latency_p99_ms")
        lines.append(
            "- `{k}` best throughput: `{x}` -> `{tps:.2f}` tokens/sec; worst p99: `{wx}` -> `{wp99:.3f}` ms".format(
                k=k,
                x=best_tps[k],
                tps=to_float(best_tps.get("tokens_per_sec", "0")),
                wx=worst_p99[k],
                wp99=to_float(worst_p99.get("latency_p99_ms", "0")),
            )
        )

    lines.extend(
        [
            "",
            "## 9. Artifacts",
            "- Sweep CSV (agg/raw): `results/sim/sweep_*.csv`, `results/sim/sweep_*_raw.csv`",
            "- Stress scenarios: `results/sim/stress_scenarios.csv`",
            "- Baselines: `results/tables/baseline_comparison.csv`",
            "- Baseline fairness: `results/tables/baseline_fairness.md`",
            "- Simulator sanity checks: `results/tables/simulator_sanity_checks.md`",
            "- Sweep tables: `results/tables/sweep_summary.md`",
            "- Plot index: `results/tables/plot_index.md`",
            "- Parameter disclosure: `results/tables/reproducibility_params.md`",
            "- Causal/tail/thermal analyses: `results/summary/causal_chain_analysis.md`, `results/summary/tail_latency_root_cause.md`, `results/summary/thermal_impact_analysis.md`",
        ]
    )

    (SUMMARY_DIR / "simulation_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sweeps = load_sweeps()
    baselines = read_rows(TABLE_DIR / "baseline_comparison.csv")
    stress = read_rows(SIM_DIR / "stress_scenarios.csv") if (SIM_DIR / "stress_scenarios.csv").exists() else []
    snapshot = {}
    snap_path = SIM_DIR / "parameter_snapshot.json"
    if snap_path.exists():
        snapshot = json.loads(snap_path.read_text(encoding="utf-8"))

    write_sweep_table(sweeps)
    write_plot_index()
    if snapshot:
        write_reproducibility(snapshot)
    write_main_summary(sweeps, baselines, stress, snapshot)
    print("wrote summary + tables")


if __name__ == "__main__":
    main()
