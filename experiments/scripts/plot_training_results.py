#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRAIN_DIR = ROOT / "results" / "training"
PLOT_DIR = ROOT / "results" / "training_plots"
TABLE_DIR = ROOT / "results" / "training_tables"
SUMMARY_DIR = ROOT / "results" / "training_summary"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_f(v: str) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def line_svg(rows: list[dict], x_key: str, y_key: str, out_svg: Path, title: str, y_label: str, color: str) -> None:
    rows = sorted(rows, key=lambda r: to_f(r.get(x_key, "0")))
    xs = [to_f(r.get(x_key, "0")) for r in rows]
    ys = [to_f(r.get(y_key, "0")) for r in rows]

    if not xs:
        return

    w, h = 980, 560
    pl, pr, pt, pb = 100, 40, 50, 95
    pw, ph = w - pl - pr, h - pt - pb
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    def sx(v: float) -> float:
        if xmax == xmin:
            return pl + pw / 2
        return pl + (v - xmin) * pw / (xmax - xmin)

    def sy(v: float) -> float:
        if ymax == ymin:
            return pt + ph / 2
        return pt + ph - (v - ymin) * ph / (ymax - ymin)

    pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, ys))
    circles = "\n".join(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="4" fill="{color}" />' for x, y in zip(xs, ys))

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{w}\" height=\"{h}\">
  <rect x=\"0\" y=\"0\" width=\"{w}\" height=\"{h}\" fill=\"white\" />
  <text x=\"{w/2:.1f}\" y=\"30\" text-anchor=\"middle\" font-family=\"Times New Roman\" font-size=\"20\">{title}</text>
  <line x1=\"{pl}\" y1=\"{pt+ph}\" x2=\"{pl+pw}\" y2=\"{pt+ph}\" stroke=\"#333\" />
  <line x1=\"{pl}\" y1=\"{pt}\" x2=\"{pl}\" y2=\"{pt+ph}\" stroke=\"#333\" />
  <polyline fill=\"none\" stroke=\"{color}\" stroke-width=\"2.4\" points=\"{pts}\" />
  {circles}
  <text x=\"{pl+pw/2:.1f}\" y=\"{h-35}\" text-anchor=\"middle\" font-family=\"Times New Roman\" font-size=\"14\">{x_key}</text>
  <text x=\"28\" y=\"{pt+ph/2:.1f}\" transform=\"rotate(-90 28,{pt+ph/2:.1f})\" text-anchor=\"middle\" font-family=\"Times New Roman\" font-size=\"14\">{y_label}</text>
</svg>
"""
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(svg, encoding="utf-8")


def bar_svg(rows: list[dict], ckey: str, ykey: str, out_svg: Path, title: str, y_label: str, color: str) -> None:
    if not rows:
        return

    cats = [str(r.get(ckey, "-")) for r in rows]
    ys = [to_f(r.get(ykey, "0")) for r in rows]

    w, h = 1180, 620
    pl, pr, pt, pb = 120, 40, 60, 180
    pw, ph = w - pl - pr, h - pt - pb
    ymax = max(ys) if ys else 1.0

    n = len(cats)
    barw = pw / (n * 1.6)
    gap = barw / 1.6

    def sy(v: float) -> float:
        if ymax <= 0:
            return pt + ph
        return pt + ph - v * ph / ymax

    elems = []
    x = pl + gap
    for c, y in zip(cats, ys):
        top = sy(y)
        elems.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{barw:.1f}" height="{pt+ph-top:.1f}" fill="{color}" opacity="0.88" />')
        elems.append(f'<text x="{x+barw/2:.1f}" y="{pt+ph+22:.1f}" text-anchor="middle" font-size="12" font-family="Times New Roman">{c}</text>')
        elems.append(f'<text x="{x+barw/2:.1f}" y="{top-6:.1f}" text-anchor="middle" font-size="11" font-family="Times New Roman">{y:.2f}</text>')
        x += barw + gap

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{w}\" height=\"{h}\">
  <rect x=\"0\" y=\"0\" width=\"{w}\" height=\"{h}\" fill=\"white\" />
  <text x=\"{w/2:.1f}\" y=\"34\" text-anchor=\"middle\" font-family=\"Times New Roman\" font-size=\"21\">{title}</text>
  <line x1=\"{pl}\" y1=\"{pt+ph}\" x2=\"{pl+pw}\" y2=\"{pt+ph}\" stroke=\"#333\" />
  <line x1=\"{pl}\" y1=\"{pt}\" x2=\"{pl}\" y2=\"{pt+ph}\" stroke=\"#333\" />
  {''.join(elems)}
  <text x=\"{pl+pw/2:.1f}\" y=\"{h-70}\" text-anchor=\"middle\" font-family=\"Times New Roman\" font-size=\"14\">{ckey}</text>
  <text x=\"30\" y=\"{pt+ph/2:.1f}\" transform=\"rotate(-90 30,{pt+ph/2:.1f})\" text-anchor=\"middle\" font-family=\"Times New Roman\" font-size=\"14\">{y_label}</text>
</svg>
"""
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(svg, encoding="utf-8")


def make_tables(sweeps: list[dict], scenarios: list[dict]) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    modes = sorted({r["mode"] for r in sweeps})
    params = sorted({r["sweep_param"] for r in sweeps})

    md = [
        "# A.F.O Training Sweep Summary",
        "",
        "Topology assumption: `Top=Compute`, `Bottom=HBM/HBF memory ring tier`.",
        "",
    ]

    for mode in modes:
        md.append(f"## mode={mode}")
        md.append("")
        for param in params:
            rows = [r for r in sweeps if r["mode"] == mode and r["sweep_param"] == param]
            if not rows:
                continue
            rows = sorted(rows, key=lambda r: to_f(r.get(param, "0")))
            b_tps = max(rows, key=lambda r: to_f(r["tokens_per_sec_train"]))
            w_p99 = max(rows, key=lambda r: to_f(r["step_p99_ms"]))

            md.append(f"### {param}")
            md.append(f"- best throughput: `{param}={b_tps[param]}` -> `{to_f(b_tps['tokens_per_sec_train']):.2f}` tok/s")
            md.append(f"- worst p99 step: `{param}={w_p99[param]}` -> `{to_f(w_p99['step_p99_ms']):.2f}` ms")
            md.append("")
            md.append(f"| {param} | tok/s | step_ms | p99_ms | tail_ratio | stability | convergence | sram_hit | bridge_util | thermal_peak_C |")
            md.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

            for r in rows:
                md.append(
                    "| {x} | {tps:.2f} | {sm:.2f} | {p99:.2f} | {tail:.3f} | {stab:.2f} | {conv:.3f} | {sram:.3f} | {bru:.3f} | {th:.2f} |".format(
                        x=r[param],
                        tps=to_f(r["tokens_per_sec_train"]),
                        sm=to_f(r["step_time_ms"]),
                        p99=to_f(r["step_p99_ms"]),
                        tail=to_f(r["tail_ratio_p99_p50"]),
                        stab=to_f(r["train_stability_score"]),
                        conv=to_f(r["convergence_proxy"]),
                        sram=to_f(r["sram_hit_ratio"]),
                        bru=to_f(r["bridge_util"]),
                        th=to_f(r["thermal_peak_c"]),
                    )
                )
            md.append("")

    (TABLE_DIR / "training_sweep_summary.md").write_text("\n".join(md), encoding="utf-8")

    sc = [
        "# A.F.O Training Scenario Summary",
        "",
        "| scenario | mode | tok/s | step_ms | p99_ms | tail_ratio | stability | convergence | bridge_util | thermal_peak_C | oom_hbm | oom_hbf |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in scenarios:
        sc.append(
            "| {s} | {m} | {tps:.2f} | {sm:.2f} | {p99:.2f} | {tail:.3f} | {stab:.2f} | {conv:.3f} | {bru:.3f} | {th:.2f} | {oh} | {of} |".format(
                s=r.get("scenario", "-"),
                m=r.get("training_mode", "-"),
                tps=to_f(r.get("tokens_per_sec_train", "0")),
                sm=to_f(r.get("step_time_ms", "0")),
                p99=to_f(r.get("step_p99_ms", "0")),
                tail=to_f(r.get("tail_ratio_p99_p50", "0")),
                stab=to_f(r.get("train_stability_score", "0")),
                conv=to_f(r.get("convergence_proxy", "0")),
                bru=to_f(r.get("bridge_util", "0")),
                th=to_f(r.get("thermal_peak_c", "0")),
                oh=int(to_f(r.get("oom_hbm", "0"))),
                of=int(to_f(r.get("oom_hbf", "0"))),
            )
        )
    (TABLE_DIR / "training_scenario_summary.md").write_text("\n".join(sc), encoding="utf-8")

    best = max(scenarios, key=lambda r: to_f(r.get("train_stability_score", "0"))) if scenarios else {}
    worst = max(scenarios, key=lambda r: to_f(r.get("step_p99_ms", "0"))) if scenarios else {}

    summary = [
        "# A.F.O Training Summary",
        "",
        f"- best stability scenario: `{best.get('scenario', '-')}` score={to_f(best.get('train_stability_score', '0')):.2f}",
        f"- worst tail scenario: `{worst.get('scenario', '-')}` p99={to_f(worst.get('step_p99_ms', '0')):.2f} ms",
        "",
        "Artifacts:",
        "- `results/training/training_sweeps.csv`",
        "- `results/training/training_scenarios.csv`",
        "- `results/training_tables/training_sweep_summary.md`",
        "- `results/training_tables/training_scenario_summary.md`",
        "- `results/training_plots/*.svg`",
    ]
    (SUMMARY_DIR / "training_summary.md").write_text("\n".join(summary), encoding="utf-8")


def main() -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    sweeps = read_csv(TRAIN_DIR / "training_sweeps.csv")
    scenarios = read_csv(TRAIN_DIR / "training_scenarios.csv")

    modes = sorted({r["mode"] for r in sweeps})
    params = sorted({r["sweep_param"] for r in sweeps})

    metric_specs = [
        ("tokens_per_sec_train", "Training Throughput (tok/s)", "#1d4ed8", "throughput"),
        ("step_p99_ms", "Step P99 Latency (ms)", "#b91c1c", "tail_p99"),
        ("train_stability_score", "Training Stability Score", "#0f766e", "stability"),
        ("convergence_proxy", "Convergence Proxy", "#7c3aed", "convergence"),
        ("bridge_util", "Bridge Utilization", "#0369a1", "bridge_util"),
        ("thermal_peak_c", "Thermal Peak (C)", "#ea580c", "thermal_peak"),
    ]

    for mode in modes:
        for param in params:
            rows = [r for r in sweeps if r["mode"] == mode and r["sweep_param"] == param]
            if not rows:
                continue
            for y_key, ylabel, color, suffix in metric_specs:
                out_svg = PLOT_DIR / f"{mode}_{param}_{suffix}.svg"
                line_svg(
                    rows=rows,
                    x_key=param,
                    y_key=y_key,
                    out_svg=out_svg,
                    title=f"A.F.O Training: {mode} | {param} vs {ylabel}",
                    y_label=ylabel,
                    color=color,
                )

    bar_svg(
        scenarios,
        ckey="scenario",
        ykey="step_p99_ms",
        out_svg=PLOT_DIR / "training_scenarios_tail_p99.svg",
        title="A.F.O Training Scenarios: P99 Step Latency",
        y_label="step_p99_ms",
        color="#b91c1c",
    )
    bar_svg(
        scenarios,
        ckey="scenario",
        ykey="train_stability_score",
        out_svg=PLOT_DIR / "training_scenarios_stability.svg",
        title="A.F.O Training Scenarios: Stability Score",
        y_label="stability_score",
        color="#0f766e",
    )

    make_tables(sweeps, scenarios)
    print("training plots/tables/summary generated")


if __name__ == "__main__":
    main()
