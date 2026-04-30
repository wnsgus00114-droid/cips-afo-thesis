# A.F.O Prototype Milestones

## Phase 0 - Architecture Spec
- Deliverables:
  - `docs/architecture/afo_system_overview.md`
  - `docs/implementation/memory_map.md`
  - `docs/implementation/block_specs.md`
- Tests:
  - interface review checklist complete
- Success criteria:
  - all blocks have defined I/O and ownership

## Phase 1 - Python Analytical Simulator
- Deliverables:
  - `sim/afo_simulator.py`
  - `experiments/configs/base.json`
- Tests:
  - single-run regression
  - monotonic sweep checks for batch/context
- Success criteria:
  - metrics generated: tps, latency, util, stall, bottleneck

## Phase 2 - Runtime Mock
- Deliverables:
  - `runtime/afo_runtime.py`
  - `docs/implementation/runtime_software_design.md`
- Tests:
  - token-step flow executes with synthetic requests
- Success criteria:
  - APIs callable end-to-end with mock scheduler

## Phase 3 - RTL Critical Blocks
- Deliverables:
  - `rtl/src/afo_addr_decoder.sv`
  - `rtl/src/afo_dma_engine.sv`
  - `rtl/src/afo_prefetch_engine.sv`
  - `rtl/src/afo_sram_bank.sv`
  - `rtl/src/afo_matrix_accel.sv`
- Tests:
  - directed TB for decode and prefetch->DMA enqueue
- Success criteria:
  - Verilator compile and directed pass

## Phase 4 - Verilator Integration
- Deliverables:
  - `rtl/src/afo_top.sv`
  - `rtl/tb/tb_afo_top.sv`
- Tests:
  - no deadlock under prefetch bursts
  - descriptor retirement correctness
- Success criteria:
  - stable cycle traces + assertion clean

## Phase 5 - FPGA Simplified Prototype
- Deliverables:
  - `fpga/` build scripts and reduced config
- Tests:
  - on-board token loop demo with reduced model
- Success criteria:
  - sustained streaming + periodic token outputs

## Phase 6 - OpenROAD ASIC Experiment
- Deliverables:
  - `openroad/` flow scripts
  - synthesized reports (area/timing/power)
- Tests:
  - lint/synth/check timing at reduced target frequency
- Success criteria:
  - first-pass PPA snapshot and hotspot analysis
