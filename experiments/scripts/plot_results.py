#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = ROOT / "results" / "sim"
PLOT_DIR = ROOT / "results" / "plots"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v: str) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _safe_sorted(rows: list[dict], key: str) -> list[dict]:
    return sorted(rows, key=lambda r: to_float(r.get(key, "0")))


def _write_svg_line_chart(
    rows: list[dict],
    x_key: str,
    y_key: str,
    out_svg: Path,
    title: str,
    y_label: str,
    color: str = "#2f6fd6",
) -> bool:
    if not rows:
        return False

    rows = _safe_sorted(rows, x_key)
    xs = [to_float(r[x_key]) for r in rows]
    ys = [to_float(r.get(y_key, "0")) for r in rows]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    width, height = 980, 560
    pad_l, pad_r, pad_t, pad_b = 110, 40, 50, 100
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    def sx(v: float) -> float:
        if x_max == x_min:
            return pad_l + plot_w / 2
        return pad_l + (v - x_min) * plot_w / (x_max - x_min)

    def sy(v: float) -> float:
        if y_max == y_min:
            return pad_t + plot_h / 2
        return pad_t + plot_h - (v - y_min) * plot_h / (y_max - y_min)

    pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, ys))
    circles = "\n".join(
        f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="4.5" fill="{color}" />' for x, y in zip(xs, ys)
    )

    labels = "\n".join(
        f'<text x="{sx(x):.1f}" y="{pad_t + plot_h + 24:.1f}" text-anchor="middle" font-size="12" font-family="Times New Roman">{x:g}</text>'
        for x in xs
    )

    grid = []
    for i in range(6):
        gy = pad_t + i * (plot_h / 5)
        grid.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{pad_l + plot_w}" y2="{gy:.1f}" stroke="#e5e7eb" />')
    grid_svg = "\n".join(grid)

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\">
  <rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" fill=\"#ffffff\"/>
  <text x=\"{width/2:.1f}\" y=\"30\" text-anchor=\"middle\" font-size=\"20\" font-family=\"Times New Roman\">{title}</text>
  {grid_svg}
  <line x1=\"{pad_l}\" y1=\"{pad_t+plot_h}\" x2=\"{pad_l+plot_w}\" y2=\"{pad_t+plot_h}\" stroke=\"#333\" />
  <line x1=\"{pad_l}\" y1=\"{pad_t}\" x2=\"{pad_l}\" y2=\"{pad_t+plot_h}\" stroke=\"#333\" />
  <polyline fill=\"none\" stroke=\"{color}\" stroke-width=\"2.6\" points=\"{pts}\" />
  {circles}
  {labels}
  <text x=\"{pad_l + plot_w/2:.1f}\" y=\"{height-40}\" text-anchor=\"middle\" font-size=\"14\" font-family=\"Times New Roman\">{x_key}</text>
  <text x=\"28\" y=\"{pad_t + plot_h/2:.1f}\" transform=\"rotate(-90 28,{pad_t + plot_h/2:.1f})\" text-anchor=\"middle\" font-size=\"14\" font-family=\"Times New Roman\">{y_label}</text>
</svg>
"""
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(svg, encoding="utf-8")
    return True


def _write_svg_bar_chart(rows: list[dict], cat_key: str, y_key: str, out_svg: Path, title: str, y_label: str, color: str = "#0f766e") -> bool:
    if not rows:
        return False

    cats = [str(r[cat_key]) for r in rows]
    ys = [to_float(r.get(y_key, "0")) for r in rows]
    y_min = 0.0
    y_max = max(ys) if ys else 1.0

    width, height = 1080, 620
    pad_l, pad_r, pad_t, pad_b = 130, 60, 70, 170
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    n = max(1, len(cats))
    bar_w = plot_w / (n * 1.5)
    gap = bar_w / 2

    def sy(v: float) -> float:
        if y_max == y_min:
            return pad_t + plot_h / 2
        return pad_t + plot_h - (v - y_min) * plot_h / (y_max - y_min)

    bars = []
    x = pad_l + gap
    for c, y in zip(cats, ys):
        top = sy(y)
        bars.append(
            f'<rect x="{x:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{(pad_t+plot_h-top):.1f}" fill="{color}" opacity="0.88" />'
        )
        bars.append(
            f'<text x="{x + bar_w/2:.1f}" y="{pad_t+plot_h+26:.1f}" text-anchor="middle" font-size="12" font-family="Times New Roman">{c}</text>'
        )
        bars.append(
            f'<text x="{x + bar_w/2:.1f}" y="{top-6:.1f}" text-anchor="middle" font-size="11" font-family="Times New Roman">{y:.2f}</text>'
        )
        x += bar_w + gap

    grid = []
    for i in range(6):
        gy = pad_t + i * (plot_h / 5)
        grid.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{pad_l + plot_w}" y2="{gy:.1f}" stroke="#e5e7eb" />')

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\">
  <rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" fill=\"#ffffff\"/>
  <text x=\"{width/2:.1f}\" y=\"36\" text-anchor=\"middle\" font-size=\"22\" font-family=\"Times New Roman\">{title}</text>
  {''.join(grid)}
  <line x1=\"{pad_l}\" y1=\"{pad_t+plot_h}\" x2=\"{pad_l+plot_w}\" y2=\"{pad_t+plot_h}\" stroke=\"#333\" />
  <line x1=\"{pad_l}\" y1=\"{pad_t}\" x2=\"{pad_l}\" y2=\"{pad_t+plot_h}\" stroke=\"#333\" />
  {''.join(bars)}
  <text x=\"{pad_l + plot_w/2:.1f}\" y=\"{height-72}\" text-anchor=\"middle\" font-size=\"14\" font-family=\"Times New Roman\">{cat_key}</text>
  <text x=\"32\" y=\"{pad_t + plot_h/2:.1f}\" transform=\"rotate(-90 32,{pad_t + plot_h/2:.1f})\" text-anchor=\"middle\" font-size=\"14\" font-family=\"Times New Roman\">{y_label}</text>
</svg>
"""
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(svg, encoding="utf-8")
    return True


