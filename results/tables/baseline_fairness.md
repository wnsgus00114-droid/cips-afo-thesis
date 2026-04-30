# Baseline Fairness Contract

This table discloses which variables are fixed and which variables are intentionally changed.

## Fixed Constraints (Identical Across Baselines)
| Field | Value |
|---|---:|
| `layer1_role` | `compute_top` |
| `layer2_role` | `memory_bottom` |
| `hbm_ring_coverage` | `1.0` |
| `hbf_outer_ring_coverage` | `1.0` |
| `batch_size` | `128` |
| `context_len` | `4096` |
| `kv_chunk_size_kb` | `128` |
| `num_layers` | `80` |
| `hidden_dim` | `8192` |
| `num_experts` | `64` |
| `top_k` | `4` |
| `hbm_capacity_gb` | `192.0` |
| `hbf_capacity_gb` | `2048.0` |
| `sram_capacity_mb` | `768.0` |
| `hbm_bw_gbs` | `6400.0` |
| `hbf_bw_gbs` | `4800.0` |
| `bridge_bw_gbs` | `4800.0` |
| `hbf_latency_us` | `6.0` |
| `multi_tenant_users` | `64` |
| `traffic_burst_factor` | `1.0` |
| `burst_probability` | `0.08` |
| `tail_jitter_sigma` | `0.08` |
| `thermal_model_enable` | `1` |
| `ambient_temp_c` | `35.0` |
| `thermal_hotspot_gain` | `1.0` |
| `thermal_throttle_start_c` | `88.0` |
| `thermal_throttle_max` | `0.25` |
| `thermal_shutdown_c` | `125.0` |
| `process_slowdown_sigma` | `0.03` |

## Variable Knobs by Baseline
| Baseline | shared_kv_ratio | weight_hbf_fraction | prefetch_accuracy | matrix_eff | routing_div | lhb_enable | lhb_size_mb | prefetch_depth |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.75 | 1.00 | 0.97 | 0.86 | 0.25 | 1 | 96.0 | 2 |
| HBM_only_GPU | 0.00 | 0.00 | 0.78 | 0.64 | 0.58 | 0 | 32.0 | 1 |
| MoSKA_only | 0.62 | 0.00 | 0.90 | 0.79 | 0.28 | 1 | 64.0 | 1 |
| H3_only | 0.35 | 1.00 | 0.84 | 0.58 | 0.56 | 1 | 48.0 | 1 |
| Apple_like_UMA | 0.25 | 0.40 | 0.74 | 0.66 | 0.60 | 0 | 32.0 | 1 |
| vLLM_like | 0.40 | 0.00 | 0.91 | 0.80 | 0.42 | 1 | 72.0 | 2 |
| FlashAttn_like | 0.15 | 0.00 | 0.88 | 0.84 | 0.50 | 0 | 32.0 | 1 |
| TensorRTLLM_like | 0.30 | 0.10 | 0.93 | 0.83 | 0.40 | 1 | 80.0 | 2 |

## Policy-Level Baseline Note
- `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` do not represent vendor-measured kernels.
- They represent policy families under the same simulator constraints for fair directional comparison.