# Reproducibility Parameters

- Seeds: `[11, 23, 37]`
- Tokens per run: `256`

| Parameter | Value |
|---|---:|
| `package_topology` | `active_base_3p5d` |
| `compute_bonding` | `hybrid_3d_tsv` |
| `memory_ring_mount` | `periphery_2p5d_microbump` |
| `base_die_xbar_bw_gbs` | `5600.0` |
| `tsv_uplink_bw_gbs` | `4200.0` |
| `tsv_protocol_overhead` | `0.1` |
| `tsv_lane_util_limit` | `0.88` |
| `periphery_to_center_hops` | `6` |
| `base_die_hop_latency_ns` | `2.5` |
| `microbump_latency_ns` | `8.0` |
| `hbm_stack_height_mm` | `0.72` |
| `compute_die_thickness_mm` | `0.12` |
| `periphery_ring_clearance_mm` | `2.0` |
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