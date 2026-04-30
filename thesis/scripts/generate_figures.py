#!/usr/bin/env python3
"""
Create publication-ready annotated figures for A.F.O thesis docs/paper.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch


OUT = Path("thesis/docs/assets/figures")
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name: str):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=300)
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)


def fig_chip_3d_explained():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor("#f7f9fc")

    # Base shapes (pseudo-3D perspective)
    ax.add_patch(Rectangle((0.08, 0.08), 0.84, 0.22, facecolor="#8e8e8e", alpha=0.35, edgecolor="#4f4f4f"))
    ax.add_patch(Rectangle((0.16, 0.18), 0.68, 0.26, facecolor="#3b82f6", alpha=0.65, edgecolor="#1d4ed8"))
    ax.add_patch(Rectangle((0.15, 0.45), 0.70, 0.04, facecolor="#8b5a2b", alpha=0.85, edgecolor="#70421d"))

    # Layer-2 memory rings:
    # inner HBM rectangular ring around full compute footprint
    ax.add_patch(Rectangle((0.13, 0.16), 0.76, 0.30, facecolor="#16a34a", edgecolor="#166534", alpha=0.22))
    ax.add_patch(Rectangle((0.19, 0.22), 0.64, 0.18, facecolor="#f7f9fc", edgecolor="#f7f9fc", alpha=1.0))
    # outer HBF rectangular ring around HBM ring
    ax.add_patch(Rectangle((0.08, 0.12), 0.86, 0.38, facecolor="#f97316", edgecolor="#c2410c", alpha=0.18))
    ax.add_patch(Rectangle((0.13, 0.16), 0.76, 0.30, facecolor="#f7f9fc", edgecolor="#f7f9fc", alpha=1.0))

    # Compute zones
    ax.add_patch(Rectangle((0.18, 0.38), 0.16, 0.05, facecolor="#1e40af", alpha=0.9))
    ax.text(0.19, 0.402, "CPU Cluster", color="white", fontsize=9)

    ax.add_patch(Rectangle((0.18, 0.26), 0.22, 0.10, facecolor="#7e22ce", alpha=0.8))
    ax.text(0.20, 0.305, "GPU-SIMT", color="white", fontsize=10)

    ax.add_patch(Rectangle((0.42, 0.26), 0.18, 0.10, facecolor="#c2410c", alpha=0.85))
    ax.text(0.44, 0.305, "NPU/Matrix", color="white", fontsize=10)

    ax.add_patch(Rectangle((0.62, 0.26), 0.18, 0.10, facecolor="#0f766e", alpha=0.9))
    ax.text(0.64, 0.305, "768MB SRAM", color="white", fontsize=10)

    # Callouts
    callouts = [
        ((0.11, 0.34), (0.01, 0.45), "Layer-2 Bottom Inner HBM Ring\nRuntime KV / Activations / Hot data"),
        ((0.90, 0.28), (0.74, 0.70), "Layer-2 Bottom Outer HBF Ring\nRO Weights / Shared KV / Cold KV"),
        ((0.50, 0.47), (0.72, 0.60), "Silicon Bridge (EMIB-like)\nVN0/VN1/VN2 QoS"),
        ((0.73, 0.31), (0.88, 0.36), "Latency Hiding Buffer\nA/B Double Buffer Staging"),
    ]
    for (x1, y1), (x2, y2), t in callouts:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=12, color="#1f2937", lw=1.2))
        ax.text(x2 + 0.005, y2, t, fontsize=9, va="center", ha="left", color="#111827")

    ax.text(0.03, 0.94, "A.F.O 3D Chip Package (Detailed Annotated View)", fontsize=16, weight="bold", color="#111827")
    ax.text(0.03, 0.90, "Layer-1 Top Compute SoC + Layer-2 Bottom HBM/HBF rectangular rings + Silicon Bridge", fontsize=11, color="#374151")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    save(fig, "fig_chip_3d_annotated")


def fig_system_3d_explained():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor("#f8fafc")

    ax.add_patch(Rectangle((0.05, 0.08), 0.90, 0.45, facecolor="#14532d", alpha=0.35, edgecolor="#166534"))
    ax.add_patch(Rectangle((0.35, 0.20), 0.25, 0.15, facecolor="#3b82f6", alpha=0.8, edgecolor="#1e3a8a"))
    ax.add_patch(Rectangle((0.33, 0.36), 0.29, 0.09, facecolor="#9ca3af", alpha=0.85, edgecolor="#6b7280"))

    for i in range(8):
        ax.add_patch(Rectangle((0.20 + i * 0.035, 0.16), 0.022, 0.03, facecolor="#6b7280", edgecolor="#374151"))

    ax.add_patch(Rectangle((0.72, 0.14), 0.18, 0.03, facecolor="#f59e0b", edgecolor="#b45309"))
    ax.add_patch(Rectangle((0.72, 0.20), 0.18, 0.03, facecolor="#f59e0b", edgecolor="#b45309"))

    ax.add_patch(Rectangle((0.08, 0.40), 0.22, 0.03, facecolor="#0f766e", edgecolor="#0f766e"))
    ax.add_patch(Rectangle((0.08, 0.45), 0.22, 0.03, facecolor="#0f766e", edgecolor="#0f766e"))

    callouts = [
        ((0.48, 0.275), (0.64, 0.30), "A.F.O Chip Package\n(L1 top compute + L2 bottom HBM/HBF rings)"),
        ((0.47, 0.41), (0.67, 0.49), "Cooling Assembly\n(heatsink fin stack + fan)"),
        ((0.28, 0.17), (0.07, 0.17), "VRM Phases\n(high-current NPU/GPU rails)"),
        ((0.80, 0.20), (0.93, 0.23), "CXL/PCIe Slots\n(scale-out memory/fabric)"),
        ((0.16, 0.46), (0.04, 0.52), "DIMM-like Modules\n(host memory + metadata caches)"),
    ]
    for (x1, y1), (x2, y2), t in callouts:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=12, color="#111827", lw=1.2))
        ax.text(x2 + 0.005, y2, t, fontsize=9, va="center", color="#111827")

    ax.text(0.03, 0.93, "A.F.O Hardware System 3D View (Chip-in-System)", fontsize=16, weight="bold", color="#111827")
    ax.text(0.03, 0.89, "Board + Power + Cooling + Interconnect around A.F.O package", fontsize=11, color="#374151")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    save(fig, "fig_system_3d_annotated")


def fig_dataflow_pipeline():
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_facecolor("#ffffff")

    stages = [
        (0.03, "HBF/HBM\n(Read-optimized + runtime tier)"),
        (0.20, "Silicon Bridge\n(VN0/VN1/VN2 QoS)"),
        (0.38, "SRAM A/B + LHB\n(staging + miss absorb)"),
        (0.58, "Shared KV GEMM\n(batch aggregated)"),
        (0.76, "Unique KV GEMV\n(per-request path)"),
        (0.90, "NPU FFN/MoE\noutput token"),
    ]

    for x, txt in stages:
        ax.add_patch(Rectangle((x, 0.35), 0.12, 0.30, facecolor="#dbeafe", edgecolor="#1e3a8a"))
        ax.text(x + 0.06, 0.50, txt, fontsize=9, ha="center", va="center", color="#0f172a")

    for i in range(len(stages) - 1):
        x1 = stages[i][0] + 0.12
        x2 = stages[i + 1][0]
        ax.add_patch(FancyArrowPatch((x1, 0.50), (x2, 0.50), arrowstyle="-|>", mutation_scale=14, lw=1.4, color="#1f2937"))

    ax.text(0.02, 0.87, "Layer N compute overlaps prefetch of Layer N+1 weights/KV/routing metadata", fontsize=11, color="#374151")
    ax.text(0.02, 0.80, "MoSKA path: shared-KV chunk routing + GEMM conversion to improve arithmetic intensity", fontsize=11, color="#374151")

    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1)
    ax.axis("off")
    save(fig, "fig_dataflow_pipeline")


def main():
    fig_chip_3d_explained()
    fig_system_3d_explained()
    fig_dataflow_pipeline()
    print("Generated figures in", OUT)


if __name__ == "__main__":
    main()
