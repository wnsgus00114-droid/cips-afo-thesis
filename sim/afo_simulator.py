#!/usr/bin/env python3
"""
A.F.O analytical simulator (MoSKA + H3).
- Models HBM/HBF/bridge/SRAM constraints
- Models Active Base Die lateral route + central TSV neck constraints
- Approximates token decode throughput, stall, utilization, power
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass, asdict
from pathlib import Path


BYTES_PER_FP16 = 2


@dataclass
class AFOConfig:
    # Physical package convention (fixed by A.F.O spec)
    layer1_role: str = "compute_top"
    layer2_role: str = "memory_bottom"
    package_topology: str = "active_base_3p5d"
    compute_bonding: str = "hybrid_3d_tsv"
    memory_ring_mount: str = "periphery_2p5d_microbump"
    # Layer-2 rectangular ring topology:
    # inner HBM ring fully surrounds Layer-1 compute footprint,
    # and outer HBF ring surrounds HBM ring.
    hbm_ring_coverage: float = 1.0
    hbf_outer_ring_coverage: float = 1.0

    # Package feasibility controls (Active Base Die + TSV neck)
    base_die_xbar_bw_gbs: float = 5600.0
    tsv_uplink_bw_gbs: float = 4200.0
    tsv_protocol_overhead: float = 0.10
    tsv_lane_util_limit: float = 0.88
    periphery_to_center_hops: int = 6
    base_die_hop_latency_ns: float = 2.5
    microbump_latency_ns: float = 8.0

    # Geometric sanity checks for packaging narrative
    hbm_stack_height_mm: float = 0.72
    compute_die_thickness_mm: float = 0.12
    periphery_ring_clearance_mm: float = 2.0

    model_size_gb: float = 180.0
    num_layers: int = 80
    hidden_dim: int = 8192
    num_experts: int = 64
    top_k: int = 4
    batch_size: int = 128
    context_len: int = 4096
    kv_chunk_size_kb: int = 128
    shared_kv_ratio: float = 0.65
    weight_hbf_fraction: float = 1.0
    moe_layer_ratio: float = 0.5
    routing_diversity: float = 0.35
    prefetch_accuracy: float = 0.90

    hbm_capacity_gb: float = 192.0
    hbf_capacity_gb: float = 2048.0
    sram_capacity_mb: float = 768.0

    hbm_bw_gbs: float = 6400.0
    hbf_bw_gbs: float = 4800.0
    bridge_bw_gbs: float = 4800.0
    hbf_latency_us: float = 6.0

    compute_tops_int8: float = 2200.0
    matrix_efficiency: float = 0.72
    freq_ghz: float = 1.5

    p_compute_w: float = 420.0
    p_hbm_w: float = 120.0
    p_hbf_w: float = 45.0
    p_sram_w: float = 55.0
    p_bridge_w: float = 35.0

    # Tail-latency / traffic contention controls
    random_seed: int = 42
    multi_tenant_users: int = 64
    traffic_burst_factor: float = 1.0
    burst_probability: float = 0.08
    tail_jitter_sigma: float = 0.08

    # LHB / prefetch controls
    lhb_enable: int = 1
    lhb_size_mb: float = 64.0
    prefetch_depth: int = 1

    # Thermal / process variability
    thermal_model_enable: int = 1
    ambient_temp_c: float = 35.0
    thermal_hotspot_gain: float = 1.0
    thermal_rc_tau_layers: float = 180.0
    thermal_throttle_start_c: float = 88.0
    thermal_throttle_max: float = 0.25
    thermal_shutdown_c: float = 125.0
    process_slowdown_sigma: float = 0.03


def validate_layer_convention(cfg: AFOConfig) -> None:
    if cfg.layer1_role != "compute_top" or cfg.layer2_role != "memory_bottom":
        raise ValueError(
            "A.F.O layer convention mismatch: required layer1_role=compute_top and "
            "layer2_role=memory_bottom (Layer 1 top=Compute, Layer 2 bottom=HBM/HBF memory)."
        )
    if cfg.hbm_ring_coverage < 0.8 or cfg.hbf_outer_ring_coverage < 0.8:
        raise ValueError(
            "A.F.O ring topology mismatch: Layer-2 must use near-full rectangular rings "
            "(HBM inner ring around compute, HBF outer ring around HBM)."
        )


def validate_package_feasibility(cfg: AFOConfig) -> None:
    if cfg.package_topology != "active_base_3p5d":
        raise ValueError(
            "A.F.O package topology mismatch: expected package_topology=active_base_3p5d "
            "(Active Base Die + central 3D bonding + periphery 2.5D memory ring)."
        )
    if cfg.compute_bonding != "hybrid_3d_tsv":
        raise ValueError(
            "A.F.O compute bonding mismatch: expected compute_bonding=hybrid_3d_tsv."
        )
    if cfg.memory_ring_mount != "periphery_2p5d_microbump":
        raise ValueError(
            "A.F.O memory mount mismatch: expected memory_ring_mount=periphery_2p5d_microbump."
        )
    if cfg.hbm_stack_height_mm <= cfg.compute_die_thickness_mm:
        raise ValueError(
            "A.F.O package geometry mismatch: HBM stack must be taller than compute die; "
            "this model assumes periphery mounting on active base die."
        )
    if cfg.periphery_ring_clearance_mm < 0.5:
        raise ValueError(
            "A.F.O package clearance mismatch: periphery ring clearance must be >= 0.5mm."
        )
    if cfg.base_die_xbar_bw_gbs <= 0 or cfg.tsv_uplink_bw_gbs <= 0:
        raise ValueError("A.F.O package bandwidth mismatch: base_die_xbar_bw_gbs and tsv_uplink_bw_gbs must be positive.")
    if not (0.5 <= cfg.tsv_lane_util_limit <= 1.0):
        raise ValueError("A.F.O package mismatch: tsv_lane_util_limit must be in [0.5, 1.0].")


def gb_to_bytes(x: float) -> float:
    return x * (1024**3)


def mb_to_bytes(x: float) -> float:
    return x * (1024**2)


def kb_to_bytes(x: float) -> float:
    return x * 1024


def bytes_to_gb(x: float) -> float:
    return x / (1024**3)


def calc_active_expert_fraction(cfg: AFOConfig) -> float:
    # Batch routing diversity raises active expert spread
    active = (cfg.top_k * cfg.batch_size * cfg.routing_diversity) / max(cfg.num_experts, 1)
    return min(1.0, max(active, cfg.top_k / max(cfg.num_experts, 1)))


def calc_memory_footprint(cfg: AFOConfig) -> dict:
    model_bytes = gb_to_bytes(cfg.model_size_gb)
    dense_weights = model_bytes * 0.45
    expert_weights = model_bytes * 0.55

    runtime_kv_bytes = (
        cfg.batch_size * cfg.context_len * cfg.hidden_dim * 2 * BYTES_PER_FP16
    )

    shared_kv_bytes = runtime_kv_bytes * (cfg.shared_kv_ratio * 0.8)

    return {
        "dense_weights_gb": bytes_to_gb(dense_weights),
        "expert_weights_gb": bytes_to_gb(expert_weights),
        "runtime_kv_gb": bytes_to_gb(runtime_kv_bytes),
        "shared_kv_gb": bytes_to_gb(shared_kv_bytes),
    }


def estimate_layer_bytes(cfg: AFOConfig) -> dict:
    fp = calc_memory_footprint(cfg)
    dense_layer_bytes = gb_to_bytes(fp["dense_weights_gb"]) / cfg.num_layers

    moe_layers = max(1, int(cfg.num_layers * cfg.moe_layer_ratio))
    full_expert_layer_bytes = gb_to_bytes(fp["expert_weights_gb"]) / moe_layers

    active_expert_fraction = calc_active_expert_fraction(cfg)
    expert_layer_bytes = full_expert_layer_bytes * active_expert_fraction

    kv_chunk_bytes = kb_to_bytes(cfg.kv_chunk_size_kb)
    context_chunk_factor = 1.0 + (cfg.context_len / 8192.0) * 0.5
    chunks_per_layer = cfg.batch_size * cfg.top_k * context_chunk_factor
    shared_kv_fetch = kv_chunk_bytes * chunks_per_layer

    # Decode attention cost grows with context; shared-KV coverage reduces unique fetch pressure.
    context_factor = 1.0 + (cfg.context_len / 2048.0)
    unique_reduction = max(0.25, 1.0 - 0.6 * cfg.shared_kv_ratio)
    unique_kv_fetch = (
        cfg.batch_size
        * cfg.hidden_dim
        * 2
        * BYTES_PER_FP16
        * context_factor
        * unique_reduction
    )

    metadata_bytes = cfg.batch_size * cfg.num_experts * 4

    return {
        "dense_layer_bytes": dense_layer_bytes,
        "expert_layer_bytes": expert_layer_bytes,
        "shared_kv_fetch_bytes": shared_kv_fetch,
        "unique_kv_fetch_bytes": unique_kv_fetch,
        "metadata_bytes": metadata_bytes,
    }


def estimate_layer_ops(cfg: AFOConfig) -> float:
    # Approximate per-layer token ops for decode
    base = 8.0 * cfg.hidden_dim * cfg.hidden_dim
    moe_factor = 1.0 + (cfg.top_k / max(cfg.num_experts, 1)) * 8.0
    return base * moe_factor * cfg.batch_size


def sec_from_bytes(x_bytes: float, bw_gbs: float) -> float:
    if bw_gbs <= 0:
        return float("inf")
    return x_bytes / (bw_gbs * (1024**3))


def _quantile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def _safe_div(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0


def run_simulation(cfg: AFOConfig, num_tokens: int = 64) -> dict:
    validate_layer_convention(cfg)
    validate_package_feasibility(cfg)
    layer_bytes = estimate_layer_bytes(cfg)
    layer_ops = estimate_layer_ops(cfg)

    rng = random.Random(cfg.random_seed)
    process_factor = max(0.85, rng.gauss(1.0, cfg.process_slowdown_sigma))
    compute_tops_eff = cfg.compute_tops_int8 * cfg.matrix_efficiency / process_factor
    compute_ops_per_sec = compute_tops_eff * 1e12

    total_time_s = 0.0
    total_stall_s = 0.0
    total_hbm_bytes = 0.0
    total_hbf_bytes = 0.0
    total_bridge_bytes = 0.0
    total_tsv_bytes = 0.0
    total_base_route_bytes = 0.0
    sram_hit_acc = 0.0
    lhb_hit_acc = 0.0
    overlap_acc = 0.0
    prefetch_cov_num = 0.0
    prefetch_cov_den = 0.0
    hbf_miss_penalty_s_total = 0.0
    bridge_contention_s_total = 0.0
    tsv_contention_s_total = 0.0
    base_route_contention_s_total = 0.0
    burst_events = 0

    # Per-token latency samples for tail analysis
    token_latency_ms_samples: list[float] = []
    token_stall_ms_samples: list[float] = []
    thermal_trace: list[float] = []

    # Bottleneck attribution buckets
    b_compute = 0.0
    b_hbm = 0.0
    b_hbf = 0.0
    b_bridge = 0.0
    b_tsv = 0.0
    b_router = 0.0

    miss_rate = max(0.01, 1.0 - cfg.prefetch_accuracy)
    active_expert_fraction = calc_active_expert_fraction(cfg)
    # Ring coverage improves effective access locality and reduces exposed miss penalty.
    ring_score = 0.5 * (cfg.hbm_ring_coverage + cfg.hbf_outer_ring_coverage)
    ring_bridge_gain = max(0.92, 1.0 - 0.10 * max(0.0, ring_score - 0.8))
    ring_hbf_latency_gain = max(0.75, 1.0 - 0.35 * max(0.0, ring_score - 0.8))

    # Active Base Die path: periphery memory ring -> base-die lateral route -> central TSV neck -> compute die
    tsv_effective_bw_gbs = cfg.tsv_uplink_bw_gbs * max(0.5, min(1.0, cfg.tsv_lane_util_limit))
    base_hops = max(1, cfg.periphery_to_center_hops)
    pkg_const_latency_s = (
        cfg.base_die_hop_latency_ns * base_hops + cfg.microbump_latency_ns
    ) * 1e-9

    # Shared-KV reuse and batch gain approximation
    context_chunk_factor = 1.0 + (cfg.context_len / 8192.0) * 0.5
    requested_chunks = cfg.batch_size * cfg.top_k * context_chunk_factor * (
        0.35 + 0.65 * cfg.shared_kv_ratio
    )
    chunk_catalog_size = max(1.0, cfg.num_experts * (2.0 + 4.0 * cfg.routing_diversity))
    unique_chunks = min(requested_chunks, chunk_catalog_size)
    shared_kv_reuse_ratio = max(0.0, 1.0 - _safe_div(unique_chunks, requested_chunks))
    batch_gain = _safe_div(requested_chunks, max(unique_chunks, 1.0))

    thermal_c = cfg.ambient_temp_c

    for _tok in range(num_tokens):
        token_time_s = 0.0
        token_stall_s = 0.0
        for _layer in range(cfg.num_layers):
            hbf_bytes = layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"]
            hbf_bytes *= cfg.weight_hbf_fraction
            hbf_bytes += layer_bytes["shared_kv_fetch_bytes"] * cfg.shared_kv_ratio

            hbm_bytes = layer_bytes["unique_kv_fetch_bytes"]
            hbm_bytes += (
                (layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"])
                * (1.0 - cfg.weight_hbf_fraction)
            )
            hbm_bytes += layer_bytes["shared_kv_fetch_bytes"] * (1.0 - cfg.shared_kv_ratio)
            hbm_bytes += layer_bytes["metadata_bytes"]

            burst_mult = 1.0
            if rng.random() < cfg.burst_probability:
                burst_events += 1
                burst_mult += max(0.0, cfg.traffic_burst_factor - 1.0) * (0.5 + rng.random())
            jitter = max(0.7, rng.lognormvariate(0.0, cfg.tail_jitter_sigma))

            bridge_bytes = (hbf_bytes + hbm_bytes) * ring_bridge_gain
            bridge_contention = 1.0 + 0.0075 * max(0, cfg.multi_tenant_users - 32)
            bridge_contention *= burst_mult

            # Active Base Die lateral route + central TSV neck contention.
            base_route_bytes = bridge_bytes
            tsv_bytes = bridge_bytes * (1.0 + max(0.0, cfg.tsv_protocol_overhead))
            base_route_scale = 1.0 + 0.035 * max(0, base_hops - 1)
            tsv_contention = 1.0 + 0.0045 * max(0, cfg.multi_tenant_users - 32)
            tsv_contention *= (1.0 + 0.15 * max(0.0, burst_mult - 1.0))

            t_hbf = sec_from_bytes(hbf_bytes, cfg.hbf_bw_gbs)
            t_hbm = sec_from_bytes(hbm_bytes, cfg.hbm_bw_gbs)
            t_bridge = sec_from_bytes(bridge_bytes, cfg.bridge_bw_gbs) * bridge_contention * jitter
            t_base_route_nominal = sec_from_bytes(base_route_bytes, cfg.base_die_xbar_bw_gbs) * base_route_scale
            t_base_route = t_base_route_nominal * bridge_contention * jitter
            t_tsv_nominal = sec_from_bytes(tsv_bytes, tsv_effective_bw_gbs)
            t_tsv = t_tsv_nominal * tsv_contention * jitter
            t_pkg_path = t_base_route + t_tsv + pkg_const_latency_s
            t_ring_to_compute = t_bridge + t_pkg_path
            t_compute = layer_ops / compute_ops_per_sec

            lhb_absorb = 0.0
            if cfg.lhb_enable:
                lhb_absorb = min(0.85, 0.40 + 0.35 * min(1.0, cfg.lhb_size_mb / 64.0))
                # under extreme contention, LHB absorption effectiveness degrades
                lhb_absorb *= max(0.65, 1.0 - 0.20 * max(0.0, bridge_contention - 1.0))
            effective_miss_rate = miss_rate * (1.0 - lhb_absorb)

            hbf_miss_penalty = effective_miss_rate * (
                cfg.hbf_latency_us * 1e-6 * ring_hbf_latency_gain + 0.25 * t_hbf
            ) * (1.0 + 0.60 * max(0.0, bridge_contention - 1.0)) * jitter

            # Thermal throttling: high traffic raises temperature and reduces effective compute speed
            if cfg.thermal_model_enable:
                traffic_pressure = min(1.8, _safe_div(bridge_contention, 1.0) * (0.7 + 0.3 * cfg.prefetch_accuracy))
                thermal_c += (
                    (cfg.thermal_hotspot_gain * 0.35 * traffic_pressure)
                    - _safe_div((thermal_c - cfg.ambient_temp_c), cfg.thermal_rc_tau_layers)
                )
                thermal_c = max(cfg.ambient_temp_c, min(cfg.thermal_shutdown_c, thermal_c))
                throttle = max(0.0, thermal_c - cfg.thermal_throttle_start_c)
                throttle = min(cfg.thermal_throttle_max, throttle * 0.01)
                t_compute *= (1.0 + throttle)
                thermal_trace.append(thermal_c)

            critical_mem = max(t_hbm, t_hbf + hbf_miss_penalty, t_ring_to_compute)
            overlap_time = max(t_compute, critical_mem) + hbf_miss_penalty

            sram_pressure = (
                layer_bytes["shared_kv_fetch_bytes"]
                + layer_bytes["unique_kv_fetch_bytes"]
                + 0.40 * (layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"])
            ) / max(mb_to_bytes(cfg.sram_capacity_mb), 1.0)
            sram_hit = max(0.2, min(0.99, cfg.prefetch_accuracy - 0.22 * max(0.0, sram_pressure - 0.35)))
            # Exposed refill penalty when SRAM staging is under-provisioned.
            sram_exposed_penalty = (1.0 - sram_hit) * 0.20 * max(t_hbm, t_ring_to_compute)

            # Routing and queueing overhead
            routing_overhead = (0.5e-6 + active_expert_fraction * 1.0e-6) * (1.0 + 0.12 * max(0.0, burst_mult - 1.0))
            stall = max(0.0, critical_mem - t_compute) + routing_overhead + hbf_miss_penalty + sram_exposed_penalty

            layer_time = overlap_time + routing_overhead + sram_exposed_penalty

            total_time_s += layer_time
            total_stall_s += stall
            total_hbm_bytes += hbm_bytes
            total_hbf_bytes += hbf_bytes
            total_bridge_bytes += bridge_bytes
            total_tsv_bytes += tsv_bytes
            total_base_route_bytes += base_route_bytes
            token_time_s += layer_time
            token_stall_s += stall
            hbf_miss_penalty_s_total += hbf_miss_penalty
            bridge_contention_s_total += max(0.0, t_bridge - sec_from_bytes(bridge_bytes, cfg.bridge_bw_gbs))
            tsv_contention_s_total += max(0.0, t_tsv - t_tsv_nominal)
            base_route_contention_s_total += max(0.0, t_base_route - t_base_route_nominal)

            sram_hit_acc += sram_hit
            lhb_hit_acc += lhb_absorb

            exposed_wait = max(0.0, critical_mem - t_compute)
            overlap = 1.0 - _safe_div(exposed_wait, max(critical_mem, 1e-12))
            overlap *= (0.82 + 0.18 * sram_hit)
            overlap_acc += max(0.0, min(1.0, overlap))

            prefetch_cov_num += cfg.prefetch_accuracy * (0.85 + 0.15 * min(1.0, cfg.prefetch_depth / 2.0))
            prefetch_cov_den += 1.0

            dominant_bucket = max(
                {
                    "compute": t_compute,
                    "hbm": t_hbm,
                    "hbf": t_hbf + hbf_miss_penalty,
                    "ring_path": t_ring_to_compute,
                    "router": routing_overhead,
                }.items(),
                key=lambda kv: kv[1],
            )[0]

            if dominant_bucket == "compute":
                b_compute += layer_time
            elif dominant_bucket == "hbm":
                b_hbm += layer_time
            elif dominant_bucket == "hbf":
                b_hbf += layer_time
            elif dominant_bucket == "ring_path":
                ring_denom = max(t_ring_to_compute, 1e-12)
                b_bridge += layer_time * _safe_div(t_bridge, ring_denom)
                b_tsv += layer_time * _safe_div(t_pkg_path, ring_denom)
            else:
                b_router += layer_time

        token_latency_ms_samples.append(token_time_s * 1000.0)
        token_stall_ms_samples.append(token_stall_s * 1000.0)

    token_per_sec = num_tokens / total_time_s if total_time_s > 0 else 0.0
    avg_sram_hit = sram_hit_acc / (num_tokens * cfg.num_layers)
    avg_lhb_hit = lhb_hit_acc / max(1, (num_tokens * cfg.num_layers))
    overlap_efficiency = overlap_acc / max(1, (num_tokens * cfg.num_layers))
    prefetch_coverage_ratio = _safe_div(prefetch_cov_num, prefetch_cov_den)

    hbm_util = min(1.0, (total_hbm_bytes / total_time_s) / (cfg.hbm_bw_gbs * (1024**3)))
    hbf_util = min(1.0, (total_hbf_bytes / total_time_s) / (cfg.hbf_bw_gbs * (1024**3)))
    bridge_util = min(1.0, (total_bridge_bytes / total_time_s) / (cfg.bridge_bw_gbs * (1024**3)))
    tsv_util = min(1.0, (total_tsv_bytes / total_time_s) / (tsv_effective_bw_gbs * (1024**3)))
    base_die_util = min(1.0, (total_base_route_bytes / total_time_s) / (cfg.base_die_xbar_bw_gbs * (1024**3)))
    bridge_domain_util = max(bridge_util, tsv_util, base_die_util)

    total_power = (
        cfg.p_compute_w * min(1.0, token_per_sec / 500.0)
        + cfg.p_hbm_w * hbm_util
        + cfg.p_hbf_w * hbf_util
        + cfg.p_sram_w * avg_sram_hit
        + cfg.p_bridge_w * bridge_domain_util
    )
    perf_per_watt = token_per_sec / max(total_power, 1e-6)

    footprint = calc_memory_footprint(cfg)
    oom_hbm = footprint["runtime_kv_gb"] > cfg.hbm_capacity_gb
    oom_hbf = (footprint["dense_weights_gb"] + footprint["expert_weights_gb"] + footprint["shared_kv_gb"]) > cfg.hbf_capacity_gb

    mem_bottleneck_pct = 100.0 * min(1.0, total_stall_s / max(total_time_s, 1e-9))

    p50 = _quantile(token_latency_ms_samples, 0.50)
    p90 = _quantile(token_latency_ms_samples, 0.90)
    p99 = _quantile(token_latency_ms_samples, 0.99)
    p999 = _quantile(token_latency_ms_samples, 0.999)
    pmax = max(token_latency_ms_samples) if token_latency_ms_samples else 0.0

    predicted_layer_s = max(
        layer_ops / compute_ops_per_sec,
        sec_from_bytes(layer_bytes["unique_kv_fetch_bytes"] + layer_bytes["metadata_bytes"], cfg.hbm_bw_gbs),
        sec_from_bytes(layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"], cfg.hbf_bw_gbs)
        + miss_rate * (cfg.hbf_latency_us * 1e-6),
        sec_from_bytes(layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"] + layer_bytes["unique_kv_fetch_bytes"], cfg.bridge_bw_gbs)
        + sec_from_bytes(layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"] + layer_bytes["unique_kv_fetch_bytes"], cfg.base_die_xbar_bw_gbs)
        + sec_from_bytes(
            (layer_bytes["dense_layer_bytes"] + layer_bytes["expert_layer_bytes"] + layer_bytes["unique_kv_fetch_bytes"])
            * (1.0 + max(0.0, cfg.tsv_protocol_overhead)),
            tsv_effective_bw_gbs,
        )
        + pkg_const_latency_s,
    ) + (0.5e-6 + active_expert_fraction * 1.0e-6)
    predicted_token_ms = predicted_layer_s * cfg.num_layers * 1000.0
    measured_token_ms = _safe_div(sum(token_latency_ms_samples), max(len(token_latency_ms_samples), 1))
    model_error_pct = 100.0 * abs(predicted_token_ms - measured_token_ms) / max(measured_token_ms, 1e-9)

    bottleneck_total = b_compute + b_hbm + b_hbf + b_bridge + b_tsv + b_router
    thermal_peak = max(thermal_trace) if thermal_trace else cfg.ambient_temp_c
    thermal_avg = _safe_div(sum(thermal_trace), max(len(thermal_trace), 1)) if thermal_trace else cfg.ambient_temp_c
    throttling_ratio = max(0.0, min(1.0, (thermal_peak - cfg.thermal_throttle_start_c) / 20.0))

    return {
        "tokens_per_sec": token_per_sec,
        "latency_ms_per_token": (1.0 / token_per_sec) * 1000.0 if token_per_sec > 0 else float("inf"),
        "latency_p50_ms": p50,
        "latency_p90_ms": p90,
        "latency_p99_ms": p99,
        "latency_p999_ms": p999,
        "latency_max_ms": pmax,
        "tail_ratio_p99_p50": _safe_div(p99, max(p50, 1e-9)),
        "stall_cycles_ratio": total_stall_s / max(total_time_s, 1e-9),
        "mem_bottleneck_pct": mem_bottleneck_pct,
        "sram_hit_ratio": avg_sram_hit,
        "lhb_hit_ratio": avg_lhb_hit,
        "overlap_efficiency": overlap_efficiency,
        "prefetch_coverage_ratio": prefetch_coverage_ratio,
        "hbm_util": hbm_util,
        "hbf_util": hbf_util,
        "bridge_util": bridge_util,
        "tsv_util": tsv_util,
        "base_die_util": base_die_util,
        "bridge_contention_ms_total": bridge_contention_s_total * 1000.0,
        "tsv_contention_ms_total": tsv_contention_s_total * 1000.0,
        "base_route_contention_ms_total": base_route_contention_s_total * 1000.0,
        "hbf_miss_penalty_ms_total": hbf_miss_penalty_s_total * 1000.0,
        "burst_event_count": burst_events,
        "burst_event_ratio": _safe_div(burst_events, max(1, (num_tokens * cfg.num_layers))),
        "throughput_per_watt": perf_per_watt,
        "power_w": total_power,
        "total_hbm_gb_transferred": bytes_to_gb(total_hbm_bytes),
        "total_hbf_gb_transferred": bytes_to_gb(total_hbf_bytes),
        "shared_kv_reuse_ratio": shared_kv_reuse_ratio,
        "batch_gain": batch_gain,
        "bottleneck_compute_pct": 100.0 * _safe_div(b_compute, max(bottleneck_total, 1e-9)),
        "bottleneck_hbm_pct": 100.0 * _safe_div(b_hbm, max(bottleneck_total, 1e-9)),
        "bottleneck_hbf_pct": 100.0 * _safe_div(b_hbf, max(bottleneck_total, 1e-9)),
        "bottleneck_bridge_pct": 100.0 * _safe_div(b_bridge, max(bottleneck_total, 1e-9)),
        "bottleneck_tsv_pct": 100.0 * _safe_div(b_tsv, max(bottleneck_total, 1e-9)),
        "bottleneck_router_pct": 100.0 * _safe_div(b_router, max(bottleneck_total, 1e-9)),
        "thermal_peak_c": thermal_peak,
        "thermal_avg_c": thermal_avg,
        "throttling_ratio": throttling_ratio,
        "process_factor": process_factor,
        "model_predicted_token_ms": predicted_token_ms,
        "model_measured_token_ms": measured_token_ms,
        "model_error_pct": model_error_pct,
        "oom_hbm": int(oom_hbm),
        "oom_hbf": int(oom_hbf),
        "runtime_kv_gb": footprint["runtime_kv_gb"],
        "shared_kv_gb": footprint["shared_kv_gb"],
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sweep(cfg: AFOConfig, sweep_param: str, values: list[float], num_tokens: int) -> list[dict]:
    rows = []
    for v in values:
        cfg_local = AFOConfig(**asdict(cfg))
        setattr(cfg_local, sweep_param, type(getattr(cfg, sweep_param))(v))
        result = run_simulation(cfg_local, num_tokens=num_tokens)
        row = asdict(cfg_local)
        row.update(result)
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="A.F.O analytical simulator")
    parser.add_argument("--config", type=str, default=None, help="JSON config file")
    parser.add_argument("--num-tokens", type=int, default=64)
    parser.add_argument("--out", type=str, default="results/sim/afo_single_run.csv")
    parser.add_argument("--sweep-param", type=str, default=None)
    parser.add_argument("--sweep-values", type=str, default=None, help="comma separated")
    args = parser.parse_args()

    cfg = AFOConfig()
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            override = json.load(f)
        cfg = AFOConfig(**{**asdict(cfg), **override})
    validate_layer_convention(cfg)

    if args.sweep_param and args.sweep_values:
        values = [float(x.strip()) for x in args.sweep_values.split(",") if x.strip()]
        rows = sweep(cfg, args.sweep_param, values, args.num_tokens)
    else:
        result = run_simulation(cfg, num_tokens=args.num_tokens)
        row = asdict(cfg)
        row.update(result)
        rows = [row]

    write_csv(Path(args.out), rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
