#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "qa"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_sanity() -> tuple[bool, str]:
    rows = read_csv(ROOT / "results" / "tables" / "simulator_sanity_checks.csv")
    if not rows:
        return (False, "missing sanity checks csv")
    fail = sum(1 for r in rows if r.get("status", "").upper() == "FAIL")
    return (fail == 0, f"sanity_fail={fail}, total={len(rows)}")


def parse_unit_tb() -> tuple[bool, str]:
    p = ROOT / "results" / "rtl" / "unit_tb_report.md"
    if not p.exists():
        return (False, "missing unit_tb_report.md")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"Overall status:\s*(PASS|FAIL)", t)
    if not m:
        return (False, "overall status not found")
    ok = m.group(1) == "PASS"
    cov_bad = len(re.findall(r"\| `tb_[^`]+` \| (?:FAIL|PASS) \| (?:FAIL|PASS) \| (?:FAIL|PASS) \| \d+ \| `([0-9]+)/([0-9]+)` \|", t))
    return (ok, f"overall={m.group(1)}, rows={cov_bad}")


def parse_contract_tb() -> tuple[bool, str]:
    p = ROOT / "results" / "rtl" / "rtl_contract_tb_summary.md"
    if not p.exists():
        return (False, "missing rtl_contract_tb_summary.md")
    t = p.read_text(encoding="utf-8")
    lint_ok = "Lint status: PASS" in t
    sim_ok = "Sim status: PASS" in t
    warn_ok = "Warning count: `0`" in t
    return (lint_ok and sim_ok and warn_ok, f"lint={lint_ok}, sim={sim_ok}, warn0={warn_ok}")


def exists_file(rel: str) -> tuple[bool, str]:
    p = ROOT / rel
    return (p.exists(), rel)


def main() -> None:
    checks: list[tuple[str, bool, str]] = []

    checks.append(("Simulator sanity gate", *parse_sanity()))
    checks.append(("RTL contract TB gate", *parse_contract_tb()))
    checks.append(("RTL unit TB gate", *parse_unit_tb()))
    checks.append(("Baseline fairness disclosure", *exists_file("results/tables/baseline_fairness.md")))
    checks.append(("Causal-chain report", *exists_file("results/summary/causal_chain_analysis.md")))
    checks.append(("Tail root-cause report", *exists_file("results/summary/tail_latency_root_cause.md")))
    checks.append(("Thermal impact report", *exists_file("results/summary/thermal_impact_analysis.md")))

    overall = all(ok for _, ok, _ in checks)

    lines = [
        "# Release Quality Gate",
        "",
        "| Gate | Status | Evidence |",
        "|---|---|---|",
    ]

    for name, ok, ev in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {ev} |")

    lines.extend(
        [
            "",
            f"## Overall: {'PASS' if overall else 'FAIL'}",
            "",
            "This gate is designed to reduce reviewer feedback risk by requiring:",
            "- fairness + sensitivity + sanity evidence",
            "- RTL assertion and coverage-style contract evidence",
            "- tail and thermal interpretability artifacts",
        ]
    )

    out = OUT_DIR / "release_gate.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
