# Repository Structure

```text
/docs
  /architecture
    afo_system_overview.md
  /implementation
    afo_implementation_plan.md
    block_specs.md
    dataflow.md
    memory_map.md
    first_coding_tasks.md
    prototype_milestones.md
    runtime_software_design.md
  /report
    experimental_design.md
    power_performance_model.md
    training_design.md
    afo_research_engineering_output.md
  /visualization
    visualization_pipeline.md
  repository_structure.md

/3d
  /blender
    build_scene.py
  /python
    chip_3d_plot.py
    chip_3d_svg.py
  /threejs
    index.html
    main.js

/sim
  afo_simulator.py
  afo_training_simulator.py

/rtl
  /include
    afo_defs.svh
  /src
    afo_top.sv
    afo_addr_decoder.sv
    afo_dma_engine.sv
    afo_prefetch_engine.sv
    afo_sram_bank.sv
    afo_matrix_accel.sv
    afo_kv_sched.sv
  /tb
    tb_afo_top.sv

/runtime
  afo_runtime.py
  afo_training_runtime.py

/compiler
  (graph pass stubs and lowering passes to be added)

/experiments
  /configs
    base.json
    training_base.json
  /scripts
    run_sweeps.py
    gen_baselines.py
    plot_results.py
    make_summary.py
    run_training_experiments.py
    plot_training_results.py

/results
  /sim
  /plots
  /tables
    baseline_comparison.md
    sweep_summary.md
    plot_index.md
  /summary
    simulation_summary.md
  /training
    training_sweeps.csv
    training_scenarios.csv
    training_parameter_snapshot.json
  /training_plots
  /training_tables
    training_sweep_summary.md
    training_scenario_summary.md
  /training_summary
    training_summary.md
  /visualization

/scripts
  run_all.sh
  check_all.sh

/fpga
  (board-specific build flow placeholder)

/openroad
  (ASIC flow scripts placeholder)

/paper
  afo_paper_draft.md

/tests
  (unit/regression tests placeholder)

/benchmarks
  (workload definitions placeholder)

/visualization
  (web docs/preview assets placeholder)
```
