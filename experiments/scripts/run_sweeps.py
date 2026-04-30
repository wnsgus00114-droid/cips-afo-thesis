#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.afo_simulator import AFOConfig, run_simulation  # noqa: E402

SIM_OUT = ROOT / "results" / "sim"

# Sweeps expanded to address reviewer feedback:
# - scenario scaling (batch/context/experts/chunk)
# - KV capacity and prefetch sensitivity
# - bridge contention + tail pressure
# - HBF latency sensitivity
SWEEPS: list[tuple[str, list[float]]] = [
    ("batch_size", [16, 32, 64, 128, 256]),
    ("context_len", [1024, 2048, 4096, 8192, 16384]),
    ("num_experts", [16, 32, 64, 128]),
    ("kv_chunk_size_kb", [64, 128, 256, 512]),
    ("prefetch_accuracy", [0.60, 0.70, 0.80, 0.90, 0.95]),
    ("shared_kv_ratio", [0.30, 0.50, 0.70, 0.85]),
    ("sram_capacity_mb", [256, 384, 512, 768, 1024]),
    ("hbf_latency_us", [4.0, 6.0, 8.0, 10.0, 12.0]),
    ("multi_tenant_users", [32, 64, 128, 256, 384]),
    ("traffic_burst_factor", [1.0, 1.5, 2.0, 2.5, 3.0]),
    ("bridge_bw_gbs", [3200, 4000, 4800, 5600, 6400]),
    ("tsv_uplink_bw_gbs", [2800, 3600, 4200, 5000, 5800]),
    ("base_die_xbar_bw_gbs", [4200, 5000, 5600, 6200, 6800]),
]

STRESS_SCENARIOS: list[tuple[str, dict]] = [
    (
        "nominal",
        {
            "multi_tenant_users": 64,
            "traffic_burst_factor": 1.0,
            "burst_probability": 0.08,
            "tail_jitter_sigma": 0.08,
            "thermal_hotspot_gain": 1.0,
            "ambient_temp_c": 35.0,
        },
    ),
    (
        "peak_traffic",
        {
            "multi_tenant_users": 256,
            "traffic_burst_factor": 2.0,
            "burst_probability": 0.14,
            "tail_jitter_sigma": 0.10,
            "thermal_hotspot_gain": 1.1,
            "ambient_temp_c": 38.0,
        },
    ),
    (
        "bridge_saturation",
        {
            "multi_tenant_users": 384,
            "traffic_burst_factor": 2.8,
            "burst_probability": 0.20,
            "tail_jitter_sigma": 0.14,
            "bridge_bw_gbs": 3600.0,
            "thermal_hotspot_gain": 1.2,
            "ambient_temp_c": 40.0,
        },
    ),
    (
        "tsv_neck_pressure",
        {
            "multi_tenant_users": 320,
            "traffic_burst_factor": 2.4,
            "burst_probability": 0.18,
            "tail_jitter_sigma": 0.13,
            "bridge_bw_gbs": 4200.0,
            "tsv_uplink_bw_gbs": 3000.0,
            "tsv_lane_util_limit": 0.82,
            "periphery_to_center_hops": 8,
            "thermal_hotspot_gain": 1.25,
            "ambient_temp_c": 41.0,
        },
    ),
    (
        "thermal_hot",
        {
            "multi_tenant_users": 192,
            "traffic_burst_factor": 1.8,
            "burst_probability": 0.12,
            "tail_jitter_sigma": 0.10,
            "ambient_temp_c": 45.0,
            "thermal_hotspot_gain": 1.35,
            "thermal_throttle_start_c": 84.0,
        },
    ),
    (
        "worst_case_tail",
        {
            "multi_tenant_users": 512,
            "traffic_burst_factor": 3.0,
            "burst_probability": 0.25,
            "tail_jitter_sigma": 0.16,
            "prefetch_accuracy": 0.80,
            "bridge_bw_gbs": 3200.0,
            "hbf_latency_us": 10.0,
            "ambient_temp_c": 45.0,
            "thermal_hotspot_gain": 1.45,
            "thermal_throttle_start_c": 82.0,
        },
    ),
]

