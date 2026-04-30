# Sweep Summary Tables (Synthetic, Multi-Seed)

Topology assumption: `Top=Compute (Layer1)`, `Bottom=HBM/HBF (Layer2)`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## batch_size

- Best throughput: `batch_size=16` -> `24.62` tokens/sec
- Worst throughput: `batch_size=256` -> `12.18` tokens/sec
- Worst p99 tail: `batch_size=256` -> `83.723` ms

| batch_size | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 24.62 | 41.417 | 1.020 | 98.03 | 0.760 | 0.753 | 0.020 | 0.000 | 110.78 |
| 32 | 16.49 | 61.830 | 1.020 | 97.35 | 0.745 | 0.649 | 0.027 | 0.000 | 110.78 |
| 64 | 12.70 | 80.259 | 1.020 | 95.92 | 0.732 | 0.555 | 0.041 | 0.120 | 110.78 |
| 128 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 256 | 12.18 | 83.723 | 1.020 | 84.37 | 0.728 | 0.518 | 0.159 | 0.780 | 110.78 |

## bridge_bw_gbs

- Best throughput: `bridge_bw_gbs=6400.0` -> `15.30` tokens/sec
- Worst throughput: `bridge_bw_gbs=3200.0` -> `8.37` tokens/sec
- Worst p99 tail: `bridge_bw_gbs=3200.0` -> `121.793` ms

| bridge_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3200.0 | 8.37 | 121.793 | 1.020 | 94.63 | 0.733 | 0.543 | 0.054 | 0.560 | 110.78 |
| 4000.0 | 10.45 | 97.560 | 1.020 | 93.29 | 0.732 | 0.543 | 0.068 | 0.560 | 110.78 |
| 4800.0 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 5600.0 | 14.41 | 70.510 | 1.017 | 90.75 | 0.721 | 0.543 | 0.094 | 0.560 | 110.78 |
| 6400.0 | 15.30 | 65.770 | 1.006 | 90.18 | 0.670 | 0.543 | 0.099 | 0.560 | 110.78 |

## context_len

- Best throughput: `context_len=1024` -> `12.59` tokens/sec
- Worst throughput: `context_len=16384` -> `12.28` tokens/sec
- Worst p99 tail: `context_len=16384` -> `83.066` ms

| context_len | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1024 | 12.59 | 80.997 | 1.020 | 91.92 | 0.731 | 0.547 | 0.082 | 0.482 | 110.78 |
| 2048 | 12.57 | 81.134 | 1.020 | 91.93 | 0.731 | 0.546 | 0.082 | 0.511 | 110.78 |
| 4096 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 8192 | 12.44 | 81.960 | 1.020 | 92.02 | 0.730 | 0.537 | 0.081 | 0.633 | 110.78 |
| 16384 | 12.28 | 83.066 | 1.020 | 92.12 | 0.729 | 0.525 | 0.080 | 0.725 | 110.78 |

## hbf_latency_us

- Best throughput: `hbf_latency_us=4.0` -> `12.53` tokens/sec
- Worst throughput: `hbf_latency_us=12.0` -> `12.52` tokens/sec
- Worst p99 tail: `hbf_latency_us=12.0` -> `81.424` ms

| hbf_latency_us | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4.0 | 12.53 | 81.404 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 6.0 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 8.0 | 12.52 | 81.414 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 10.0 | 12.52 | 81.419 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 12.0 | 12.52 | 81.424 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |

## kv_chunk_size_kb

- Best throughput: `kv_chunk_size_kb=64` -> `12.69` tokens/sec
- Worst throughput: `kv_chunk_size_kb=512` -> `11.61` tokens/sec
- Worst p99 tail: `kv_chunk_size_kb=512` -> `87.811` ms

| kv_chunk_size_kb | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 12.69 | 80.355 | 1.020 | 91.86 | 0.732 | 0.554 | 0.083 | 0.560 | 110.78 |
| 128 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 256 | 12.21 | 83.528 | 1.020 | 92.17 | 0.728 | 0.520 | 0.080 | 0.560 | 110.78 |
| 512 | 11.61 | 87.811 | 1.020 | 92.55 | 0.722 | 0.474 | 0.076 | 0.560 | 110.78 |

## multi_tenant_users

- Best throughput: `multi_tenant_users=32` -> `14.99` tokens/sec
- Worst throughput: `multi_tenant_users=384` -> `4.26` tokens/sec
- Worst p99 tail: `multi_tenant_users=384` -> `239.295` ms

| multi_tenant_users | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 14.99 | 67.495 | 1.012 | 91.51 | 0.875 | 0.543 | 0.086 | 0.560 | 96.11 |
| 64 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 128 | 9.03 | 112.961 | 1.020 | 94.09 | 0.527 | 0.543 | 0.060 | 0.560 | 125.00 |
| 256 | 5.78 | 176.267 | 1.020 | 96.21 | 0.338 | 0.543 | 0.039 | 0.560 | 125.00 |
| 384 | 4.26 | 239.295 | 1.020 | 97.21 | 0.249 | 0.543 | 0.028 | 0.560 | 125.00 |

