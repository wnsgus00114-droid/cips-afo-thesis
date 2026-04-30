# A.F.O Power/Performance/Tail Model

## 1. Per-layer Timing Model
For layer `l`,

- `T_layer(l) = max(T_compute(l), T_mem_crit(l)) + T_router(l) + T_sram_exposed(l)`
- `T_mem_crit(l) = max(T_hbm(l), T_hbf(l) + T_hbf_miss(l), T_bridge(l))`

Where:
- `T_hbm = Bytes_hbm / BW_hbm`
- `T_hbf = Bytes_hbf / BW_hbf`
- `T_bridge = Bytes_bridge_eff / BW_bridge * C_bridge * J_tail`

Bridge contention multiplier:
- `C_bridge = (1 + a * max(0, U_tenant - U_ref)) * B_burst`
- `B_burst = 1 + (traffic_burst_factor - 1) * f_burst`

Tail jitter:
- `J_tail ~ LogNormal(0, sigma_tail)`

## 2. Ring-topology Locality Adjustment
With full ring coverage constraint:
- `R_topo = 0.5 * (hbm_ring_coverage + hbf_outer_ring_coverage)`

Effective bytes/latency:
- `Bytes_bridge_eff = Bytes_bridge * (1 - gamma * max(0, R_topo - 0.8))`
- `Lat_hbf_eff = Lat_hbf * (1 - eta * max(0, R_topo - 0.8))`

## 3. HBF Miss and LHB Absorption
- `miss = max(0.01, 1 - prefetch_accuracy)`
- `miss_eff = miss * (1 - absorb_lhb)`

- `T_hbf_miss = miss_eff * (Lat_hbf_eff + 0.25*T_hbf) * (1 + beta*(C_bridge-1)) * J_tail`

## 4. SRAM Exposure Penalty
SRAM pressure:
- `P_sram = (Bytes_shared_kv + Bytes_unique_kv + rho*Bytes_weight_window) / Cap_sram`

SRAM hit approximation:
- `H_sram = clamp(prefetch_accuracy - k*max(0, P_sram - P0), H_min, H_max)`

Exposed refill penalty:
- `T_sram_exposed = (1 - H_sram) * lambda * max(T_hbm, T_bridge)`

## 5. Thermal/Process Coupling
Thermal RC update per layer:
- `Temp_{l+1} = Temp_l + G_hotspot*traffic_pressure - (Temp_l - Temp_amb)/tau_rc`
- `Temp` is clamped by `thermal_shutdown_c`

Throttle term:
- `throttle = min(throttle_max, max(0, Temp - Temp_start)*k_t)`
- `T_compute <- T_compute * (1 + throttle)`

Process corner factor:
- `process_factor ~ N(1, sigma_proc)`
- `TOPS_eff = TOPS_nominal * eff_matrix / process_factor`

## 6. Token-level Metrics
For `L` layers:
- `Lat_token = Σ_{l=1..L} T_layer(l)`
- `TPS = 1 / Lat_token`

Tail metrics:
- `p50, p90, p99, p999, max` from token latency samples
- `TailRatio = p99 / p50`

Model-vs-observed linkage:
- `Error_model(%) = |Lat_pred - Lat_meas| / Lat_meas * 100`

## 7. Power Model
- `P_total = P_compute + P_hbm + P_hbf + P_sram + P_bridge`

Approximations:
- `P_compute = P_compute_peak * Util_compute`
- `P_hbm = P_hbm_peak * Util_hbm`
- `P_hbf = P_hbf_peak * Util_hbf`
- `P_sram = P_sram_peak * H_sram`
- `P_bridge = P_bridge_peak * Util_bridge`

Energy efficiency:
- `TPW = TPS / P_total`

## 8. Outputs Used by the Paper
- Tail robustness: `latency_p99_ms`, `latency_max_ms`, `tail_ratio_p99_p50`
- Contention path: `bridge_util`, `bridge_contention_ms_total`
- Prefetch/LHB effect: `prefetch_coverage_ratio`, `lhb_hit_ratio`, `hbf_miss_penalty_ms_total`
- Cache/overlap effect: `sram_hit_ratio`, `overlap_efficiency`
- Thermal/process effect: `thermal_peak_c`, `throttling_ratio`, `process_factor`
- Causality table: bottleneck attribution percentages