# Keep this list stable so downstream docs/plots always find expected columns.
PRIMARY_METRICS = [
    "tokens_per_sec",
    "latency_ms_per_token",
    "latency_p50_ms",
    "latency_p90_ms",
    "latency_p99_ms",
    "latency_p999_ms",
    "latency_max_ms",
    "tail_ratio_p99_p50",
    "mem_bottleneck_pct",
    "stall_cycles_ratio",
    "sram_hit_ratio",
    "lhb_hit_ratio",
    "overlap_efficiency",
    "prefetch_coverage_ratio",
    "hbm_util",
    "hbf_util",
    "bridge_util",
    "tsv_util",
    "base_die_util",
    "bridge_contention_ms_total",
    "tsv_contention_ms_total",
    "base_route_contention_ms_total",
    "hbf_miss_penalty_ms_total",
    "burst_event_ratio",
    "shared_kv_reuse_ratio",
    "batch_gain",
    "bottleneck_compute_pct",
    "bottleneck_hbm_pct",
    "bottleneck_hbf_pct",
    "bottleneck_bridge_pct",
    "bottleneck_tsv_pct",
    "bottleneck_router_pct",
    "thermal_peak_c",
    "thermal_avg_c",
    "throttling_ratio",
    "model_predicted_token_ms",
    "model_measured_token_ms",
    "model_error_pct",
    "throughput_per_watt",
    "power_w",
    "oom_hbm",
    "oom_hbf",
]


