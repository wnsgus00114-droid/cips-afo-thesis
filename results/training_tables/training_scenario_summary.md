# A.F.O Training Scenario Summary

| scenario | mode | tok/s | step_ms | p99_ms | tail_ratio | stability | convergence | bridge_util | thermal_peak_C | oom_hbm | oom_hbf |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full_ft_nominal | full_finetune | 2370.71 | 110889.14 | 170290.52 | 1.571 | 28.60 | 0.255 | 0.002 | 74.06 | 1 | 0 |
| full_ft_longctx | full_finetune | 2008.22 | 392715.25 | 603085.97 | 1.571 | 27.51 | 0.255 | 0.001 | 73.20 | 1 | 0 |
| full_ft_thermal_hot | full_finetune | 2121.55 | 123864.80 | 259107.55 | 2.324 | 26.39 | 0.223 | 0.002 | 98.31 | 1 | 0 |
| lora_nominal | lora_sft | 2507.07 | 209715.96 | 322057.11 | 1.571 | 66.78 | 0.728 | 0.001 | 73.75 | 0 | 0 |
| lora_throughput | lora_sft | 2303.34 | 256798.88 | 394361.53 | 1.571 | 65.83 | 0.728 | 0.001 | 73.73 | 0 | 0 |
| lora_worst_tail | lora_sft | 1504.68 | 3161348.48 | 8754839.06 | 3.747 | 21.42 | 0.243 | 0.001 | 87.33 | 1 | 0 |