def save_sweep_summary(rows: list[dict], x_key: str, out_txt: Path) -> None:
    rows = _safe_sorted(rows, x_key)

    best_tps = max(rows, key=lambda r: to_float(r.get("tokens_per_sec", "0")))
    worst_tail = max(rows, key=lambda r: to_float(r.get("latency_p99_ms", "0")))
    worst_bottleneck = max(rows, key=lambda r: to_float(r.get("mem_bottleneck_pct", "0")))

    lines = [
        f"# Sweep Summary: {x_key}",
        f"best_throughput: {x_key}={best_tps[x_key]} -> {to_float(best_tps['tokens_per_sec']):.2f} tokens/sec",
        f"worst_p99_tail: {x_key}={worst_tail[x_key]} -> {to_float(worst_tail['latency_p99_ms']):.3f} ms",
        f"worst_memory_bottleneck: {x_key}={worst_bottleneck[x_key]} -> {to_float(worst_bottleneck['mem_bottleneck_pct']):.2f}%",
        "",
        "detailed_points:",
    ]

    for r in rows:
        lines.append(
            "{x_key}={x}: tps={tps:.2f}, lat={lat:.3f}ms, p99={p99:.3f}ms, tail_ratio={tail:.3f}, "
            "bridge_util={bridge:.3f}, overlap={ov:.3f}, reuse={reuse:.3f}, model_err={merr:.2f}%".format(
                x_key=x_key,
                x=r[x_key],
                tps=to_float(r.get("tokens_per_sec", "0")),
                lat=to_float(r.get("latency_ms_per_token", "0")),
                p99=to_float(r.get("latency_p99_ms", "0")),
                tail=to_float(r.get("tail_ratio_p99_p50", "0")),
                bridge=to_float(r.get("bridge_util", "0")),
                ov=to_float(r.get("overlap_efficiency", "0")),
                reuse=to_float(r.get("shared_kv_reuse_ratio", "0")),
                merr=to_float(r.get("model_error_pct", "0")),
            )
        )

    out_txt.write_text("\n".join(lines), encoding="utf-8")


def sweep_csv_paths() -> Iterable[Path]:
    for path in sorted(SIM_DIR.glob("sweep_*.csv")):
        stem = path.stem
        if stem.endswith("_raw"):
            continue
        yield path


def main() -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    metric_specs = [
        ("tokens_per_sec", "Throughput (tokens/sec)", "#1d4ed8", "throughput"),
        ("latency_p99_ms", "P99 Latency (ms)", "#b91c1c", "tail_p99"),
        ("tail_ratio_p99_p50", "Tail Ratio (p99/p50)", "#7c3aed", "tail_ratio"),
        ("mem_bottleneck_pct", "Memory Bottleneck (%)", "#b45309", "mem_bottleneck"),
        ("bridge_util", "Bridge Utilization", "#0f766e", "bridge_util"),
        ("overlap_efficiency", "Overlap Efficiency", "#0369a1", "overlap_eff"),
        ("shared_kv_reuse_ratio", "Shared KV Reuse Ratio", "#4338ca", "kv_reuse"),
        ("thermal_peak_c", "Thermal Peak (C)", "#dc2626", "thermal_peak"),
    ]

    for csv_path in sweep_csv_paths():
        x_key = csv_path.stem.replace("sweep_", "")
        rows = read_csv(csv_path)
        save_sweep_summary(rows, x_key, PLOT_DIR / f"{x_key}_summary.txt")

        for y_key, y_label, color, suffix in metric_specs:
            out_svg = PLOT_DIR / f"{x_key}_{suffix}.svg"
            _write_svg_line_chart(
                rows,
                x_key=x_key,
                y_key=y_key,
                out_svg=out_svg,
                title=f"A.F.O Sweep: {x_key} vs {y_label}",
                y_label=y_label,
                color=color,
            )

    stress_csv = SIM_DIR / "stress_scenarios.csv"
    if stress_csv.exists():
        stress = read_csv(stress_csv)
        _write_svg_bar_chart(
            stress,
            cat_key="scenario",
            y_key="latency_p99_ms",
            out_svg=PLOT_DIR / "stress_scenarios_tail_p99.svg",
            title="A.F.O Stress Scenarios: P99 Tail Latency",
            y_label="latency_p99_ms",
            color="#b91c1c",
        )
        _write_svg_bar_chart(
            stress,
            cat_key="scenario",
            y_key="bridge_util",
            out_svg=PLOT_DIR / "stress_scenarios_bridge_util.svg",
            title="A.F.O Stress Scenarios: Bridge Utilization",
            y_label="bridge_util",
            color="#0f766e",
        )
        _write_svg_bar_chart(
            stress,
            cat_key="scenario",
            y_key="thermal_peak_c",
            out_svg=PLOT_DIR / "stress_scenarios_thermal_peak.svg",
            title="A.F.O Stress Scenarios: Thermal Peak",
            y_label="thermal_peak_C",
            color="#ea580c",
        )

    print("plots generated")


if __name__ == "__main__":
    main()
