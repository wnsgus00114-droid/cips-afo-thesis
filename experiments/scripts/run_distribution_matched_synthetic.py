#!/usr/bin/env python3
"""
Run distribution-matched synthetic experiments using paper-anchored
ShareGPT/vLLM-style prompt/output token statistics.

This script maps request-length and Poisson-arrival statistics into
the existing A.F.O synthetic simulator knobs, then executes fairness-locked
baseline comparisons under the same sampled windows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.afo_simulator import AFOConfig, run_simulation  # noqa: E402
from experiments.scripts.gen_baselines import BASELINE_SPECS, load_base_config  # noqa: E402


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def sample_length_tokens(
    *,
    mean_tokens: float,
    sigma: float,
    tail_mix_prob: float,
    tail_alpha: float,
    max_tokens: int,
    rng: random.Random,
) -> int:
    mu = math.log(max(mean_tokens, 1e-6)) - 0.5 * sigma * sigma
    base = rng.lognormvariate(mu, sigma)

    if rng.random() < tail_mix_prob:
        tail_multiplier = rng.paretovariate(max(1.05, tail_alpha))
        base = base * tail_multiplier

    return int(round(clamp(base, 16.0, float(max_tokens))))


def sample_requests(
    profile: dict[str, Any],
    num_requests: int,
    rng: random.Random,
) -> list[dict[str, float]]:
    arrival_rate = float(profile.get("arrival_rate_rps", 2.0))
    prompt_mean = float(profile["prompt_mean_tokens"])
    output_mean = float(profile["output_mean_tokens"])
    prompt_sigma = float(profile.get("prompt_lognorm_sigma", 1.0))
    output_sigma = float(profile.get("output_lognorm_sigma", 1.0))
    tail_mix_prob = float(profile.get("tail_mix_prob", 0.08))
    tail_alpha = float(profile.get("tail_pareto_alpha", 2.0))
    max_prompt = int(profile.get("max_prompt_tokens", 4096))
    max_output = int(profile.get("max_output_tokens", 2048))

    rows: list[dict[str, float]] = []
    t_now = 0.0
    for _ in range(num_requests):
        prompt = sample_length_tokens(
            mean_tokens=prompt_mean,
            sigma=prompt_sigma,
            tail_mix_prob=tail_mix_prob,
            tail_alpha=tail_alpha,
            max_tokens=max_prompt,
            rng=rng,
        )
        output = sample_length_tokens(
            mean_tokens=output_mean,
            sigma=output_sigma,
            tail_mix_prob=tail_mix_prob,
            tail_alpha=tail_alpha,
            max_tokens=max_output,
            rng=rng,
        )
        gap_s = rng.expovariate(arrival_rate) if arrival_rate > 0 else 0.5
        t_now += gap_s
        rows.append(
            {
                "prompt_tokens": float(prompt),
                "output_tokens": float(output),
                "arrival_gap_s": float(gap_s),
                "arrival_time_s": float(t_now),
                # Decode-time effective context approximation:
                # prefill prompt + half of generated continuation.
                "effective_context_tokens": float(prompt + int(0.5 * output)),
            }
        )
    return rows


def windowed(rows: list[dict[str, float]], window_size: int) -> list[list[dict[str, float]]]:
    out: list[list[dict[str, float]]] = []
    for i in range(0, len(rows), window_size):
        chunk = rows[i : i + window_size]
        if chunk:
            out.append(chunk)
    return out


def derive_window_knobs(
    *,
    window: list[dict[str, float]],
    arrival_rate_rps: float,
    base_cfg: AFOConfig,
) -> dict[str, float]:
    prompts = [r["prompt_tokens"] for r in window]
    outputs = [r["output_tokens"] for r in window]
    eff_ctx = [r["effective_context_tokens"] for r in window]
    gaps = [max(r["arrival_gap_s"], 1e-9) for r in window]

    window_req_rate = len(window) / max(sum(gaps), 1e-9)
    burst_index = window_req_rate / max(arrival_rate_rps, 1e-9)
    output_cv = (math.sqrt(mean([(o - mean(outputs)) ** 2 for o in outputs])) / max(mean(outputs), 1e-9)) if len(outputs) > 1 else 0.0

    traffic_burst_factor = clamp(1.0 + 0.75 * (burst_index - 1.0), 0.8, 3.2)
    burst_probability = clamp(0.05 + 0.09 * max(0.0, burst_index - 1.0), 0.03, 0.30)
    tail_jitter_sigma = clamp(0.06 + 0.05 * output_cv, 0.04, 0.20)
    multi_tenant_users = int(clamp(base_cfg.multi_tenant_users * max(0.75, burst_index), 16.0, 512.0))

    context_len = int(clamp(quantile(eff_ctx, 0.90), 256.0, 131072.0))
    # Run length for this window: median decode length to avoid extreme single-sample spikes.
    num_tokens = int(clamp(quantile(outputs, 0.50), 16.0, 4096.0))

    return {
        "window_req_rate_rps": window_req_rate,
        "burst_index": burst_index,
        "traffic_burst_factor": traffic_burst_factor,
        "burst_probability": burst_probability,
        "tail_jitter_sigma": tail_jitter_sigma,
        "multi_tenant_users": float(multi_tenant_users),
        "context_len": float(context_len),
        "num_tokens": float(num_tokens),
        "prompt_mean_tokens": mean(prompts),
        "output_mean_tokens": mean(outputs),
        "output_p95_tokens": quantile(outputs, 0.95),
        "effective_context_p95_tokens": quantile(eff_ctx, 0.95),
    }


def aggregate_profile_baseline(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {}
    weights = [max(float(r["window_output_mean_tokens"]), 1.0) for r in rows]
    w_sum = sum(weights)

    def wavg(key: str) -> float:
        return sum(float(r[key]) * w for r, w in zip(rows, weights)) / max(w_sum, 1e-9)

    return {
        "tokens_per_sec_wavg": wavg("tokens_per_sec"),
        "latency_p50_ms_wavg": wavg("latency_p50_ms"),
        "latency_p95_ms_wavg": wavg("latency_p95_ms"),
        "latency_p99_ms_wavg": wavg("latency_p99_ms"),
        "stall_cycles_ratio_wavg": wavg("stall_cycles_ratio"),
        "bridge_util_wavg": wavg("bridge_util"),
        "tsv_util_wavg": wavg("tsv_util"),
        "bottleneck_bridge_pct_wavg": wavg("bottleneck_bridge_pct"),
        "bottleneck_tsv_pct_wavg": wavg("bottleneck_tsv_pct"),
        "bottleneck_router_pct_wavg": wavg("bottleneck_router_pct"),
        "window_count": float(len(rows)),
        "latency_p99_ms_max": max(float(r["latency_p99_ms"]) for r in rows),
        "tokens_per_sec_min": min(float(r["tokens_per_sec"]) for r in rows),
    }


def run_distribution_profile(
    *,
    profile: dict[str, Any],
    base_cfg: AFOConfig,
    baseline_specs: list[dict[str, Any]],
    requests_per_profile: int,
    window_size: int,
    base_seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(base_seed)
    req_rows = sample_requests(profile, requests_per_profile, rng)
    windows = windowed(req_rows, window_size)

    all_window_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    arrival_rate_rps = float(profile.get("arrival_rate_rps", 2.0))

    for b_idx, spec in enumerate(baseline_specs):
        baseline_name = str(spec["name"])
        cfg_fixed = AFOConfig(**{**asdict(base_cfg), **spec["overrides"]})
        baseline_window_rows: list[dict[str, Any]] = []

        for w_idx, w in enumerate(windows):
            knobs = derive_window_knobs(window=w, arrival_rate_rps=arrival_rate_rps, base_cfg=cfg_fixed)
            cfg = AFOConfig(**asdict(cfg_fixed))
            cfg.context_len = int(knobs["context_len"])
            cfg.traffic_burst_factor = float(knobs["traffic_burst_factor"])
            cfg.burst_probability = float(knobs["burst_probability"])
            cfg.tail_jitter_sigma = float(knobs["tail_jitter_sigma"])
            cfg.multi_tenant_users = int(knobs["multi_tenant_users"])
            cfg.random_seed = int(base_seed + 1000 * b_idx + w_idx)

            num_tokens = int(knobs["num_tokens"])
            metrics = run_simulation(cfg, num_tokens=num_tokens)

            row = {
                "profile_name": profile["name"],
                "baseline": baseline_name,
                "window_index": w_idx,
                "window_size_reqs": len(w),
                "window_req_rate_rps": knobs["window_req_rate_rps"],
                "burst_index": knobs["burst_index"],
                "window_prompt_mean_tokens": knobs["prompt_mean_tokens"],
                "window_output_mean_tokens": knobs["output_mean_tokens"],
                "window_output_p95_tokens": knobs["output_p95_tokens"],
                "window_effective_context_p95_tokens": knobs["effective_context_p95_tokens"],
                "sim_context_len": cfg.context_len,
                "sim_num_tokens": num_tokens,
                "sim_traffic_burst_factor": cfg.traffic_burst_factor,
                "sim_burst_probability": cfg.burst_probability,
                "sim_tail_jitter_sigma": cfg.tail_jitter_sigma,
                "sim_multi_tenant_users": cfg.multi_tenant_users,
                **metrics,
            }
            baseline_window_rows.append(row)
            all_window_rows.append(row)

        agg = aggregate_profile_baseline(baseline_window_rows)
        summary_rows.append(
            {
                "profile_name": profile["name"],
                "baseline": baseline_name,
                "requests_per_profile": requests_per_profile,
                "window_size": window_size,
                "arrival_rate_rps": arrival_rate_rps,
                "prompt_mean_tokens_cfg": profile["prompt_mean_tokens"],
                "output_mean_tokens_cfg": profile["output_mean_tokens"],
                **agg,
            }
        )

    return all_window_rows, summary_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Distribution-Matched Synthetic Experiment Summary",
        "",
        "Paper-anchored profiles are mapped into synthetic input knobs (context length, decode steps, arrival-driven burstiness).",
        "",
        "| Profile | Baseline | Tok/s (wavg) | p99 mpath (ms, wavg) | Stall (wavg) | Bridge util (wavg) | Inter-tier util (wavg) | Bridge share % | Inter-tier share % |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary_rows:
        lines.append(
            "| {profile} | {baseline} | {tps:.2f} | {p99:.6f} | {stall:.4f} | {bu:.4f} | {iu:.4f} | {bb:.2f} | {ib:.2f} |".format(
                profile=r["profile_name"],
                baseline=r["baseline"],
                tps=float(r.get("tokens_per_sec_wavg", 0.0)),
                p99=float(r.get("latency_p99_ms_wavg", 0.0)),
                stall=float(r.get("stall_cycles_ratio_wavg", 0.0)),
                bu=float(r.get("bridge_util_wavg", 0.0)),
                iu=float(r.get("tsv_util_wavg", 0.0)),
                bb=float(r.get("bottleneck_bridge_pct_wavg", 0.0)),
                ib=float(r.get("bottleneck_tsv_pct_wavg", 0.0)),
            )
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run distribution-matched synthetic experiments (ShareGPT/vLLM-style profiles)."
    )
    p.add_argument(
        "--profiles-config",
        type=Path,
        default=ROOT / "experiments" / "configs" / "distribution_matched_profiles.json",
        help="Profile JSON path.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results" / "distribution_matched",
        help="Output directory.",
    )
    p.add_argument("--requests-per-profile", type=int, default=96)
    p.add_argument("--window-size", type=int, default=24)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument(
        "--baselines",
        type=str,
        default="AFO_Proposed,HBM_GPU_Baseline,H3_Hybrid_Memory_Baseline",
        help="Comma-separated baseline names from gen_baselines.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg_data = json.loads(args.profiles_config.read_text(encoding="utf-8"))
    profiles = cfg_data.get("profiles", [])
    if not profiles:
        raise SystemExit(f"No profiles found in {args.profiles_config}")

    requested_baselines = {x.strip() for x in args.baselines.split(",") if x.strip()}
    baseline_specs = [b for b in BASELINE_SPECS if b["name"] in requested_baselines]
    if not baseline_specs:
        raise SystemExit(f"No matched baselines for: {sorted(requested_baselines)}")

    base_cfg = load_base_config()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    all_windows: list[dict[str, Any]] = []
    all_summary: list[dict[str, Any]] = []

    for idx, profile in enumerate(profiles):
        w_rows, s_rows = run_distribution_profile(
            profile=profile,
            base_cfg=base_cfg,
            baseline_specs=baseline_specs,
            requests_per_profile=args.requests_per_profile,
            window_size=args.window_size,
            base_seed=args.seed + 100 * idx,
        )
        all_windows.extend(w_rows)
        all_summary.extend(s_rows)

    windows_csv = out_dir / "distribution_matched_windows.csv"
    summary_csv = out_dir / "distribution_matched_summary.csv"
    summary_md = out_dir / "distribution_matched_summary.md"
    summary_json = out_dir / "distribution_matched_summary.json"

    write_csv(windows_csv, all_windows)
    write_csv(summary_csv, all_summary)
    write_markdown(summary_md, all_summary)
    summary_json.write_text(json.dumps(all_summary, indent=2), encoding="utf-8")

    print(f"[ok] wrote {windows_csv}")
    print(f"[ok] wrote {summary_csv}")
    print(f"[ok] wrote {summary_md}")
    print(f"[ok] wrote {summary_json}")


if __name__ == "__main__":
    main()

