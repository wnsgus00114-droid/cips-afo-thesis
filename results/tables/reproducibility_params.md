# Reproducibility Parameters

- Seeds: `[11, 23, 37]`
- Tokens per run: `256`

| Parameter | Value |
|---|---:|
| `hbm_bw_gbs` | `6400.0` |
| `hbf_bw_gbs` | `4800.0` |
| `bridge_bw_gbs` | `4800.0` |
| `hbf_latency_us` | `6.0` |
| `sram_capacity_mb` | `768.0` |
| `hbm_capacity_gb` | `192.0` |
| `hbf_capacity_gb` | `2048.0` |
| `compute_tops_int8` | `2200.0` |
| `matrix_efficiency` | `0.72` |
| `batch_size` | `128` |
| `context_len` | `4096` |
| `num_experts` | `64` |
| `kv_chunk_size_kb` | `128` |
| `prefetch_accuracy` | `0.9` |
| `shared_kv_ratio` | `0.65` |
| `multi_tenant_users` | `64` |
| `traffic_burst_factor` | `1.0` |
| `burst_probability` | `0.08` |
| `tail_jitter_sigma` | `0.08` |
| `thermal_hotspot_gain` | `1.0` |
| `ambient_temp_c` | `35.0` |
| `process_slowdown_sigma` | `0.03` |