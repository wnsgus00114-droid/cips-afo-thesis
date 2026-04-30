# Sweep Summary Tables (Synthetic, Multi-Seed)

Topology assumption: `Top=Compute (Layer1)`, `Bottom=HBM/HBF (Layer2)`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## base_die_xbar_bw_gbs

- Best throughput: `base_die_xbar_bw_gbs=6800.0` -> `4.25` tokens/sec
- Worst throughput: `base_die_xbar_bw_gbs=4200.0` -> `3.64` tokens/sec
- Worst p99 tail: `base_die_xbar_bw_gbs=4200.0` -> `279.961` ms

| base_die_xbar_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4200.0 | 3.64 | 279.961 | 1.020 | 97.66 | 0.213 | 0.266 | 0.543 | 0.024 | 0.560 | 110.78 |
| 5000.0 | 3.88 | 263.123 | 1.020 | 97.51 | 0.226 | 0.283 | 0.543 | 0.025 | 0.560 | 110.78 |
| 5600.0 | 4.02 | 253.651 | 1.020 | 97.42 | 0.235 | 0.294 | 0.543 | 0.026 | 0.560 | 110.78 |
| 6200.0 | 4.14 | 246.013 | 1.020 | 97.34 | 0.242 | 0.303 | 0.543 | 0.027 | 0.560 | 110.78 |
| 6800.0 | 4.25 | 239.722 | 1.020 | 97.27 | 0.248 | 0.311 | 0.543 | 0.028 | 0.560 | 110.78 |

## batch_size

- Best throughput: `batch_size=16` -> `8.07` tokens/sec
- Worst throughput: `batch_size=256` -> `3.99` tokens/sec
- Worst p99 tail: `batch_size=256` -> `255.475` ms

| batch_size | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 8.07 | 126.313 | 1.020 | 99.35 | 0.249 | 0.312 | 0.753 | 0.007 | 0.000 | 110.78 |
| 32 | 5.41 | 188.608 | 1.020 | 99.13 | 0.244 | 0.306 | 0.649 | 0.009 | 0.000 | 110.78 |
| 64 | 4.16 | 244.867 | 1.020 | 98.66 | 0.240 | 0.301 | 0.555 | 0.014 | 0.120 | 110.78 |
| 128 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 256 | 3.99 | 255.475 | 1.020 | 94.88 | 0.238 | 0.299 | 0.518 | 0.052 | 0.780 | 110.78 |

## bridge_bw_gbs

- Best throughput: `bridge_bw_gbs=6400.0` -> `4.47` tokens/sec
- Worst throughput: `bridge_bw_gbs=3200.0` -> `3.53` tokens/sec
- Worst p99 tail: `bridge_bw_gbs=3200.0` -> `288.777` ms

| bridge_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3200.0 | 3.53 | 288.777 | 1.020 | 97.73 | 0.309 | 0.258 | 0.543 | 0.023 | 0.560 | 110.78 |
| 4000.0 | 3.85 | 264.544 | 1.020 | 97.53 | 0.270 | 0.282 | 0.543 | 0.025 | 0.560 | 110.78 |
| 4800.0 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 5600.0 | 4.31 | 236.850 | 1.020 | 97.24 | 0.215 | 0.315 | 0.543 | 0.028 | 0.560 | 110.78 |
| 6400.0 | 4.47 | 228.195 | 1.020 | 97.13 | 0.196 | 0.327 | 0.543 | 0.029 | 0.560 | 110.78 |

## context_len

- Best throughput: `context_len=1024` -> `4.13` tokens/sec
- Worst throughput: `context_len=16384` -> `4.02` tokens/sec
- Worst p99 tail: `context_len=16384` -> `253.464` ms

| context_len | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1024 | 4.13 | 247.125 | 1.020 | 97.35 | 0.240 | 0.300 | 0.547 | 0.027 | 0.482 | 110.78 |
| 2048 | 4.12 | 247.546 | 1.020 | 97.36 | 0.240 | 0.300 | 0.546 | 0.027 | 0.511 | 110.78 |
| 4096 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 8192 | 4.08 | 250.078 | 1.020 | 97.38 | 0.239 | 0.300 | 0.537 | 0.026 | 0.633 | 110.78 |
| 16384 | 4.02 | 253.464 | 1.020 | 97.42 | 0.239 | 0.299 | 0.525 | 0.026 | 0.725 | 110.78 |

