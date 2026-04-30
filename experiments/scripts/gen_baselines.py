#!/usr/bin/env python3

from __future__ import annotations

import csv
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


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


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


def make_rows() -> list[dict]:
    rows = []

    # 1) A.F.O full stack
    cfg_afo = AFOConfig(
        layer1_role="compute_top",
        layer2_role="memory_bottom",
        hbm_ring_coverage=1.0,
        hbf_outer_ring_coverage=1.0,
        shared_kv_ratio=0.75,
        weight_hbf_fraction=1.0,
        prefetch_accuracy=0.97,
        matrix_efficiency=0.86,
        routing_diversity=0.25,
        bridge_bw_gbs=5600.0,
        lhb_enable=1,
        lhb_size_mb=96.0,
        prefetch_depth=2,
    )
    rows.append(aggregate(cfg_afo, "AFO_full"))

    # 2) HBM-only GPU style baseline
    cfg_hbm = AFOConfig(
        weight_hbf_fraction=0.0,
        shared_kv_ratio=0.0,
        prefetch_accuracy=0.78,
        matrix_efficiency=0.64,
        top_k=6,
        routing_diversity=0.58,
        bridge_bw_gbs=4200.0,
        lhb_enable=0,
        prefetch_depth=1,
    )
    rows.append(aggregate(cfg_hbm, "HBM_only_GPU"))

    # 3) MoSKA-only (no H3)
    cfg_moska = AFOConfig(
        weight_hbf_fraction=0.0,
        shared_kv_ratio=0.62,
        prefetch_accuracy=0.90,
        top_k=4,
        matrix_efficiency=0.79,
        routing_diversity=0.28,
        bridge_bw_gbs=4500.0,
        lhb_enable=1,
        lhb_size_mb=64.0,
        prefetch_depth=1,
    )
    rows.append(aggregate(cfg_moska, "MoSKA_only"))

    # 4) H3-only (tiering but weaker shared-KV exploitation)
    cfg_h3 = AFOConfig(
        weight_hbf_fraction=1.0,
        shared_kv_ratio=0.35,
        matrix_efficiency=0.58,
        prefetch_accuracy=0.84,
        routing_diversity=0.56,
        bridge_bw_gbs=3800.0,
        lhb_enable=1,
        lhb_size_mb=48.0,
        prefetch_depth=1,
    )
    rows.append(aggregate(cfg_h3, "H3_only"))

    # 5) Apple-like UMA
    cfg_uma = AFOConfig(
        weight_hbf_fraction=0.40,
        shared_kv_ratio=0.25,
        prefetch_accuracy=0.74,
        routing_diversity=0.60,
        matrix_efficiency=0.66,
        bridge_bw_gbs=4000.0,
        lhb_enable=0,
        prefetch_depth=1,
    )
    rows.append(aggregate(cfg_uma, "Apple_like_UMA"))

    # 6) vLLM-like (paged KV, better runtime scheduling, no H3 by default)
    cfg_vllm = AFOConfig(
        weight_hbf_fraction=0.0,
        shared_kv_ratio=0.40,
        prefetch_accuracy=0.91,
        routing_diversity=0.42,
        matrix_efficiency=0.80,
        bridge_bw_gbs=4700.0,
        lhb_enable=1,
        lhb_size_mb=72.0,
        prefetch_depth=2,
    )
    rows.append(aggregate(cfg_vllm, "vLLM_like"))

    # 7) FlashAttention-like (kernel optimization strong, memory placement limited)
    cfg_flash = AFOConfig(
        weight_hbf_fraction=0.0,
        shared_kv_ratio=0.15,
        prefetch_accuracy=0.88,
        routing_diversity=0.50,
        matrix_efficiency=0.84,
        bridge_bw_gbs=4400.0,
        lhb_enable=0,
        prefetch_depth=1,
    )
    rows.append(aggregate(cfg_flash, "FlashAttn_like"))

    # 8) TensorRT-LLM-like (good kernel fusion + prefetch, mostly HBM centric)
    cfg_trt = AFOConfig(
        weight_hbf_fraction=0.10,
        shared_kv_ratio=0.30,
        prefetch_accuracy=0.93,
        routing_diversity=0.40,
        matrix_efficiency=0.83,
        bridge_bw_gbs=4900.0,
        lhb_enable=1,
        lhb_size_mb=80.0,
        prefetch_depth=2,
    )
    rows.append(aggregate(cfg_trt, "TensorRTLLM_like"))

    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict]) -> None:
    lines = [
        "# Baseline Comparison (Synthetic, Multi-Seed)",
        "",
        "Topology: `Layer1=compute_top`, `Layer2=memory_bottom`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.",
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
            "| Baseline | compute% | hbm% | hbf% | bridge% | router% | bridge_util | sram_hit | overlap_eff |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for r in rows:
        lines.append(
            "| {baseline} | {c:.2f} | {hbm:.2f} | {hbf:.2f} | {br:.2f} | {rt:.2f} | {bru:.3f} | {sram:.3f} | {ov:.3f} |".format(
                baseline=r["baseline"],
                c=r["bottleneck_compute_pct"],
                hbm=r["bottleneck_hbm_pct"],
                hbf=r["bottleneck_hbf_pct"],
                br=r["bottleneck_bridge_pct"],
                rt=r["bottleneck_router_pct"],
                bru=r["bridge_util"],
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


def main() -> None:
    rows = make_rows()
    root = Path(__file__).resolve().parents[2]
    write_csv(root / "results" / "tables" / "baseline_comparison.csv", rows)
    write_md(root / "results" / "tables" / "baseline_comparison.md", rows)
    print("wrote baseline comparison")


if __name__ == "__main__":
    main()
