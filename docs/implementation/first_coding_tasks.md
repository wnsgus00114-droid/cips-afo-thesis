# First Coding Task List (Immediate)

1. Add cycle-accurate queueing model to `sim/afo_simulator.py`
- Implement per-tier request queue depth and FR-FCFS approximation.

2. Add baseline config YAML/JSON set
- Create `experiments/configs/baselines/*.json` for reproducible runs.

3. Add deterministic seed handling
- Extend simulator with `--seed` and routing randomness control.

4. Implement runtime prefetch planner class
- Add `runtime/prefetch_planner.py` with confidence-based depth logic.

5. Implement router index mock
- Add `runtime/router_index.py` with centroid table + top-k API.

6. Expand RTL DMA engine
- Add burst length, outstanding transactions, completion queue model.

7. Implement RTL SRAM allocator
- Add bank ownership map and A/B buffer swap hazard checks.

8. Add Verilator smoke test harness
- Add `rtl/tb/tb_dma_prefetch.sv` for prefetch->DMA path assertions.

9. Build compiler pass skeleton
- Add `compiler/moska_pass.py` for shared/unique attention graph rewrite.

10. Add CI-like script
- Add `scripts/check_all.sh` to run simulator smoke + lint placeholders.
