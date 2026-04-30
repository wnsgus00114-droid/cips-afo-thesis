#!/usr/bin/env python3
"""
Generate a static 3D conceptual render for A.F.O package using matplotlib.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def cuboid(ax, origin, size, color, alpha=0.5, edge="k"):
    x, y, z = origin
    dx, dy, dz = size
    v = [
        (x, y, z),
        (x + dx, y, z),
        (x + dx, y + dy, z),
        (x, y + dy, z),
        (x, y, z + dz),
        (x + dx, y, z + dz),
        (x + dx, y + dy, z + dz),
        (x, y + dy, z + dz),
    ]
    faces = [
        [v[0], v[1], v[2], v[3]],
        [v[4], v[5], v[6], v[7]],
        [v[0], v[1], v[5], v[4]],
        [v[2], v[3], v[7], v[6]],
        [v[1], v[2], v[6], v[5]],
        [v[4], v[7], v[3], v[0]],
    ]
    pc = Poly3DCollection(faces, facecolors=color, linewidths=0.8, edgecolors=edge, alpha=alpha)
    ax.add_collection3d(pc)


def main() -> None:
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    # Substrate/package base
    cuboid(ax, (0, 0, 0), (16, 12, 0.8), color="#b0b0b0", alpha=0.35)

    # Layer-2 inner HBM rectangular ring (bottom memory)
    hbm_segments = [
        (1.6, 1.6, 1.0, 12.8, 1.0, 1.4),
        (1.6, 9.4, 1.0, 12.8, 1.0, 1.4),
        (1.6, 2.6, 1.0, 1.0, 6.8, 1.4),
        (13.4, 2.6, 1.0, 1.0, 6.8, 1.4),
    ]
    for x, y, z, dx, dy, dz in hbm_segments:
        cuboid(ax, (x, y, z), (dx, dy, dz), color="#2ca25f", alpha=0.75)

    # Layer-2 outer HBF rectangular ring surrounding HBM ring
    hbf_segments = [
        (0.5, 0.5, 1.0, 15.0, 0.8, 1.6),
        (0.5, 10.7, 1.0, 15.0, 0.8, 1.6),
        (0.5, 1.3, 1.0, 0.8, 9.4, 1.6),
        (14.7, 1.3, 1.0, 0.8, 9.4, 1.6),
    ]
    for x, y, z, dx, dy, dz in hbf_segments:
        cuboid(ax, (x, y, z), (dx, dy, dz), color="#f16913", alpha=0.75)

    # Bridge slab (between bottom memory and top compute)
    cuboid(ax, (2.0, 2.0, 2.8), (12.0, 8.0, 0.15), color="#8c6d31", alpha=0.6)

    # Compute die (Layer 1 top)
    cuboid(ax, (2, 2, 3.1), (12, 8, 0.8), color="#4f81bd", alpha=0.65)

    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.set_zlim(0, 5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("A.F.O 3D Package Concept (L1 Top Compute, L2 Bottom HBM/HBF Rings)")
    ax.view_init(elev=24, azim=-58)

    out = Path("results/visualization/afo_3d_chip.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out, dpi=180)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
