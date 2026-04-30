#!/usr/bin/env python3

from __future__ import annotations

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

SEEDS = [11, 23, 37, 53, 79]
NUM_TOKENS = 256
BASE_CONFIG_PATH = ROOT / "experiments" / "configs" / "base.json"

# Reviewer fairness contract: these constraints are identical for all baselines.
LOCKED_FIELDS = [
    "layer1_role",
    "layer2_role",
    "package_topology",
    "compute_bonding",
    "memory_ring_mount",
    "hbm_ring_coverage",
    "hbf_outer_ring_coverage",
    "base_die_xbar_bw_gbs",
    "tsv_uplink_bw_gbs",
    "tsv_protocol_overhead",
    "tsv_lane_util_limit",
    "periphery_to_center_hops",
    "base_die_hop_latency_ns",
    "microbump_latency_ns",
    "hbm_stack_height_mm",
    "compute_die_thickness_mm",
    "periphery_ring_clearance_mm",
    "batch_size",
    "context_len",
    "kv_chunk_size_kb",
    "num_layers",
    "hidden_dim",
    "num_experts",
    "top_k",
    "hbm_capacity_gb",
    "hbf_capacity_gb",
    "sram_capacity_mb",
    "hbm_bw_gbs",
    "hbf_bw_gbs",
    "bridge_bw_gbs",
    "hbf_latency_us",
    "multi_tenant_users",
    "traffic_burst_factor",
    "burst_probability",
    "tail_jitter_sigma",
    "thermal_model_enable",
    "ambient_temp_c",
    "thermal_hotspot_gain",
    "thermal_throttle_start_c",
    "thermal_throttle_max",
    "thermal_shutdown_c",
    "process_slowdown_sigma",
]

BASELINE_SPECS: list[dict] = [
    {
        "name": "AFO_full",
        "description": "A.F.O full mechanism (tier-locality + route-aware shared KV + overlap contract)",
        "overrides": {
            "shared_kv_ratio": 0.75,
            "weight_hbf_fraction": 1.0,
            "prefetch_accuracy": 0.97,
            "matrix_efficiency": 0.86,
            "routing_diversity": 0.25,
            "lhb_enable": 1,
            "lhb_size_mb": 96.0,
            "prefetch_depth": 2,
        },
    },
    {
        "name": "HBM_only_GPU",
        "description": "HBM-centric decode path without shared KV reuse",
        "overrides": {
            "shared_kv_ratio": 0.00,
            "weight_hbf_fraction": 0.0,
            "prefetch_accuracy": 0.78,
            "matrix_efficiency": 0.64,
            "routing_diversity": 0.58,
            "lhb_enable": 0,
            "lhb_size_mb": 32.0,
            "prefetch_depth": 1,
        },
    },
    {
        "name": "MoSKA_only",
        "description": "Shared/Unique KV split and routing; no H3 placement (weights mostly HBM)",
        "overrides": {
            "shared_kv_ratio": 0.62,
            "weight_hbf_fraction": 0.0,
            "prefetch_accuracy": 0.90,
            "matrix_efficiency": 0.79,
            "routing_diversity": 0.28,
            "lhb_enable": 1,
            "lhb_size_mb": 64.0,
            "prefetch_depth": 1,
        },
    },
    {
        "name": "H3_only",
        "description": "HBM/HBF tiering enabled but weak shared-KV batching",
        "overrides": {
            "shared_kv_ratio": 0.35,
            "weight_hbf_fraction": 1.0,
            "prefetch_accuracy": 0.84,
            "matrix_efficiency": 0.58,
            "routing_diversity": 0.56,
            "lhb_enable": 1,
            "lhb_size_mb": 48.0,
            "prefetch_depth": 1,
        },
    },
    {
        "name": "Apple_like_UMA",
        "description": "UMA-like policy without route-aware chunk reuse",
        "overrides": {
            "shared_kv_ratio": 0.25,
            "weight_hbf_fraction": 0.40,
            "prefetch_accuracy": 0.74,
            "matrix_efficiency": 0.66,
            "routing_diversity": 0.60,
            "lhb_enable": 0,
            "lhb_size_mb": 32.0,
            "prefetch_depth": 1,
        },
    },
    {
        "name": "vLLM_like",
        "description": "Paged-KV style runtime policy baseline (synthetic 'like')",
        "overrides": {
            "shared_kv_ratio": 0.40,
            "weight_hbf_fraction": 0.0,
            "prefetch_accuracy": 0.91,
            "matrix_efficiency": 0.80,
            "routing_diversity": 0.42,
            "lhb_enable": 1,
            "lhb_size_mb": 72.0,
            "prefetch_depth": 2,
        },
    },
    {
        "name": "FlashAttn_like",
        "description": "Kernel-optimized attention baseline (synthetic 'like')",
        "overrides": {
            "shared_kv_ratio": 0.15,
            "weight_hbf_fraction": 0.0,
            "prefetch_accuracy": 0.88,
            "matrix_efficiency": 0.84,
            "routing_diversity": 0.50,
            "lhb_enable": 0,
            "lhb_size_mb": 32.0,
            "prefetch_depth": 1,
        },
    },
    {
        "name": "TensorRTLLM_like",
        "description": "Kernel fusion + scheduler baseline (synthetic 'like')",
        "overrides": {
            "shared_kv_ratio": 0.30,
            "weight_hbf_fraction": 0.10,
            "prefetch_accuracy": 0.93,
            "matrix_efficiency": 0.83,
            "routing_diversity": 0.40,
            "lhb_enable": 1,
            "lhb_size_mb": 80.0,
            "prefetch_depth": 2,
        },
    },
]


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def load_base_config() -> AFOConfig:
    cfg = AFOConfig()
    if BASE_CONFIG_PATH.exists():
        data = json.loads(BASE_CONFIG_PATH.read_text(encoding="utf-8"))
        cfg = AFOConfig(**{**asdict(cfg), **data})
    return cfg


