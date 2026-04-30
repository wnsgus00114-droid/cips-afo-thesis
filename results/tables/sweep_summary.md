# Sweep Summary Tables (Synthetic, Multi-Seed)

Topology assumption: `Top=Compute (Layer1)`, `Bottom=HBM/HBF (Layer2)`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## base_die_xbar_bw_gbs

- Best throughput: `base_die_xbar_bw_gbs=6800.0` -> `6.13` tokens/sec
- Worst throughput: `base_die_xbar_bw_gbs=4200.0` -> `4.99` tokens/sec
- Worst p99 tail: `base_die_xbar_bw_gbs=4200.0` -> `204.322` ms

| base_die_xbar_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4200.0 | 4.99 | 204.322 | 1.020 | 96.80 | 0.291 | 0.416 | 0.543 | 0.031 | 0.560 | 110.78 |
| 5000.0 | 5.41 | 188.421 | 1.020 | 96.53 | 0.316 | 0.451 | 0.543 | 0.033 | 0.560 | 110.78 |
| 5600.0 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 6200.0 | 5.92 | 172.263 | 1.020 | 96.20 | 0.345 | 0.493 | 0.543 | 0.037 | 0.560 | 110.78 |
| 6800.0 | 6.13 | 166.323 | 1.020 | 96.07 | 0.358 | 0.511 | 0.543 | 0.038 | 0.560 | 110.78 |

## batch_size

- Best throughput: `batch_size=16` -> `10.93` tokens/sec
- Worst throughput: `batch_size=256` -> `5.54` tokens/sec
- Worst p99 tail: `batch_size=256` -> `184.133` ms

| batch_size | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 10.93 | 93.278 | 1.020 | 99.12 | 0.337 | 0.482 | 0.753 | 0.009 | 0.000 | 110.78 |
| 32 | 7.40 | 137.760 | 1.020 | 98.81 | 0.334 | 0.478 | 0.649 | 0.012 | 0.000 | 110.78 |
| 64 | 5.76 | 177.155 | 1.020 | 98.15 | 0.332 | 0.474 | 0.555 | 0.018 | 0.120 | 110.78 |
| 128 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 256 | 5.54 | 184.133 | 1.020 | 92.89 | 0.331 | 0.473 | 0.518 | 0.068 | 0.780 | 110.78 |

## bridge_bw_gbs

- Best throughput: `bridge_bw_gbs=6400.0` -> `5.74` tokens/sec
- Worst throughput: `bridge_bw_gbs=3200.0` -> `5.58` tokens/sec
- Worst p99 tail: `bridge_bw_gbs=3200.0` -> `182.860` ms

| bridge_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3200.0 | 5.58 | 182.860 | 1.020 | 96.42 | 0.488 | 0.465 | 0.543 | 0.035 | 0.560 | 110.78 |
| 4000.0 | 5.64 | 180.830 | 1.020 | 96.38 | 0.395 | 0.470 | 0.543 | 0.035 | 0.560 | 110.78 |
| 4800.0 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 5600.0 | 5.71 | 178.509 | 1.020 | 96.33 | 0.286 | 0.476 | 0.543 | 0.035 | 0.560 | 110.78 |
| 6400.0 | 5.74 | 177.784 | 1.020 | 96.32 | 0.251 | 0.478 | 0.543 | 0.035 | 0.560 | 110.78 |

## context_len

- Best throughput: `context_len=1024` -> `5.71` tokens/sec
- Worst throughput: `context_len=16384` -> `5.58` tokens/sec
- Worst p99 tail: `context_len=16384` -> `182.813` ms

| context_len | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1024 | 5.71 | 178.644 | 1.020 | 96.34 | 0.332 | 0.474 | 0.547 | 0.035 | 0.482 | 110.78 |
| 2048 | 5.70 | 178.921 | 1.020 | 96.34 | 0.332 | 0.474 | 0.546 | 0.035 | 0.511 | 110.78 |
| 4096 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 8192 | 5.65 | 180.587 | 1.020 | 96.38 | 0.331 | 0.473 | 0.537 | 0.035 | 0.633 | 110.78 |
| 16384 | 5.58 | 182.813 | 1.020 | 96.42 | 0.331 | 0.473 | 0.525 | 0.034 | 0.725 | 110.78 |