def _is_number(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def _quantile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def aggregate_seed_runs(seed_rows: list[dict]) -> dict:
    out: dict[str, object] = {}
    if not seed_rows:
        return out

    numeric_keys = [k for k, v in seed_rows[0].items() if _is_number(v)]

    for k in numeric_keys:
        vals = [float(r[k]) for r in seed_rows]
        out[k] = _mean(vals)

    # Seed variation quality indicators
    for k in [
        "tokens_per_sec",
        "latency_ms_per_token",
        "latency_p99_ms",
        "tail_ratio_p99_p50",
        "bridge_util",
        "thermal_peak_c",
        "model_error_pct",
    ]:
        vals = [float(r[k]) for r in seed_rows]
        out[f"{k}_std"] = _std(vals)

    # Worst-case markers across seeds (reviewer-facing)
    p99_vals = [float(r["latency_p99_ms"]) for r in seed_rows]
    p999_vals = [float(r["latency_p999_ms"]) for r in seed_rows]
    max_vals = [float(r["latency_max_ms"]) for r in seed_rows]
    tps_vals = [float(r["tokens_per_sec"]) for r in seed_rows]

    out["latency_p99_worst_ms"] = max(p99_vals)
    out["latency_p999_worst_ms"] = max(p999_vals)
    out["latency_max_worst_ms"] = max(max_vals)
    out["tokens_per_sec_p05"] = _quantile(tps_vals, 0.05)
    out["tokens_per_sec_p95"] = _quantile(tps_vals, 0.95)
    out["seed_count"] = len(seed_rows)

    return out


def run_single(cfg: AFOConfig, num_tokens: int, seeds: list[int]) -> tuple[list[dict], dict]:
    raw_rows: list[dict] = []
    for seed in seeds:
        cfg_local = AFOConfig(**asdict(cfg))
        cfg_local.random_seed = int(seed)
        metrics = run_simulation(cfg_local, num_tokens=num_tokens)
        raw_rows.append({"seed": int(seed), **asdict(cfg_local), **metrics})

    agg = aggregate_seed_runs(raw_rows)
    return raw_rows, agg


def run_sweep(cfg: AFOConfig, param: str, values: list[float], num_tokens: int, seeds: list[int]) -> tuple[list[dict], list[dict]]:
    rows_agg: list[dict] = []
    rows_raw: list[dict] = []

    for value in values:
        cfg_local = AFOConfig(**asdict(cfg))
        current = getattr(cfg_local, param)
        typed_value = type(current)(value)
        setattr(cfg_local, param, typed_value)

        raw, agg = run_single(cfg_local, num_tokens=num_tokens, seeds=seeds)
        rows_raw.extend(raw)

        row = {**asdict(cfg_local), param: typed_value}
        for k in PRIMARY_METRICS:
            row[k] = float(agg.get(k, 0.0))
        # Additional robustness fields.
        for k in [
            "tokens_per_sec_std",
            "latency_ms_per_token_std",
            "latency_p99_ms_std",
            "tail_ratio_p99_p50_std",
            "bridge_util_std",
            "thermal_peak_c_std",
            "model_error_pct_std",
            "latency_p99_worst_ms",
            "latency_p999_worst_ms",
            "latency_max_worst_ms",
            "tokens_per_sec_p05",
            "tokens_per_sec_p95",
            "seed_count",
        ]:
            row[k] = float(agg.get(k, 0.0))

        rows_agg.append(row)

    return rows_agg, rows_raw


def run_stress_scenarios(cfg: AFOConfig, num_tokens: int, seeds: list[int]) -> tuple[list[dict], list[dict]]:
    agg_rows: list[dict] = []
    raw_rows: list[dict] = []

    for scenario_name, overrides in STRESS_SCENARIOS:
        cfg_local = AFOConfig(**{**asdict(cfg), **overrides})
        raw, agg = run_single(cfg_local, num_tokens=num_tokens, seeds=seeds)

        for rr in raw:
            raw_rows.append({"scenario": scenario_name, **rr})

        row = {"scenario": scenario_name, **asdict(cfg_local)}
        for k in PRIMARY_METRICS:
            row[k] = float(agg.get(k, 0.0))
        for k in [
            "tokens_per_sec_std",
            "latency_ms_per_token_std",
            "latency_p99_ms_std",
            "tail_ratio_p99_p50_std",
            "bridge_util_std",
            "thermal_peak_c_std",
            "model_error_pct_std",
            "latency_p99_worst_ms",
            "latency_p999_worst_ms",
            "latency_max_worst_ms",
            "tokens_per_sec_p05",
            "tokens_per_sec_p95",
            "seed_count",
        ]:
            row[k] = float(agg.get(k, 0.0))
        agg_rows.append(row)

    return agg_rows, raw_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_parameter_snapshot(cfg: AFOConfig, seeds: list[int], num_tokens: int) -> None:
    snapshot = {
        "config": asdict(cfg),
        "sweep_params": [{"param": p, "values": vals} for p, vals in SWEEPS],
        "stress_scenarios": [{"scenario": name, "overrides": ov} for name, ov in STRESS_SCENARIOS],
        "seeds": seeds,
        "num_tokens": num_tokens,
        "notes": "Synthetic analytical simulator with Active Base Die + TSV neck modeling; values are for architecture trend analysis and reproducibility.",
    }
    SIM_OUT.mkdir(parents=True, exist_ok=True)
    with (SIM_OUT / "parameter_snapshot.json").open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run A.F.O experiment sweeps with multi-seed aggregation")
    p.add_argument("--config", type=str, default=str(ROOT / "experiments" / "configs" / "base.json"))
    p.add_argument("--num-tokens", type=int, default=256)
    p.add_argument("--seeds", type=str, default="11,23,37")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = AFOConfig()
    with open(args.config, "r", encoding="utf-8") as f:
        override = json.load(f)
    cfg = AFOConfig(**{**asdict(cfg), **override})

    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    SIM_OUT.mkdir(parents=True, exist_ok=True)
    write_parameter_snapshot(cfg, seeds=seeds, num_tokens=args.num_tokens)

    for param, values in SWEEPS:
        rows_agg, rows_raw = run_sweep(cfg, param, values, num_tokens=args.num_tokens, seeds=seeds)
        write_csv(SIM_OUT / f"sweep_{param}.csv", rows_agg)
        write_csv(SIM_OUT / f"sweep_{param}_raw.csv", rows_raw)
        print(f"[sweep] {param}: points={len(rows_agg)}, raw_rows={len(rows_raw)}")

    stress_agg, stress_raw = run_stress_scenarios(cfg, num_tokens=args.num_tokens, seeds=seeds)
    write_csv(SIM_OUT / "stress_scenarios.csv", stress_agg)
    write_csv(SIM_OUT / "stress_scenarios_raw.csv", stress_raw)
    print(f"[stress] scenarios={len(stress_agg)}, raw_rows={len(stress_raw)}")


if __name__ == "__main__":
    main()