def enforce_fairness(base: AFOConfig, candidate: AFOConfig, baseline_name: str) -> None:
    for field in LOCKED_FIELDS:
        base_v = getattr(base, field)
        cand_v = getattr(candidate, field)
        if base_v != cand_v:
            raise ValueError(
                f"Fairness contract violation in {baseline_name}: {field} base={base_v} candidate={cand_v}"
            )


def aggregate(cfg: AFOConfig, baseline_name: str) -> dict:
    runs = []
    for seed in SEEDS:
        c = AFOConfig(**asdict(cfg))
        c.random_seed = seed
        runs.append(run_simulation(c, num_tokens=NUM_TOKENS))

    keys = list(runs[0].keys())
    row = {"baseline": baseline_name}
    for k in keys:
        vals = [float(r[k]) for r in runs]
        row[k] = _mean(vals)

    row["tokens_per_sec_std"] = _std([float(r["tokens_per_sec"]) for r in runs])
    row["latency_p99_ms_std"] = _std([float(r["latency_p99_ms"]) for r in runs])
    row["tail_ratio_p99_p50_std"] = _std([float(r["tail_ratio_p99_p50"]) for r in runs])
    row["seed_count"] = len(SEEDS)
    return row


def make_rows() -> tuple[list[dict], list[dict], AFOConfig]:
    base = load_base_config()
    rows: list[dict] = []
    cfg_rows: list[dict] = []

    for spec in BASELINE_SPECS:
        merged = {**asdict(base), **spec["overrides"]}
        cfg = AFOConfig(**merged)
        enforce_fairness(base, cfg, spec["name"])

        rows.append(aggregate(cfg, spec["name"]))
        cfg_rows.append(
            {
                "baseline": spec["name"],
                "description": spec["description"],
                "shared_kv_ratio": cfg.shared_kv_ratio,
                "weight_hbf_fraction": cfg.weight_hbf_fraction,
                "prefetch_accuracy": cfg.prefetch_accuracy,
                "matrix_efficiency": cfg.matrix_efficiency,
                "routing_diversity": cfg.routing_diversity,
                "lhb_enable": cfg.lhb_enable,
                "lhb_size_mb": cfg.lhb_size_mb,
                "prefetch_depth": cfg.prefetch_depth,
                "batch_size": cfg.batch_size,
                "context_len": cfg.context_len,
                "kv_chunk_size_kb": cfg.kv_chunk_size_kb,
                "hbm_bw_gbs": cfg.hbm_bw_gbs,
                "hbf_bw_gbs": cfg.hbf_bw_gbs,
                "bridge_bw_gbs": cfg.bridge_bw_gbs,
                "tsv_uplink_bw_gbs": cfg.tsv_uplink_bw_gbs,
                "base_die_xbar_bw_gbs": cfg.base_die_xbar_bw_gbs,
            }
        )

    return rows, cfg_rows, base


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict], base: AFOConfig) -> None:
    lines = [
        "# Baseline Comparison (Synthetic, Multi-Seed)",
        "",
        "Topology: `Layer1=compute_top`, `Layer2=memory_bottom`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.",
        "",
        "## Fairness Contract",
        "- Same workload: `batch_size={}`, `context_len={}`, `kv_chunk_size_kb={}`".format(
            base.batch_size,
            base.context_len,
            base.kv_chunk_size_kb,
        ),
        "- Same memory/interface constraints: `HBM BW={}`, `HBF BW={}`, `Bridge BW={}`, `HBF latency={}us`".format(
            base.hbm_bw_gbs,
            base.hbf_bw_gbs,
            base.bridge_bw_gbs,
            base.hbf_latency_us,
        ),
        "- Same package-neck constraints: `TSV BW={} GB/s`, `Base-die BW={} GB/s`, `TSV util cap={}`".format(
            base.tsv_uplink_bw_gbs,
            base.base_die_xbar_bw_gbs,
            base.tsv_lane_util_limit,
        ),
        "- Same capacity constraints: `HBM={}GB`, `HBF={}GB`, `SRAM={}MB`".format(
            base.hbm_capacity_gb,
            base.hbf_capacity_gb,
            base.sram_capacity_mb,
        ),
        "- Only policy/algorithm knobs are varied per baseline (`shared_kv_ratio`, `weight_hbf_fraction`, `prefetch_accuracy`, `routing`, `LHB`, `matrix_efficiency`).",
        "",
        "## Core Metrics",
        "| Baseline | tokens/sec | latency_ms/token | p99_ms | tail_ratio(p99/p50) | mem_bottleneck_% | tpw |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            "| {baseline} | {tps:.2f} | {lat:.3f} | {p99:.3f} | {tail:.3f} | {mb:.2f} | {tpw:.4f} |".format(
                baseline=r["baseline"],
                tps=r["tokens_per_sec"],
                lat=r["latency_ms_per_token"],
                p99=r["latency_p99_ms"],
                tail=r["tail_ratio_p99_p50"],
                mb=r["mem_bottleneck_pct"],
                tpw=r["throughput_per_watt"],
            )
        )

    lines.extend(
        [
            "",
            "## Bottleneck Attribution",
            "| Baseline | compute% | hbm% | hbf% | bridge% | tsv% | router% | bridge_util | tsv_util | sram_hit | overlap_eff |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for r in rows:
        lines.append(
            "| {baseline} | {c:.2f} | {hbm:.2f} | {hbf:.2f} | {br:.2f} | {tsv:.2f} | {rt:.2f} | {bru:.3f} | {tsvu:.3f} | {sram:.3f} | {ov:.3f} |".format(
                baseline=r["baseline"],
                c=r["bottleneck_compute_pct"],
                hbm=r["bottleneck_hbm_pct"],
                hbf=r["bottleneck_hbf_pct"],
                br=r["bottleneck_bridge_pct"],
                tsv=r["bottleneck_tsv_pct"],
                rt=r["bottleneck_router_pct"],
                bru=r["bridge_util"],
                tsvu=r["tsv_util"],
                sram=r["sram_hit_ratio"],
                ov=r["overlap_efficiency"],
            )
        )

    lines.extend(
        [
            "",
            "## Shared-KV Reuse / Prefetch Evidence",
            "| Baseline | shared_kv_reuse_ratio | batch_gain | prefetch_coverage | lhb_hit | thermal_peak_C | model_error_% |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for r in rows:
        lines.append(
            "| {baseline} | {reuse:.3f} | {gain:.3f} | {cov:.3f} | {lhb:.3f} | {th:.2f} | {err:.2f} |".format(
                baseline=r["baseline"],
                reuse=r["shared_kv_reuse_ratio"],
                gain=r["batch_gain"],
                cov=r["prefetch_coverage_ratio"],
                lhb=r["lhb_hit_ratio"],
                th=r["thermal_peak_c"],
                err=r["model_error_pct"],
            )
        )

    lines.extend(
        [
            "",
            "Assumption note: `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines in this simulator, not measured vendor kernels.",
            f"Seed count per baseline: {len(SEEDS)}",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_fairness_md(path: Path, cfg_rows: list[dict], base: AFOConfig) -> None:
    lines = [
        "# Baseline Fairness Contract",
        "",
        "This table discloses which variables are fixed and which variables are intentionally changed.",
        "",
        "## Fixed Constraints (Identical Across Baselines)",
        "| Field | Value |",
        "|---|---:|",
    ]

    for field in LOCKED_FIELDS:
        lines.append(f"| `{field}` | `{getattr(base, field)}` |")

    lines.extend(
        [
            "",
            "## Variable Knobs by Baseline",
            "| Baseline | shared_kv_ratio | weight_hbf_fraction | prefetch_accuracy | matrix_eff | routing_div | lhb_enable | lhb_size_mb | prefetch_depth | tsv_bw | base_die_bw |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for r in cfg_rows:
        lines.append(
            "| {baseline} | {shared_kv_ratio:.2f} | {weight_hbf_fraction:.2f} | {prefetch_accuracy:.2f} | {matrix_efficiency:.2f} | {routing_diversity:.2f} | {lhb_enable} | {lhb_size_mb:.1f} | {prefetch_depth} | {tsv_uplink_bw_gbs:.0f} | {base_die_xbar_bw_gbs:.0f} |".format(
                **r
            )
        )

    lines.extend(
        [
            "",
            "## Policy-Level Baseline Note",
            "- `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` do not represent vendor-measured kernels.",
            "- They represent policy families under the same simulator constraints for fair directional comparison.",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows, cfg_rows, base = make_rows()
    write_csv(ROOT / "results" / "tables" / "baseline_comparison.csv", rows)
    write_md(ROOT / "results" / "tables" / "baseline_comparison.md", rows, base)
    write_csv(ROOT / "results" / "tables" / "baseline_configs.csv", cfg_rows)
    write_fairness_md(ROOT / "results" / "tables" / "baseline_fairness.md", cfg_rows, base)
    print("wrote baseline comparison + fairness tables")


if __name__ == "__main__":
    main()
