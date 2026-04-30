# RTL Contract TB Summary

## Execution
- Lint status: PASS
- Sim status: PASS
- Warning count: `0`
- Waveform: `results/waves/tb_afo_top.vcd`
- Full log: `results/rtl/tb_afo_top_run.log`

## Scenario Metrics
| Scenario | Check | Result |
|---|---|---:|
| Nominal | queue remains shallow (`o_dma_qmax<=2`) | PASS (assertion in TB) |
| Invalid Address | prefetch issue is blocked on decode fault | PASS (assertion in TB) |
| Saturation Proxy | peak queue depth | `12` |
| Saturation Proxy | drain cycles after ready release | `13` |
| Saturation Proxy | drained descriptor count | `12` |

## Experiment Linkage
- This TB approximates bridge contention with `i_dma_ready=0` backpressure.
- Observed deep queue and long drain map to the simulator's bridge-contention/tail-latency trend.
- Tail proxy classification: `valid`

## Notes
- This is a contract-level RTL proxy, not cycle-exact DRAM/NAND timing validation.
- Use this alongside `results/summary/tail_latency_root_cause.md` and `results/tables/key_sensitivity_panels.md`.