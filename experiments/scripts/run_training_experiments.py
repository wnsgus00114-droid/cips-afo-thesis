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

from sim.afo_training_simulator import AFOTrainingConfig, run_training_simulation  # noqa: E402

OUT_DIR = ROOT / "results" / "training"

MODES: dict[str, dict] = {
    "full_ft": {
        "training_mode": "full_finetune",
        "micro_batch_size": 4,
        "grad_accum_steps": 16,
        "activation_checkpoint_ratio": 0.65,
        "activation_offload_ratio": 0.35,
        "prefetch_accuracy": 0.90,
    },
    "lora_sft": {
        "training_mode": "lora_sft",
        "lora_rank": 64,
        "micro_batch_size": 8,
        "grad_accum_steps": 16,
        "activation_checkpoint_ratio": 0.45,
        "activation_offload_ratio": 0.20,
        "prefetch_accuracy": 0.92,
    },
}

SWEEPS: list[tuple[str, list[float]]] = [
    ("sequence_len", [2048, 4096, 8192, 16384]),
    ("micro_batch_size", [2, 4, 8, 12]),
    ("grad_accum_steps", [8, 16, 24, 32]),
    ("activation_checkpoint_ratio", [0.0, 0.3, 0.6, 0.8]),
    ("activation_offload_ratio", [0.0, 0.2, 0.4, 0.6]),
    ("prefetch_accuracy", [0.6, 0.75, 0.9, 0.97]),
    ("sram_capacity_mb", [256, 512, 768, 1024]),
    ("hbf_latency_us", [4, 6, 8, 10, 12]),
    ("bridge_bw_gbs", [3200, 4000, 4800, 6400]),
    ("traffic_burst_factor", [1.0, 1.5, 2.0, 2.8]),
]

SCENARIOS: list[tuple[str, dict]] = [
    (
        "full_ft_nominal",
        {
            "training_mode": "full_finetune",
            "sequence_len": 4096,
            "micro_batch_size": 4,
            "grad_accum_steps": 16,
        },
    ),
    (
        "full_ft_longctx",
        {
            "training_mode": "full_finetune",
            "sequence_len": 16384,
            "micro_batch_size": 2,
            "grad_accum_steps": 24,
            "activation_checkpoint_ratio": 0.80,
            "activation_offload_ratio": 0.55,
        },
    ),
    (
        "full_ft_thermal_hot",
        {
            "training_mode": "full_finetune",
            "ambient_temp_c": 45.0,
            "thermal_hotspot_gain": 1.35,
            "traffic_burst_factor": 2.0,
            "burst_probability": 0.12,
        },
    ),
    (
        "lora_nominal",
        {
            "training_mode": "lora_sft",
            "lora_rank": 64,
            "micro_batch_size": 8,
            "grad_accum_steps": 16,
            "activation_checkpoint_ratio": 0.45,
            "activation_offload_ratio": 0.2,
        },
    ),
    (
        "lora_throughput",
        {
            "training_mode": "lora_sft",
            "lora_rank": 32,
            "micro_batch_size": 12,
            "grad_accum_steps": 12,
            "prefetch_accuracy": 0.95,
            "bridge_bw_gbs": 5600,
        },
    ),
    (
        "lora_worst_tail",
        {
            "training_mode": "lora_sft",
            "sequence_len": 16384,
            "micro_batch_size": 12,
            "grad_accum_steps": 24,
            "traffic_burst_factor": 3.0,
            "burst_probability": 0.20,
            "tail_jitter_sigma": 0.14,
            "hbf_latency_us": 10.0,
            "bridge_bw_gbs": 3600,
            "ambient_temp_c": 45.0,
        },
    ),
]


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def _q(vals: list[float], q: float) -> float:
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