## hbf_latency_us

- Best throughput: `hbf_latency_us=4.0` -> `4.11` tokens/sec
- Worst throughput: `hbf_latency_us=12.0` -> `4.11` tokens/sec
- Worst p99 tail: `hbf_latency_us=12.0` -> `248.404` ms

| hbf_latency_us | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4.0 | 4.11 | 248.384 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 6.0 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 8.0 | 4.11 | 248.394 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 10.0 | 4.11 | 248.399 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 12.0 | 4.11 | 248.404 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |

## kv_chunk_size_kb

- Best throughput: `kv_chunk_size_kb=64` -> `4.16` tokens/sec
- Worst throughput: `kv_chunk_size_kb=512` -> `3.81` tokens/sec
- Worst p99 tail: `kv_chunk_size_kb=512` -> `267.989` ms

| kv_chunk_size_kb | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 4.16 | 245.162 | 1.020 | 97.33 | 0.240 | 0.301 | 0.554 | 0.027 | 0.560 | 110.78 |
| 128 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 256 | 4.00 | 254.877 | 1.020 | 97.43 | 0.239 | 0.299 | 0.520 | 0.026 | 0.560 | 110.78 |
| 512 | 3.81 | 267.989 | 1.020 | 97.56 | 0.237 | 0.296 | 0.474 | 0.025 | 0.560 | 110.78 |

## multi_tenant_users

- Best throughput: `multi_tenant_users=32` -> `4.93` tokens/sec
- Worst throughput: `multi_tenant_users=384` -> `1.53` tokens/sec
- Worst p99 tail: `multi_tenant_users=384` -> `666.322` ms

| multi_tenant_users | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 4.93 | 206.631 | 1.020 | 97.21 | 0.288 | 0.361 | 0.543 | 0.028 | 0.560 | 96.11 |
| 64 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 128 | 3.07 | 331.954 | 1.020 | 97.99 | 0.179 | 0.224 | 0.543 | 0.020 | 0.560 | 125.00 |
| 256 | 2.04 | 499.277 | 1.020 | 98.66 | 0.119 | 0.149 | 0.543 | 0.014 | 0.560 | 125.00 |
| 384 | 1.53 | 666.322 | 1.020 | 99.00 | 0.089 | 0.112 | 0.543 | 0.010 | 0.560 | 125.00 |

## num_experts

- Best throughput: `num_experts=16` -> `4.11` tokens/sec
- Worst throughput: `num_experts=128` -> `4.11` tokens/sec
- Worst p99 tail: `num_experts=128` -> `248.391` ms

| num_experts | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 4.11 | 248.388 | 1.020 | 94.73 | 0.240 | 0.300 | 0.543 | 0.053 | 0.890 | 110.78 |
| 32 | 4.11 | 248.388 | 1.020 | 96.49 | 0.240 | 0.300 | 0.543 | 0.036 | 0.780 | 110.78 |
| 64 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 128 | 4.11 | 248.391 | 1.020 | 97.80 | 0.240 | 0.300 | 0.543 | 0.022 | 0.120 | 110.78 |

## prefetch_accuracy

- Best throughput: `prefetch_accuracy=0.95` -> `4.15` tokens/sec
- Worst throughput: `prefetch_accuracy=0.6` -> `3.87` tokens/sec
- Worst p99 tail: `prefetch_accuracy=0.6` -> `263.534` ms

| prefetch_accuracy | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.6 | 3.87 | 263.534 | 1.020 | 97.66 | 0.226 | 0.283 | 0.243 | 0.024 | 0.560 | 103.75 |
| 0.7 | 3.94 | 258.486 | 1.020 | 97.56 | 0.230 | 0.288 | 0.343 | 0.025 | 0.560 | 106.09 |
| 0.8 | 4.02 | 253.438 | 1.020 | 97.47 | 0.235 | 0.294 | 0.443 | 0.026 | 0.560 | 108.43 |
| 0.9 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 0.95 | 4.15 | 245.865 | 1.020 | 97.31 | 0.242 | 0.303 | 0.593 | 0.027 | 0.560 | 111.95 |

## shared_kv_ratio

- Best throughput: `shared_kv_ratio=0.85` -> `4.11` tokens/sec
- Worst throughput: `shared_kv_ratio=0.3` -> `4.10` tokens/sec
- Worst p99 tail: `shared_kv_ratio=0.3` -> `248.589` ms

