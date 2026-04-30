#!/usr/bin/env python3

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RTL_DIR = ROOT / "rtl"
OUT_DIR = ROOT / "results" / "rtl"
UNIT_DIR = OUT_DIR / "unit"
UNIT_DIR.mkdir(parents=True, exist_ok=True)

TESTS = [
    {
        "name": "tb_afo_addr_decoder",
        "tb": "tb/tb_afo_addr_decoder.sv",
        "src": ["src/afo_addr_decoder.sv"],
    },
    {
        "name": "tb_afo_prefetch_engine",
        "tb": "tb/tb_afo_prefetch_engine.sv",
        "src": ["src/afo_prefetch_engine.sv"],
    },
    {
        "name": "tb_afo_dma_engine",
        "tb": "tb/tb_afo_dma_engine.sv",
        "src": ["src/afo_dma_engine.sv"],
    },
]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(RTL_DIR), text=True, capture_output=True, check=False)


def parse_cov(text: str) -> tuple[int, int]:
    m = re.search(r"\[COV\]\s+\S+\s+covered=(\d+)\s+total=(\d+)", text)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def main() -> None:
    rows = []

    for test in TESTS:
        base_cmd = ["verilator", "-Wall", "-Wno-fatal", "--assert", "-Iinclude"]

        lint_cmd = base_cmd + ["--lint-only", test["tb"], *test["src"]]
        lint = run(lint_cmd)

        sim_cmd = base_cmd + ["--timing", "--binary", "--trace", test["tb"], *test["src"]]
        sim = run(sim_cmd)

        binary = RTL_DIR / "obj_dir" / f"V{test['name']}"
        run_ret = subprocess.run([str(binary)], cwd=str(RTL_DIR), text=True, capture_output=True, check=False)

        text = "\n".join(
            [
                f"$ {' '.join(lint_cmd)}",
                lint.stdout,
                lint.stderr,
                f"$ {' '.join(sim_cmd)}",
                sim.stdout,
                sim.stderr,
                f"$ {binary}",
                run_ret.stdout,
                run_ret.stderr,
            ]
        )

        log_path = UNIT_DIR / f"{test['name']}.log"
        log_path.write_text(text, encoding="utf-8")

        warn_count = text.count("%Warning")
        lint_pass = lint.returncode == 0 and warn_count == 0
        sim_pass = sim.returncode == 0 and run_ret.returncode == 0
        pass_mark = f"[PASS] {test['name']} assertions passed." in text
        cov_hit, cov_total = parse_cov(text)

        rows.append(
            {
                "name": test["name"],
                "lint_pass": lint_pass,
                "sim_pass": sim_pass,
                "pass_mark": pass_mark,
                "warnings": warn_count,
                "cov_hit": cov_hit,
                "cov_total": cov_total,
                "log": f"results/rtl/unit/{test['name']}.log",
            }
        )

    summary_lines = [
        "# RTL Unit TB Report",
        "",
        "| TB | Lint | Sim | PASS Mark | Warnings | Coverage | Log |",
        "|---|---|---|---|---:|---:|---|",
    ]

    all_ok = True
    for r in rows:
        lint_s = "PASS" if r["lint_pass"] else "FAIL"
        sim_s = "PASS" if r["sim_pass"] else "FAIL"
        mark_s = "PASS" if r["pass_mark"] else "FAIL"
        cov_s = f"{r['cov_hit']}/{r['cov_total']}"
        summary_lines.append(
            f"| `{r['name']}` | {lint_s} | {sim_s} | {mark_s} | {r['warnings']} | `{cov_s}` | `{r['log']}` |"
        )

        if not (r["lint_pass"] and r["sim_pass"] and r["pass_mark"] and r["warnings"] == 0 and r["cov_hit"] == r["cov_total"]):
            all_ok = False

    summary_lines.extend(
        [
            "",
            "## Quality Gate",
            f"- Overall status: {'PASS' if all_ok else 'FAIL'}",
            "- Gate criteria: lint warning=0, sim PASS, assertion PASS marker, and full TB-declared coverage bins.",
            "",
            "## Waveforms",
            "- `results/waves/tb_afo_addr_decoder.vcd`",
            "- `results/waves/tb_afo_prefetch_engine.vcd`",
            "- `results/waves/tb_afo_dma_engine.vcd`",
        ]
    )

    summary_path = OUT_DIR / "unit_tb_report.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"wrote {summary_path}")
    for r in rows:
        print(f"{r['name']}: lint={'PASS' if r['lint_pass'] else 'FAIL'} sim={'PASS' if r['sim_pass'] else 'FAIL'} cov={r['cov_hit']}/{r['cov_total']}")


if __name__ == "__main__":
    main()