## hbf_latency_us

- Best throughput: `hbf_latency_us=4.0` -> `5.68` tokens/sec
- Worst throughput: `hbf_latency_us=12.0` -> `5.68` tokens/sec
- Worst p99 tail: `hbf_latency_us=12.0` -> `179.491` ms

| hbf_latency_us | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4.0 | 5.68 | 179.471 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 6.0 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 8.0 | 5.68 | 179.481 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 10.0 | 5.68 | 179.486 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 12.0 | 5.68 | 179.491 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |

## kv_chunk_size_kb

- Best throughput: `kv_chunk_size_kb=64` -> `5.75` tokens/sec
- Worst throughput: `kv_chunk_size_kb=512` -> `5.30` tokens/sec
- Worst p99 tail: `kv_chunk_size_kb=512` -> `192.314` ms

| kv_chunk_size_kb | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 5.75 | 177.350 | 1.020 | 96.31 | 0.332 | 0.474 | 0.554 | 0.036 | 0.560 | 110.78 |
| 128 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 256 | 5.55 | 183.741 | 1.020 | 96.44 | 0.331 | 0.473 | 0.520 | 0.034 | 0.560 | 110.78 |
| 512 | 5.30 | 192.314 | 1.020 | 96.60 | 0.330 | 0.471 | 0.474 | 0.033 | 0.560 | 110.78 |

## multi_tenant_users

- Best throughput: `multi_tenant_users=32` -> `6.74` tokens/sec
- Worst throughput: `multi_tenant_users=384` -> `2.21` tokens/sec
- Worst p99 tail: `multi_tenant_users=384` -> `461.169` ms

| multi_tenant_users | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 6.74 | 151.342 | 1.020 | 96.19 | 0.393 | 0.562 | 0.543 | 0.037 | 0.560 | 96.11 |
| 64 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 128 | 4.32 | 235.793 | 1.020 | 97.17 | 0.252 | 0.361 | 0.543 | 0.027 | 0.560 | 125.00 |
| 256 | 2.92 | 348.620 | 1.020 | 98.08 | 0.171 | 0.244 | 0.543 | 0.019 | 0.560 | 125.00 |
| 384 | 2.21 | 461.169 | 1.020 | 98.55 | 0.129 | 0.184 | 0.543 | 0.014 | 0.560 | 125.00 |

## num_experts

- Best throughput: `num_experts=16` -> `5.68` tokens/sec
- Worst throughput: `num_experts=128` -> `5.68` tokens/sec
- Worst p99 tail: `num_experts=128` -> `179.478` ms

| num_experts | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 5.68 | 179.475 | 1.020 | 92.71 | 0.332 | 0.474 | 0.543 | 0.070 | 0.890 | 110.78 |
| 32 | 5.68 | 179.476 | 1.020 | 95.14 | 0.332 | 0.474 | 0.543 | 0.047 | 0.780 | 110.78 |
| 64 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 128 | 5.68 | 179.478 | 1.020 | 96.96 | 0.332 | 0.474 | 0.543 | 0.029 | 0.120 | 110.78 |

## prefetch_accuracy

- Best throughput: `prefetch_accuracy=0.95` -> `5.71` tokens/sec
- Worst throughput: `prefetch_accuracy=0.6` -> `5.50` tokens/sec
- Worst p99 tail: `prefetch_accuracy=0.6` -> `185.442` ms

| prefetch_accuracy | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.6 | 5.50 | 185.442 | 1.020 | 96.67 | 0.321 | 0.458 | 0.243 | 0.031 | 0.560 | 103.75 |
| 0.7 | 5.56 | 183.453 | 1.020 | 96.57 | 0.324 | 0.463 | 0.343 | 0.032 | 0.560 | 106.09 |
| 0.8 | 5.62 | 181.465 | 1.020 | 96.46 | 0.328 | 0.468 | 0.443 | 0.034 | 0.560 | 108.43 |
| 0.9 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 0.95 | 5.71 | 178.482 | 1.020 | 96.30 | 0.333 | 0.476 | 0.593 | 0.036 | 0.560 | 111.95 |