## num_experts

- Best throughput: `num_experts=16` -> `12.52` tokens/sec
- Worst throughput: `num_experts=128` -> `12.52` tokens/sec
- Worst p99 tail: `num_experts=128` -> `81.410` ms

| num_experts | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 12.52 | 81.409 | 1.020 | 83.92 | 0.731 | 0.543 | 0.163 | 0.890 | 110.78 |
| 32 | 12.52 | 81.409 | 1.020 | 89.28 | 0.731 | 0.543 | 0.109 | 0.780 | 110.78 |
| 64 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 128 | 12.52 | 81.410 | 1.020 | 93.30 | 0.731 | 0.543 | 0.068 | 0.120 | 110.78 |

## prefetch_accuracy

- Best throughput: `prefetch_accuracy=0.95` -> `12.68` tokens/sec
- Worst throughput: `prefetch_accuracy=0.6` -> `11.67` tokens/sec
- Worst p99 tail: `prefetch_accuracy=0.6` -> `87.381` ms

| prefetch_accuracy | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.6 | 11.67 | 87.381 | 1.020 | 92.94 | 0.681 | 0.243 | 0.072 | 0.560 | 103.75 |
| 0.7 | 11.94 | 85.390 | 1.020 | 92.63 | 0.697 | 0.343 | 0.075 | 0.560 | 106.09 |
| 0.8 | 12.23 | 83.399 | 1.020 | 92.30 | 0.713 | 0.443 | 0.079 | 0.560 | 108.43 |
| 0.9 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 0.95 | 12.68 | 80.414 | 1.020 | 91.79 | 0.740 | 0.593 | 0.083 | 0.560 | 111.95 |

## shared_kv_ratio

- Best throughput: `shared_kv_ratio=0.85` -> `12.53` tokens/sec
- Worst throughput: `shared_kv_ratio=0.3` -> `12.52` tokens/sec
- Worst p99 tail: `shared_kv_ratio=0.3` -> `81.471` ms

| shared_kv_ratio | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.3 | 12.52 | 81.471 | 1.020 | 91.97 | 0.731 | 0.542 | 0.082 | 0.376 | 110.78 |
| 0.5 | 12.52 | 81.435 | 1.020 | 91.96 | 0.731 | 0.542 | 0.082 | 0.496 | 110.78 |
| 0.7 | 12.53 | 81.400 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.578 | 110.78 |
| 0.85 | 12.53 | 81.375 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.623 | 110.78 |

## sram_capacity_mb

- Best throughput: `sram_capacity_mb=1024.0` -> `12.78` tokens/sec
- Worst throughput: `sram_capacity_mb=256.0` -> `11.79` tokens/sec
- Worst p99 tail: `sram_capacity_mb=256.0` -> `86.483` ms

| sram_capacity_mb | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 256.0 | 11.79 | 86.483 | 1.020 | 92.43 | 0.688 | 0.200 | 0.076 | 0.560 | 110.78 |
| 384.0 | 11.79 | 86.483 | 1.020 | 92.43 | 0.688 | 0.200 | 0.076 | 0.560 | 110.78 |
| 512.0 | 12.05 | 84.623 | 1.020 | 92.27 | 0.703 | 0.326 | 0.078 | 0.560 | 110.78 |
| 768.0 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 1024.0 | 12.78 | 79.802 | 1.020 | 91.80 | 0.746 | 0.651 | 0.083 | 0.560 | 110.78 |

## traffic_burst_factor

- Best throughput: `traffic_burst_factor=1.0` -> `12.52` tokens/sec
- Worst throughput: `traffic_burst_factor=3.0` -> `10.79` tokens/sec
- Worst p99 tail: `traffic_burst_factor=3.0` -> `107.699` ms

| traffic_burst_factor | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 12.52 | 81.409 | 1.020 | 91.96 | 0.731 | 0.543 | 0.082 | 0.560 | 110.78 |
| 1.5 | 12.04 | 87.148 | 1.050 | 92.14 | 0.703 | 0.543 | 0.081 | 0.560 | 115.59 |
| 2.0 | 11.59 | 93.960 | 1.092 | 92.43 | 0.676 | 0.543 | 0.080 | 0.560 | 116.25 |
| 2.5 | 11.17 | 100.809 | 1.130 | 92.70 | 0.652 | 0.543 | 0.079 | 0.560 | 116.25 |
| 3.0 | 10.79 | 107.699 | 1.166 | 92.95 | 0.629 | 0.543 | 0.079 | 0.560 | 116.25 |
