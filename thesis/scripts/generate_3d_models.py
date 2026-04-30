#!/usr/bin/env python3
"""
Generate detailed 3D models for A.F.O:
1) chip_package (Layer-1 compute + Layer-2 HBM-inner/HBF-outer rings + bridge + labeled regions)
2) system_full (chip + board + heatsink + vrm + interconnect)

Outputs:
- OBJ + MTL (for GitHub 3D preview and mesh tools)
- ASCII STL (alternative GitHub 3D preview path)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Material:
    name: str
    kd: tuple[float, float, float]


@dataclass
class Box:
    name: str
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    material: str


# 12 triangles per cuboid (2 per face * 6 faces)
FACES = [
    (0, 1, 2), (0, 2, 3),  # bottom
    (4, 6, 5), (4, 7, 6),  # top
    (0, 4, 5), (0, 5, 1),  # front
    (1, 5, 6), (1, 6, 2),  # right
    (2, 6, 7), (2, 7, 3),  # back
    (3, 7, 4), (3, 4, 0),  # left
]


def box_vertices(b: Box) -> list[tuple[float, float, float]]:
    x, y, z, dx, dy, dz = b.x, b.y, b.z, b.dx, b.dy, b.dz
    return [
        (x, y, z),
        (x + dx, y, z),
        (x + dx, y + dy, z),
        (x, y + dy, z),
        (x, y, z + dz),
        (x + dx, y, z + dz),
        (x + dx, y + dy, z + dz),
        (x, y + dy, z + dz),
    ]


def normal(v1, v2, v3):
    ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
    bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    mag = (nx * nx + ny * ny + nz * nz) ** 0.5
    if mag == 0:
        return (0.0, 0.0, 1.0)
    return (nx / mag, ny / mag, nz / mag)


def write_mtl(path: Path, materials: list[Material]) -> None:
    lines = []
    for m in materials:
        lines.append(f"newmtl {m.name}")
        lines.append("Ka 0.1 0.1 0.1")
        lines.append(f"Kd {m.kd[0]:.4f} {m.kd[1]:.4f} {m.kd[2]:.4f}")
        lines.append("Ks 0.15 0.15 0.15")
        lines.append("Ns 60")
        lines.append("d 1.0")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_obj(path: Path, mtl_name: str, boxes: list[Box]) -> None:
    lines = [f"mtllib {mtl_name}"]
    v_offset = 1

    for b in boxes:
        verts = box_vertices(b)
        lines.append(f"o {b.name}")
        lines.append(f"usemtl {b.material}")
        for vx, vy, vz in verts:
            lines.append(f"v {vx:.6f} {vy:.6f} {vz:.6f}")

        for tri in FACES:
            a, c, d = tri
            lines.append(f"f {v_offset + a} {v_offset + c} {v_offset + d}")

        v_offset += 8

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ascii_stl(path: Path, solid_name: str, boxes: list[Box]) -> None:
    lines = [f"solid {solid_name}"]
    for b in boxes:
        verts = box_vertices(b)
        for tri in FACES:
            i1, i2, i3 = tri
            v1, v2, v3 = verts[i1], verts[i2], verts[i3]
            nx, ny, nz = normal(v1, v2, v3)
            lines.append(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}")
            lines.append("    outer loop")
            lines.append(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}")
            lines.append(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}")
            lines.append(f"      vertex {v3[0]:.6e} {v3[1]:.6e} {v3[2]:.6e}")
            lines.append("    endloop")
            lines.append("  endfacet")
    lines.append(f"endsolid {solid_name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def chip_model() -> tuple[list[Material], list[Box]]:
    mats = [
        Material("substrate", (0.53, 0.53, 0.53)),
        Material("compute_die", (0.20, 0.45, 0.86)),
        Material("bridge", (0.52, 0.39, 0.16)),
        Material("hbm", (0.12, 0.66, 0.31)),
        Material("hbf", (0.95, 0.47, 0.10)),
        Material("sram_zone", (0.04, 0.55, 0.55)),
        Material("npu_zone", (0.82, 0.33, 0.19)),
        Material("gpu_zone", (0.58, 0.27, 0.80)),
        Material("cpu_zone", (0.25, 0.32, 0.71)),
    ]

    boxes: list[Box] = []
    boxes.append(Box("substrate", 0, 0, 0, 220, 160, 8, "substrate"))
    # Layer-2 bottom memory rings are placed first (lower z),
    # then bridge, then Layer-1 top compute die.
    boxes.append(Box("bridge", 28, 23, 30, 164, 114, 2.2, "bridge"))
    boxes.append(Box("compute_die", 30, 25, 34, 160, 110, 9, "compute_die"))

    # Floorplan overlays on compute die
    boxes.append(Box("cpu_cluster", 40, 95, 43.2, 45, 30, 2.2, "cpu_zone"))
    boxes.append(Box("gpu_array_w", 40, 30, 43.2, 55, 55, 2.2, "gpu_zone"))
    boxes.append(Box("gpu_array_e", 125, 30, 43.2, 55, 55, 2.2, "gpu_zone"))
    boxes.append(Box("npu_matrix", 98, 95, 43.2, 52, 30, 2.2, "npu_zone"))
    boxes.append(Box("sram_banks", 96, 58, 43.2, 58, 28, 2.2, "sram_zone"))

    # Layer-2 inner HBM rectangular ring around full Layer-1 compute footprint
    boxes.append(Box("hbm_ring_bottom", 25, 18, 10, 170, 14, 16, "hbm"))
    boxes.append(Box("hbm_ring_top", 25, 128, 10, 170, 14, 16, "hbm"))
    boxes.append(Box("hbm_ring_left", 25, 32, 10, 14, 96, 16, "hbm"))
    boxes.append(Box("hbm_ring_right", 181, 32, 10, 14, 96, 16, "hbm"))

    # Layer-2 outer HBF rectangular ring around HBM ring
    boxes.append(Box("hbf_ring_bottom", 8, 2, 10, 204, 12, 18, "hbf"))
    boxes.append(Box("hbf_ring_top", 8, 146, 10, 204, 12, 18, "hbf"))
    boxes.append(Box("hbf_ring_left", 8, 14, 10, 12, 132, 18, "hbf"))
    boxes.append(Box("hbf_ring_right", 200, 14, 10, 12, 132, 18, "hbf"))

    return mats, boxes


def system_model() -> tuple[list[Material], list[Box]]:
    mats = [
        Material("board", (0.10, 0.43, 0.19)),
        Material("socket", (0.20, 0.20, 0.24)),
        Material("chip_pkg", (0.20, 0.45, 0.86)),
        Material("heatsink", (0.75, 0.77, 0.79)),
        Material("fan", (0.18, 0.18, 0.18)),
        Material("vrm", (0.45, 0.45, 0.50)),
        Material("cxl", (0.95, 0.62, 0.14)),
        Material("dram", (0.22, 0.60, 0.58)),
        Material("psu", (0.35, 0.35, 0.40)),
    ]

    boxes: list[Box] = []
    boxes.append(Box("main_board", 0, 0, 0, 520, 330, 10, "board"))
    boxes.append(Box("chip_socket", 170, 100, 12, 180, 120, 8, "socket"))
    boxes.append(Box("afo_chip_pkg", 190, 118, 22, 140, 85, 18, "chip_pkg"))

    # Cooling assembly
    boxes.append(Box("heatsink_base", 180, 108, 42, 160, 105, 8, "heatsink"))
    for i in range(10):
        boxes.append(Box(f"fin_{i}", 186 + i * 14, 112, 50, 6, 96, 34, "heatsink"))
    boxes.append(Box("fan_hub", 245, 145, 86, 30, 30, 8, "fan"))
    boxes.append(Box("fan_frame", 220, 120, 82, 80, 80, 6, "fan"))

    # VRM phases
    for i in range(8):
        boxes.append(Box(f"vrm_{i}", 120 + i * 20, 70, 12, 14, 18, 8, "vrm"))

    # CXL / PCIe connectors
    boxes.append(Box("cxl_slot0", 380, 40, 12, 110, 16, 12, "cxl"))
    boxes.append(Box("cxl_slot1", 380, 70, 12, 110, 16, 12, "cxl"))

    # DIMM-like memory modules
    boxes.append(Box("dram_mod0", 70, 245, 12, 140, 16, 24, "dram"))
    boxes.append(Box("dram_mod1", 70, 270, 12, 140, 16, 24, "dram"))

    # Power domain brick
    boxes.append(Box("psu_block", 20, 20, 12, 70, 45, 24, "psu"))

    return mats, boxes


def generate_one(base: Path, stem: str, mats: list[Material], boxes: list[Box]) -> None:
    obj = base / f"{stem}.obj"
    mtl = base / f"{stem}.mtl"
    stl = base / f"{stem}.stl"

    write_mtl(mtl, mats)
    write_obj(obj, mtl.name, boxes)
    write_ascii_stl(stl, stem, boxes)


def main() -> None:
    out = Path("thesis/docs/assets/models")
    out.mkdir(parents=True, exist_ok=True)

    mats, boxes = chip_model()
    generate_one(out, "afo_chip_package_3d", mats, boxes)

    mats2, boxes2 = system_model()
    generate_one(out, "afo_hardware_system_3d", mats2, boxes2)

    print("Generated 3D models:")
    for p in sorted(out.glob("afo_*.*")):
        print(" -", p)


if __name__ == "__main__":
    main()
