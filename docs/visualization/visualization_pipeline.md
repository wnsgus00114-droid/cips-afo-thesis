# A.F.O 3D Visualization Pipeline

## 1. Goals
- Chip-level 3D: compute die + HBM/HBF + silicon bridge + SRAM regions
- System-level 3D: package + cooler + board + interconnect path
- Outputs:
  - interactive web viewer (Three.js)
  - static render (Python matplotlib)
  - Blender-render-ready scene script

## 2. File Structure
```text
/3d
  /python
    chip_3d_plot.py
  /threejs
    index.html
    main.js
  /blender
    build_scene.py
/results
  /visualization
    afo_3d_chip.png
    afo_chip_static.svg
```

## 3. Scene Setup Logic
1. define package substrate bounding box
2. place compute die at Layer 1 center
3. place Layer-2 HBM as an inner rectangular ring that fully surrounds Layer-1 compute footprint
4. place Layer-2 HBF as an outer rectangular ring that fully surrounds the HBM ring
5. place bridge slab between compute and memory layer
6. annotate logical zones (SRAM banks, NPU, GPU clusters)

## 4. Three.js Interactive Viewer
- Launch:
  - `cd 3d/threejs`
  - `python3 -m http.server 8080`
  - open `http://localhost:8080`
- Features:
  - orbit controls
  - color-coded memory/compute blocks
  - easy extension for labels and animation

## 5. Python Static Render
- Run:
  - `python3 3d/python/chip_3d_plot.py`
- Output:
  - `results/visualization/afo_3d_chip.png`

Dependency-free static render:
- Run:
  - `python3 3d/python/chip_3d_svg.py`
- Output:
  - `results/visualization/afo_chip_static.svg`

## 6. Blender Script Plan
- Use `3d/blender/build_scene.py`:
  - generate primitive meshes for blocks
  - assign materials by function class
  - set camera and lights
  - render PNG + optional turntable animation

## 7. System-level 3D Extension
- Add board, heatsink, memory VRM zone, PCIe/CXL edge connectors
- Add airflow path and thermal hotspot overlays from simulation