## shared_kv_ratio

- Best throughput: `shared_kv_ratio=0.85` -> `5.68` tokens/sec
- Worst throughput: `shared_kv_ratio=0.3` -> `5.68` tokens/sec
- Worst p99 tail: `shared_kv_ratio=0.3` -> `179.606` ms

| shared_kv_ratio | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.3 | 5.68 | 179.606 | 1.020 | 96.36 | 0.332 | 0.474 | 0.542 | 0.035 | 0.376 | 110.78 |
| 0.5 | 5.68 | 179.532 | 1.020 | 96.35 | 0.332 | 0.474 | 0.542 | 0.035 | 0.496 | 110.78 |
| 0.7 | 5.68 | 179.458 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.578 | 110.78 |
| 0.85 | 5.68 | 179.402 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.623 | 110.78 |

## sram_capacity_mb

- Best throughput: `sram_capacity_mb=1024.0` -> `5.73` tokens/sec
- Worst throughput: `sram_capacity_mb=256.0` -> `5.53` tokens/sec
- Worst p99 tail: `sram_capacity_mb=256.0` -> `184.550` ms

| sram_capacity_mb | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 256.0 | 5.53 | 184.550 | 1.020 | 96.45 | 0.322 | 0.461 | 0.200 | 0.033 | 0.560 | 110.78 |
| 384.0 | 5.53 | 184.550 | 1.020 | 96.45 | 0.322 | 0.461 | 0.200 | 0.033 | 0.560 | 110.78 |
| 512.0 | 5.58 | 182.690 | 1.020 | 96.42 | 0.326 | 0.465 | 0.326 | 0.034 | 0.560 | 110.78 |
| 768.0 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 1024.0 | 5.73 | 177.870 | 1.020 | 96.32 | 0.335 | 0.478 | 0.651 | 0.036 | 0.560 | 110.78 |

## traffic_burst_factor

- Best throughput: `traffic_burst_factor=1.0` -> `5.68` tokens/sec
- Worst throughput: `traffic_burst_factor=3.0` -> `5.23` tokens/sec
- Worst p99 tail: `traffic_burst_factor=3.0` -> `209.359` ms

| traffic_burst_factor | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 1.5 | 5.56 | 185.517 | 1.032 | 96.37 | 0.325 | 0.464 | 0.543 | 0.035 | 0.560 | 115.59 |
| 2.0 | 5.45 | 193.265 | 1.053 | 96.44 | 0.318 | 0.454 | 0.543 | 0.035 | 0.560 | 116.25 |
| 2.5 | 5.33 | 201.350 | 1.076 | 96.51 | 0.311 | 0.445 | 0.543 | 0.035 | 0.560 | 116.25 |
| 3.0 | 5.23 | 209.359 | 1.097 | 96.58 | 0.305 | 0.436 | 0.543 | 0.034 | 0.560 | 116.25 |

## tsv_uplink_bw_gbs

- Best throughput: `tsv_uplink_bw_gbs=5800.0` -> `6.68` tokens/sec
- Worst throughput: `tsv_uplink_bw_gbs=2800.0` -> `4.47` tokens/sec
- Worst p99 tail: `tsv_uplink_bw_gbs=2800.0` -> `228.247` ms

| tsv_uplink_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2800.0 | 4.47 | 228.247 | 1.020 | 97.13 | 0.261 | 0.559 | 0.543 | 0.027 | 0.560 | 110.78 |
| 3600.0 | 5.21 | 195.733 | 1.020 | 96.66 | 0.304 | 0.507 | 0.543 | 0.032 | 0.560 | 110.78 |
| 4200.0 | 5.68 | 179.476 | 1.020 | 96.35 | 0.332 | 0.474 | 0.543 | 0.035 | 0.560 | 110.78 |
| 5000.0 | 6.22 | 163.870 | 1.020 | 96.01 | 0.363 | 0.436 | 0.543 | 0.039 | 0.560 | 110.78 |
| 5800.0 | 6.68 | 152.568 | 1.020 | 95.71 | 0.390 | 0.403 | 0.543 | 0.042 | 0.560 | 110.78 |