def aggregate_rows(seed_rows: list[dict]) -> dict:
    out: dict[str, float] = {}
    if not seed_rows:
        return out

    numeric_keys = []
    for k, v in seed_rows[0].items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            numeric_keys.append(k)

    for k in numeric_keys:
        vals = [float(r[k]) for r in seed_rows]
        out[k] = _mean(vals)

    for key in ["tokens_per_sec_train", "step_time_ms", "step_p99_ms", "tail_ratio_p99_p50", "train_stability_score", "convergence_proxy"]:
        vals = [float(r[key]) for r in seed_rows]
        out[f"{key}_std"] = _std(vals)

    p99_vals = [float(r["step_p99_ms"]) for r in seed_rows]
    tps_vals = [float(r["tokens_per_sec_train"]) for r in seed_rows]
    out["step_p99_worst_ms"] = max(p99_vals)
    out["tokens_per_sec_p05"] = _q(tps_vals, 0.05)
    out["tokens_per_sec_p95"] = _q(tps_vals, 0.95)
    out["seed_count"] = len(seed_rows)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_mode_sweeps(base_cfg: AFOTrainingConfig, mode_name: str, seeds: list[int], num_steps: int) -> tuple[list[dict], list[dict]]:
    mode_over = MODES[mode_name]
    base = AFOTrainingConfig(**{**asdict(base_cfg), **mode_over})
    agg_rows: list[dict] = []
    raw_rows: list[dict] = []

    for param, values in SWEEPS:
        for value in values:
            cfg = AFOTrainingConfig(**asdict(base))
            current = getattr(cfg, param)
            setattr(cfg, param, type(current)(value))

            seed_rows = []
            for seed in seeds:
                cfg_seed = AFOTrainingConfig(**asdict(cfg))
                cfg_seed.random_seed = int(seed)
                res = run_training_simulation(cfg_seed, num_steps=num_steps)
                row_raw = {"mode": mode_name, "sweep_param": param, "seed": seed, **asdict(cfg_seed), **res}
                raw_rows.append(row_raw)
                seed_rows.append(res)

            agg = aggregate_rows(seed_rows)
            row_agg = {"mode": mode_name, "sweep_param": param, **asdict(cfg), **agg}
            agg_rows.append(row_agg)

    return agg_rows, raw_rows


def run_scenarios(base_cfg: AFOTrainingConfig, seeds: list[int], num_steps: int) -> tuple[list[dict], list[dict]]:
    agg_rows: list[dict] = []
    raw_rows: list[dict] = []

    for scenario_name, over in SCENARIOS:
        cfg = AFOTrainingConfig(**{**asdict(base_cfg), **over})
        seed_rows = []
        for seed in seeds:
            cfg_seed = AFOTrainingConfig(**asdict(cfg))
            cfg_seed.random_seed = int(seed)
            res = run_training_simulation(cfg_seed, num_steps=num_steps)
            raw_rows.append({"scenario": scenario_name, "seed": seed, **asdict(cfg_seed), **res})
            seed_rows.append(res)

        agg = aggregate_rows(seed_rows)
        agg_rows.append({"scenario": scenario_name, **asdict(cfg), **agg})

    return agg_rows, raw_rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run A.F.O training experiments")
    p.add_argument("--config", type=str, default=str(ROOT / "experiments" / "configs" / "training_base.json"))
    p.add_argument("--num-steps", type=int, default=200)
    p.add_argument("--seeds", type=str, default="11,23,37")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    base_cfg = AFOTrainingConfig()
    with open(args.config, "r", encoding="utf-8") as f:
        over = json.load(f)
    base_cfg = AFOTrainingConfig(**{**asdict(base_cfg), **over})

    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]

    snap = {
        "config": asdict(base_cfg),
        "modes": MODES,
        "sweeps": [{"param": p, "values": v} for p, v in SWEEPS],
        "scenarios": [{"scenario": s, "override": o} for s, o in SCENARIOS],
        "seeds": seeds,
        "num_steps": args.num_steps,
    }
    (OUT_DIR / "training_parameter_snapshot.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")

    all_agg = []
    all_raw = []
    for mode in MODES:
        agg, raw = run_mode_sweeps(base_cfg, mode_name=mode, seeds=seeds, num_steps=args.num_steps)
        all_agg.extend(agg)
        all_raw.extend(raw)

    write_csv(OUT_DIR / "training_sweeps.csv", all_agg)
    write_csv(OUT_DIR / "training_sweeps_raw.csv", all_raw)

    s_agg, s_raw = run_scenarios(base_cfg, seeds=seeds, num_steps=args.num_steps)
    write_csv(OUT_DIR / "training_scenarios.csv", s_agg)
    write_csv(OUT_DIR / "training_scenarios_raw.csv", s_raw)

    print(f"wrote {len(all_agg)} sweep rows, {len(all_raw)} raw rows")
    print(f"wrote {len(s_agg)} scenario rows, {len(s_raw)} scenario raw rows")


if __name__ == "__main__":
    main()
