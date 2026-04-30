#!/usr/bin/env python3

from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = ROOT / "results" / "sim"
TABLE_DIR = ROOT / "results" / "tables"


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_f(v: str) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def corr(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / math.sqrt(vx * vy)


def row_by(rows: list[dict], key: str, value: str) -> dict | None:
    for r in rows:
        if r.get(key) == value:
            return r
    return None


def pass_fail(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def add_check(checks: list[dict], name: str, result: bool, evidence: str, rationale: str) -> None:
    checks.append(
        {
            "check": name,
            "status": pass_fail(result),
            "evidence": evidence,
            "rationale": rationale,
        }
    )


def load_sweep(name: str) -> list[dict]:
    path = SIM_DIR / f"sweep_{name}.csv"
    return read_rows(path) if path.exists() else []


def main() -> None:
    checks: list[dict] = []

    baseline_path = TABLE_DIR / "baseline_comparison.csv"
    if not baseline_path.exists():
        raise SystemExit("baseline_comparison.csv not found. Run gen_baselines.py first.")

    baselines = read_rows(baseline_path)

    afo = row_by(baselines, "baseline", "AFO_full")
    hbm = row_by(baselines, "baseline", "HBM_only_GPU")
    vllm = row_by(baselines, "baseline", "vLLM_like")
    flash = row_by(baselines, "baseline", "FlashAttn_like")
    trt = row_by(baselines, "baseline", "TensorRTLLM_like")

    if not all([afo, hbm, vllm, flash, trt]):
        raise SystemExit("required baselines are missing")

    afo_tps = to_f(afo["tokens_per_sec"])
    hbm_tps = to_f(hbm["tokens_per_sec"])
    afo_p99 = to_f(afo["latency_p99_ms"])
    hbm_p99 = to_f(hbm["latency_p99_ms"])

    add_check(
        checks,
        "Anchor-1: AFO throughput exceeds HBM-only baseline",
        afo_tps > hbm_tps,
        f"AFO={afo_tps:.2f} tok/s vs HBM-only={hbm_tps:.2f} tok/s",
        "Cross-tier routing + overlap contract should outperform plain HBM-only scheduling.",
    )

    add_check(
        checks,
        "Anchor-2: AFO p99 latency lower than HBM-only baseline",
        afo_p99 < hbm_p99,
        f"AFO p99={afo_p99:.3f} ms vs HBM-only p99={hbm_p99:.3f} ms",
        "Route-aware prefetch and LHB should reduce exposed miss latency.",
    )

    norm_vllm = to_f(vllm["tokens_per_sec"]) / max(hbm_tps, 1e-9)
    norm_flash = to_f(flash["tokens_per_sec"]) / max(hbm_tps, 1e-9)
    norm_trt = to_f(trt["tokens_per_sec"]) / max(hbm_tps, 1e-9)

    add_check(
        checks,
        "Anchor-3: vLLM/Flash/TRT-like trends are in expected normalized envelopes",
        (0.90 <= norm_vllm <= 1.60) and (0.90 <= norm_flash <= 1.60) and (0.90 <= norm_trt <= 1.80),
        f"vLLM_like={norm_vllm:.3f}x, Flash_like={norm_flash:.3f}x, TensorRTLLM_like={norm_trt:.3f}x (vs HBM-only=1.0x)",
        "Synthetic baselines should follow known directional trends without implausible speedups.",
    )

    sweeps = {
        "bridge_bw_gbs": ("bridge_bw_gbs", "latency_p99_ms", "negative"),
        "tsv_uplink_bw_gbs": ("tsv_uplink_bw_gbs", "latency_p99_ms", "negative"),
        "prefetch_accuracy": ("prefetch_accuracy", "overlap_efficiency", "positive"),
        "shared_kv_ratio": ("shared_kv_ratio", "tokens_per_sec", "positive"),
    }

    for sweep_name, (x_key, y_key, direction) in sweeps.items():
        rows = load_sweep(sweep_name)
        xs = [to_f(r.get(x_key, "0")) for r in rows]
        ys = [to_f(r.get(y_key, "0")) for r in rows]
        c = corr(xs, ys)
        ok = c > 0.30 if direction == "positive" else c < -0.30
        add_check(
            checks,
            f"Trend-{sweep_name}: corr({x_key}, {y_key}) {direction}",
            ok,
            f"corr={c:.3f}; points={len(rows)}",
            "Sensitivity should preserve expected direction under fixed constraints.",
        )

    model_errors = [to_f(r.get("model_error_pct", "0")) for r in baselines]
    mean_model_err = sum(model_errors) / max(len(model_errors), 1)
    add_check(
        checks,
        "Model-link sanity: mean analytical error below 35%",
        mean_model_err < 35.0,
        f"mean(model_error_pct)={mean_model_err:.2f}%",
        "Cycle-inspired simulator remains first-order; error bound must stay moderate.",
    )

    stress_path = SIM_DIR / "stress_scenarios.csv"
    if stress_path.exists():
        stress_rows = read_rows(stress_path)
        nominal = row_by(stress_rows, "scenario", "nominal")
        tsv_pressure = row_by(stress_rows, "scenario", "tsv_neck_pressure")
        if nominal and tsv_pressure:
            add_check(
                checks,
                "Stress check: TSV neck pressure worsens p99 tail",
                to_f(tsv_pressure.get("latency_p99_ms", "0")) > to_f(nominal.get("latency_p99_ms", "0")),
                "nominal p99={:.3f} ms, tsv_neck_pressure p99={:.3f} ms".format(
                    to_f(nominal.get("latency_p99_ms", "0")),
                    to_f(tsv_pressure.get("latency_p99_ms", "0")),
                ),
                "Central TSV neck contention should increase tail under bursty multi-tenant load.",
            )

    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = len(checks) - pass_count

    md_lines = [
        "# Simulator Sanity Validation",
        "",
        "This report addresses reviewer concern: \"How do we trust the simulator?\"",
        "",
        "## Validation Policy",
        "- Anchor checks compare normalized baseline behavior against known system trends.",
        "- Trend checks verify causal sweep direction under a fixed fairness contract.",
        "- Analytical-vs-measured linkage checks bound model error.",
        "",
        f"## Summary: {pass_count} PASS / {fail_count} FAIL",
        "",
        "| Check | Status | Evidence | Rationale |",
        "|---|---|---|---|",
    ]

    for c in checks:
        md_lines.append(f"| {c['check']} | {c['status']} | {c['evidence']} | {c['rationale']} |")

    md_lines.extend(
        [
            "",
            "## Interpretation",
            "- If all checks pass, simulator outputs are directionally consistent with known-system behavior and internal equations.",
            "- If failures appear, they indicate either unrealistic parameterization or missing mechanism terms requiring model revision.",
        ]
    )

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    (TABLE_DIR / "simulator_sanity_checks.md").write_text("\n".join(md_lines), encoding="utf-8")

    csv_path = TABLE_DIR / "simulator_sanity_checks.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "evidence", "rationale"])
        writer.writeheader()
        writer.writerows(checks)

    print(f"wrote sanity checks: pass={pass_count}, fail={fail_count}")


if __name__ == "__main__":
    main()