| shared_kv_ratio | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.3 | 4.10 | 248.589 | 1.020 | 97.37 | 0.240 | 0.300 | 0.542 | 0.027 | 0.376 | 110.78 |
| 0.5 | 4.10 | 248.475 | 1.020 | 97.37 | 0.240 | 0.300 | 0.542 | 0.027 | 0.496 | 110.78 |
| 0.7 | 4.11 | 248.361 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.578 | 110.78 |
| 0.85 | 4.11 | 248.275 | 1.020 | 97.36 | 0.240 | 0.300 | 0.543 | 0.027 | 0.623 | 110.78 |

## sram_capacity_mb

- Best throughput: `sram_capacity_mb=1024.0` -> `4.19` tokens/sec
- Worst throughput: `sram_capacity_mb=256.0` -> `3.86` tokens/sec
- Worst p99 tail: `sram_capacity_mb=256.0` -> `263.952` ms

| sram_capacity_mb | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 256.0 | 3.86 | 263.952 | 1.020 | 97.52 | 0.225 | 0.282 | 0.200 | 0.025 | 0.560 | 110.78 |
| 384.0 | 3.86 | 263.952 | 1.020 | 97.52 | 0.225 | 0.282 | 0.200 | 0.025 | 0.560 | 110.78 |
| 512.0 | 3.95 | 258.246 | 1.020 | 97.47 | 0.230 | 0.289 | 0.326 | 0.025 | 0.560 | 110.78 |
| 768.0 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 1024.0 | 4.19 | 243.461 | 1.020 | 97.31 | 0.244 | 0.306 | 0.651 | 0.027 | 0.560 | 110.78 |

## traffic_burst_factor

- Best throughput: `traffic_burst_factor=1.0` -> `4.11` tokens/sec
- Worst throughput: `traffic_burst_factor=3.0` -> `3.70` tokens/sec
- Worst p99 tail: `traffic_burst_factor=3.0` -> `301.631` ms

| traffic_burst_factor | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 4.11 | 248.389 | 1.020 | 97.37 | 0.240 | 0.300 | 0.543 | 0.027 | 0.560 | 110.78 |
| 1.5 | 4.00 | 259.373 | 1.037 | 97.39 | 0.233 | 0.292 | 0.543 | 0.027 | 0.560 | 115.59 |
| 2.0 | 3.89 | 273.331 | 1.065 | 97.46 | 0.227 | 0.284 | 0.543 | 0.026 | 0.560 | 116.25 |
| 2.5 | 3.79 | 287.459 | 1.093 | 97.52 | 0.221 | 0.277 | 0.543 | 0.026 | 0.560 | 116.25 |
| 3.0 | 3.70 | 301.631 | 1.119 | 97.58 | 0.216 | 0.270 | 0.543 | 0.026 | 0.560 | 116.25 |

## tsv_uplink_bw_gbs

- Best throughput: `tsv_uplink_bw_gbs=5800.0` -> `4.45` tokens/sec
- Worst throughput: `tsv_uplink_bw_gbs=2800.0` -> `3.31` tokens/sec
- Worst p99 tail: `tsv_uplink_bw_gbs=2800.0` -> `308.378` ms

| tsv_uplink_bw_gbs | tokens/sec | p99_ms | tail_ratio | mem_bottleneck_% | bridge_util | tsv_util | sram_hit | overlap_eff | kv_reuse | thermal_peak_C |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2800.0 | 3.31 | 308.378 | 1.020 | 97.88 | 0.193 | 0.397 | 0.543 | 0.021 | 0.560 | 110.78 |
| 3600.0 | 3.72 | 274.310 | 1.020 | 97.61 | 0.217 | 0.347 | 0.543 | 0.024 | 0.560 | 110.78 |
| 4200.0 | 3.96 | 257.276 | 1.020 | 97.46 | 0.231 | 0.317 | 0.543 | 0.026 | 0.560 | 110.78 |
| 5000.0 | 4.23 | 240.924 | 1.020 | 97.28 | 0.247 | 0.285 | 0.543 | 0.027 | 0.560 | 110.78 |
| 5800.0 | 4.45 | 229.083 | 1.020 | 97.14 | 0.260 | 0.258 | 0.543 | 0.029 | 0.560 | 110.78 |
