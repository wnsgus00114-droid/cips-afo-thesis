#!/usr/bin/env python3
"""
A.F.O training simulator (full-finetune + LoRA/PEFT) for reviewer-facing experiments.
Focus:
- training-step timing and tail latency under bridge/HBM/HBF constraints
- activation checkpointing/offload behavior
- prefetch effectiveness + expert routing balance
- thermal/process slowdown coupling
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path


BYTES_FP16 = 2
BYTES_FP32 = 4


@dataclass
class AFOTrainingConfig:
    # Physical topology (fixed by A.F.O spec)
    layer1_role: str = "compute_top"
    layer2_role: str = "memory_bottom"
    hbm_ring_coverage: float = 1.0
    hbf_outer_ring_coverage: float = 1.0

    # Model
    model_size_gb: float = 180.0
    num_layers: int = 80
    hidden_dim: int = 8192
    num_experts: int = 64
    top_k: int = 4

    # Training workload
    sequence_len: int = 4096
    micro_batch_size: int = 4
    grad_accum_steps: int = 16
    data_parallel_degree: int = 1
    training_mode: str = "full_finetune"  # full_finetune | lora_sft
    lora_rank: int = 64
    route_diversity: float = 0.35
    expert_capacity_factor: float = 1.2

    # Memory policy
    activation_checkpoint_ratio: float = 0.60  # 0..1
    activation_offload_ratio: float = 0.30     # portion of stored activations offloaded to HBF
    prefetch_accuracy: float = 0.90
    weight_prefetch_depth: int = 2
    lhb_enable: int = 1
    lhb_size_mb: float = 64.0

    # HW capacities
    hbm_capacity_gb: float = 192.0
    hbf_capacity_gb: float = 2048.0
    sram_capacity_mb: float = 768.0

    # BW/latency
    hbm_bw_gbs: float = 6400.0
    hbf_bw_gbs: float = 4800.0
    bridge_bw_gbs: float = 4800.0
    hbf_latency_us: float = 6.0

    # Compute
    compute_tflops_bf16: float = 1100.0
    compute_efficiency: float = 0.68

    # Power model (training)
    p_compute_w: float = 520.0
    p_hbm_w: float = 140.0
    p_hbf_w: float = 55.0
    p_sram_w: float = 65.0
    p_bridge_w: float = 42.0

    # Stochastic + thermal/process
    random_seed: int = 42
    tail_jitter_sigma: float = 0.07
    burst_probability: float = 0.06
    traffic_burst_factor: float = 1.5
    thermal_model_enable: int = 1
    ambient_temp_c: float = 35.0
    thermal_hotspot_gain: float = 1.05
    thermal_rc_tau_steps: float = 140.0
    thermal_throttle_start_c: float = 86.0
    thermal_throttle_max: float = 0.30
    thermal_shutdown_c: float = 125.0
    process_slowdown_sigma: float = 0.035


def validate(cfg: AFOTrainingConfig) -> None:
    if cfg.layer1_role != "compute_top" or cfg.layer2_role != "memory_bottom":
        raise ValueError("A.F.O training config must use Layer1=compute_top, Layer2=memory_bottom")
    if cfg.hbm_ring_coverage < 0.8 or cfg.hbf_outer_ring_coverage < 0.8:
        raise ValueError("A.F.O ring coverage is too low for the target physical package")
    if cfg.training_mode not in {"full_finetune", "lora_sft"}:
        raise ValueError("training_mode must be full_finetune or lora_sft")


def gb_to_bytes(x: float) -> float:
    return x * (1024**3)


def mb_to_bytes(x: float) -> float:
    return x * (1024**2)


def bytes_to_gb(x: float) -> float:
    return x / (1024**3)


def sec_from_bytes(x_bytes: float, bw_gbs: float) -> float:
    if bw_gbs <= 0:
        return float("inf")
    return x_bytes / (bw_gbs * (1024**3))


def qtile(vals: list[float], q: float) -> float:
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


def safe_div(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0


def trainable_ratio(cfg: AFOTrainingConfig) -> float:
    if cfg.training_mode == "full_finetune":
        return 1.0
    # PEFT/LoRA approximation scaled by rank/hidden
    raw = 2.0 * safe_div(float(cfg.lora_rank), float(max(1, cfg.hidden_dim)))
    return max(0.001, min(0.08, raw))


def memory_footprint(cfg: AFOTrainingConfig) -> dict[str, float]:
    model_bytes = gb_to_bytes(cfg.model_size_gb)
    tr_ratio = trainable_ratio(cfg)

    trainable_bytes = model_bytes * tr_ratio
    grad_bytes = trainable_bytes * BYTES_FP16 / BYTES_FP16
    optimizer_bytes = trainable_bytes * 2.0 * BYTES_FP32 / BYTES_FP16  # m,v in fp32
    master_weight_bytes = trainable_bytes * BYTES_FP16 / BYTES_FP16

    tokens_per_micro = cfg.micro_batch_size * cfg.sequence_len
    # Activation footprint multiplier includes attention/FFN intermediates and framework buffers.
    # Kept below full worst-case tensor expansion because checkpointing/reuse cuts residency.
    act_base = tokens_per_micro * cfg.hidden_dim * cfg.num_layers * BYTES_FP16 * 4.5
    stored_factor = max(0.20, 1.0 - 0.75 * cfg.activation_checkpoint_ratio)
    act_stored = act_base * stored_factor
    act_offload = act_stored * cfg.activation_offload_ratio
    act_hbm_live = act_stored - act_offload

    # optimistic hot windows for hbm residency of optimizer/weights
    hbm_opt_hot = optimizer_bytes * 0.10
    hbm_weight_hot = model_bytes * 0.04

    hbm_resident = act_hbm_live + grad_bytes + hbm_opt_hot + hbm_weight_hot
    hbf_resident = model_bytes + optimizer_bytes + master_weight_bytes + act_offload

    return {
        "model_gb": bytes_to_gb(model_bytes),
        "trainable_ratio": tr_ratio,
        "trainable_gb": bytes_to_gb(trainable_bytes),
        "grad_gb": bytes_to_gb(grad_bytes),
        "optimizer_gb": bytes_to_gb(optimizer_bytes),
        "activation_stored_gb": bytes_to_gb(act_stored),
        "activation_offload_gb": bytes_to_gb(act_offload),
        "hbm_resident_gb": bytes_to_gb(hbm_resident),
        "hbf_resident_gb": bytes_to_gb(hbf_resident),
    }


def estimate_step_components(cfg: AFOTrainingConfig) -> dict[str, float]:
    fp = memory_footprint(cfg)

    tokens_per_micro = cfg.micro_batch_size * cfg.sequence_len
    eff_expert = 1.0 + 0.25 * safe_div(cfg.top_k, max(1, cfg.num_experts)) * cfg.num_experts * 0.02
    dense_layer_ops = 12.0 * cfg.hidden_dim * cfg.hidden_dim * tokens_per_micro
    moe_layer_ops = dense_layer_ops * 0.28 * eff_expert
    forward_ops = (dense_layer_ops + moe_layer_ops) * cfg.num_layers
    backward_ops = forward_ops * 2.1
    recompute_ops = forward_ops * (0.85 * cfg.activation_checkpoint_ratio)
    shape_penalty = (
        1.0
        + 0.10 * max(0.0, (cfg.micro_batch_size - 8) / 8.0)
        + 0.12 * max(0.0, (cfg.sequence_len - 8192) / 8192.0)
        + 0.04 * max(0.0, (8 - cfg.micro_batch_size) / 8.0)
    )
    total_ops = (forward_ops + backward_ops + recompute_ops) * cfg.grad_accum_steps * shape_penalty

    # traffic bytes per step
    model_bytes = gb_to_bytes(fp["model_gb"])
    trainable_bytes = gb_to_bytes(fp["trainable_gb"])
    act_offload_bytes = gb_to_bytes(fp["activation_offload_gb"])

    weight_stream = model_bytes * (0.18 + 0.03 * cfg.grad_accum_steps + 0.08 * (1.0 - cfg.prefetch_accuracy))
    optimizer_rw = trainable_bytes * (1.8 if cfg.training_mode == "full_finetune" else 1.1)
    act_offload_rw = act_offload_bytes * cfg.grad_accum_steps * 2.0
    grad_sync = 0.0
    if cfg.data_parallel_degree > 1:
        grad_sync = trainable_bytes * 2.0 * (cfg.data_parallel_degree - 1) / cfg.data_parallel_degree

    router_meta = tokens_per_micro * cfg.num_experts * cfg.grad_accum_steps * 2.0

    hbf_bytes = weight_stream + optimizer_rw + act_offload_rw
    hbm_bytes = grad_sync + router_meta + (trainable_bytes * 0.2)

    ring_score = 0.5 * (cfg.hbm_ring_coverage + cfg.hbf_outer_ring_coverage)
    ring_bridge_gain = max(0.90, 1.0 - 0.10 * max(0.0, ring_score - 0.8))
    bridge_bytes = (hbm_bytes + hbf_bytes) * ring_bridge_gain

    # compute and memory times (no stochastic yet)
    process_factor = max(0.85, random.Random(cfg.random_seed).gauss(1.0, cfg.process_slowdown_sigma))
    compute_tflops_eff = cfg.compute_tflops_bf16 * cfg.compute_efficiency / process_factor
    t_compute = total_ops / (compute_tflops_eff * 1e12)

    t_hbm = sec_from_bytes(hbm_bytes, cfg.hbm_bw_gbs)
    t_hbf = sec_from_bytes(hbf_bytes, cfg.hbf_bw_gbs)
    t_bridge = sec_from_bytes(bridge_bytes, cfg.bridge_bw_gbs)

    miss = max(0.01, 1.0 - cfg.prefetch_accuracy)
    lhb_absorb = 0.0
    if cfg.lhb_enable:
        lhb_absorb = min(0.85, 0.35 + 0.40 * min(1.0, cfg.lhb_size_mb / 64.0))
    miss_eff = miss * (1.0 - lhb_absorb)

    queue_depth = 1.0 + 0.015 * cfg.grad_accum_steps + 0.010 * cfg.micro_batch_size
    bridge_pressure = 1.0 + 0.35 * min(1.0, safe_div(bridge_bytes, cfg.bridge_bw_gbs * (1024**3)))
    t_hbf_miss = miss_eff * (cfg.hbf_latency_us * 1e-6 * queue_depth + 0.22 * t_hbf) * bridge_pressure

    sram_window = (
        weight_stream / max(cfg.grad_accum_steps, 1) * 0.02
        + gb_to_bytes(fp["activation_stored_gb"]) * 0.005
    )
    sram_pressure = safe_div(sram_window, mb_to_bytes(cfg.sram_capacity_mb))
    sram_hit = max(0.15, min(0.99, cfg.prefetch_accuracy - 0.45 * max(0.0, sram_pressure - 0.25)))
    t_sram_exposed = (1.0 - sram_hit) * 0.20 * max(t_hbm, t_bridge)

    overlap_eff = max(
        0.02,
        min(
            0.94,
            0.10
            + 0.55 * cfg.prefetch_accuracy
            + 0.08 * cfg.weight_prefetch_depth
            + 0.20 * sram_hit
            - 0.20 * cfg.activation_offload_ratio
            - 0.05 * (cfg.hbf_latency_us / 10.0),
        ),
    )

    critical_mem = max(t_hbm, t_hbf + t_hbf_miss, t_bridge)
    mem_exposed = critical_mem * (1.0 - overlap_eff) + t_hbf_miss + t_sram_exposed

    routing_overhead = (cfg.num_layers * cfg.grad_accum_steps) * (1.2e-6 + cfg.route_diversity * 1.0e-6)
    launch_overhead = cfg.grad_accum_steps * cfg.num_layers * 0.7e-6

    return {
        "process_factor": process_factor,
        "t_compute_s": t_compute,
        "t_hbm_s": t_hbm,
        "t_hbf_s": t_hbf,
        "t_bridge_s": t_bridge,
        "t_hbf_miss_s": t_hbf_miss,
        "t_sram_exposed_s": t_sram_exposed,
        "critical_mem_s": critical_mem,
        "overlap_efficiency": overlap_eff,
        "mem_exposed_s": mem_exposed,
        "routing_overhead_s": routing_overhead + launch_overhead,
        "hbm_bytes": hbm_bytes,
        "hbf_bytes": hbf_bytes,
        "bridge_bytes": bridge_bytes,
        "sram_hit_ratio": sram_hit,
        "lhb_hit_ratio": lhb_absorb,
    }


def run_training_simulation(cfg: AFOTrainingConfig, num_steps: int = 200) -> dict[str, float]:
    validate(cfg)
    rng = random.Random(cfg.random_seed)

    fp = memory_footprint(cfg)
    comp = estimate_step_components(cfg)

    oom_hbm = fp["hbm_resident_gb"] > cfg.hbm_capacity_gb
    oom_hbf = fp["hbf_resident_gb"] > cfg.hbf_capacity_gb

    base_step_s = comp["t_compute_s"] + comp["mem_exposed_s"] + comp["routing_overhead_s"]

    thermal_c = cfg.ambient_temp_c
    step_samples_ms: list[float] = []
    throttles: list[float] = []
    thermal_trace: list[float] = []
    burst_count = 0

    for _ in range(num_steps):
        burst_scale = 1.0
        if rng.random() < cfg.burst_probability:
            burst_count += 1
            burst_scale += (cfg.traffic_burst_factor - 1.0) * (0.5 + rng.random())

        jitter = max(0.80, rng.lognormvariate(0.0, cfg.tail_jitter_sigma))

        thermal_throttle = 0.0
        if cfg.thermal_model_enable:
            traffic_pressure = min(2.0, burst_scale * (0.8 + 0.4 * comp["overlap_efficiency"]))
            thermal_c += (
                cfg.thermal_hotspot_gain * 0.40 * traffic_pressure
                - (thermal_c - cfg.ambient_temp_c) / cfg.thermal_rc_tau_steps
            )
            thermal_c = max(cfg.ambient_temp_c, min(cfg.thermal_shutdown_c, thermal_c))
            thermal_throttle = max(0.0, thermal_c - cfg.thermal_throttle_start_c) * 0.01
            thermal_throttle = min(cfg.thermal_throttle_max, thermal_throttle)
            thermal_trace.append(thermal_c)

        step_s = base_step_s * jitter * burst_scale * (1.0 + thermal_throttle)
        step_samples_ms.append(step_s * 1000.0)
        throttles.append(thermal_throttle)

    step_mean_ms = safe_div(sum(step_samples_ms), max(len(step_samples_ms), 1))
    p50 = qtile(step_samples_ms, 0.50)
    p90 = qtile(step_samples_ms, 0.90)
    p99 = qtile(step_samples_ms, 0.99)
    p999 = qtile(step_samples_ms, 0.999)
    pmax = max(step_samples_ms) if step_samples_ms else 0.0

    tokens_per_step = cfg.micro_batch_size * cfg.sequence_len * cfg.grad_accum_steps * cfg.data_parallel_degree
    tokens_per_sec = safe_div(tokens_per_step, step_mean_ms / 1000.0)

    hbm_util = min(1.0, safe_div(comp["hbm_bytes"] / (step_mean_ms / 1000.0), cfg.hbm_bw_gbs * (1024**3)))
    hbf_util = min(1.0, safe_div(comp["hbf_bytes"] / (step_mean_ms / 1000.0), cfg.hbf_bw_gbs * (1024**3)))
    bridge_util = min(1.0, safe_div(comp["bridge_bytes"] / (step_mean_ms / 1000.0), cfg.bridge_bw_gbs * (1024**3)))

    util_compute = min(1.0, safe_div(comp["t_compute_s"], step_mean_ms / 1000.0))
    power_w = (
        cfg.p_compute_w * util_compute
        + cfg.p_hbm_w * hbm_util
        + cfg.p_hbf_w * hbf_util
        + cfg.p_sram_w * comp["sram_hit_ratio"]
        + cfg.p_bridge_w * bridge_util
    )

    tpw = safe_div(tokens_per_sec, max(power_w, 1e-9))

    requested_chunks = cfg.micro_batch_size * cfg.top_k * (1.0 + cfg.sequence_len / 8192.0)
    catalog = cfg.num_experts * (2.0 + 4.0 * cfg.route_diversity)
    unique_chunks = min(requested_chunks, catalog)
    shared_reuse = max(0.0, 1.0 - safe_div(unique_chunks, max(requested_chunks, 1e-9)))
    batch_gain = safe_div(requested_chunks, max(unique_chunks, 1e-9))

    expert_imbalance = max(
        0.0,
        0.65 * cfg.route_diversity
        + 0.30 * safe_div(cfg.top_k, max(cfg.num_experts, 1))
        - 0.25 * (cfg.expert_capacity_factor - 1.0),
    )
    expert_balance_score = max(0.0, min(1.0, 1.0 - expert_imbalance))

    tail_ratio = safe_div(p99, max(p50, 1e-9))
    tail_penalty = min(1.0, max(0.0, (tail_ratio - 1.0) / 0.60))
    thermal_penalty = min(1.0, safe_div(max(throttles) if throttles else 0.0, cfg.thermal_throttle_max))
    stall_ratio = safe_div(comp["mem_exposed_s"], max(base_step_s, 1e-9))

    train_stability = 100.0 * (
        0.30 * expert_balance_score
        + 0.25 * comp["overlap_efficiency"]
        + 0.20 * comp["sram_hit_ratio"]
        + 0.15 * (1.0 - tail_penalty)
        + 0.10 * (1.0 - thermal_penalty)
    )
    convergence_proxy = max(0.0, 1.0 - 0.55 * stall_ratio - 0.30 * tail_penalty - 0.15 * thermal_penalty)

    if oom_hbm or oom_hbf:
        train_stability *= 0.40
        convergence_proxy *= 0.35

    return {
        "training_mode": cfg.training_mode,
        "tokens_per_sec_train": tokens_per_sec,
        "step_time_ms": step_mean_ms,
        "step_p50_ms": p50,
        "step_p90_ms": p90,
        "step_p99_ms": p99,
        "step_p999_ms": p999,
        "step_max_ms": pmax,
        "tail_ratio_p99_p50": tail_ratio,
        "stall_ratio": stall_ratio,
        "hbm_util": hbm_util,
        "hbf_util": hbf_util,
        "bridge_util": bridge_util,
        "sram_hit_ratio": comp["sram_hit_ratio"],
        "lhb_hit_ratio": comp["lhb_hit_ratio"],
        "overlap_efficiency": comp["overlap_efficiency"],
        "shared_context_reuse_ratio": shared_reuse,
        "batch_gain": batch_gain,
        "expert_balance_score": expert_balance_score,
        "thermal_peak_c": max(thermal_trace) if thermal_trace else cfg.ambient_temp_c,
        "thermal_avg_c": safe_div(sum(thermal_trace), max(len(thermal_trace), 1)) if thermal_trace else cfg.ambient_temp_c,
        "thermal_throttle_ratio": max(throttles) if throttles else 0.0,
        "burst_event_ratio": safe_div(burst_count, max(num_steps, 1)),
        "power_w": power_w,
        "throughput_per_watt": tpw,
        "train_stability_score": train_stability,
        "convergence_proxy": convergence_proxy,
        "process_factor": comp["process_factor"],
        "model_hbm_resident_gb": fp["hbm_resident_gb"],
        "model_hbf_resident_gb": fp["hbf_resident_gb"],
        "trainable_ratio": fp["trainable_ratio"],
        "trainable_gb": fp["trainable_gb"],
        "optimizer_gb": fp["optimizer_gb"],
        "activation_stored_gb": fp["activation_stored_gb"],
        "activation_offload_gb": fp["activation_offload_gb"],
        "oom_hbm": int(oom_hbm),
        "oom_hbf": int(oom_hbf),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sweep(cfg: AFOTrainingConfig, param: str, values: list[float], num_steps: int) -> list[dict]:
    rows = []
    for value in values:
        cfg_local = AFOTrainingConfig(**asdict(cfg))
        current = getattr(cfg_local, param)
        setattr(cfg_local, param, type(current)(value))
        result = run_training_simulation(cfg_local, num_steps=num_steps)
        row = asdict(cfg_local)
        row.update(result)
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="A.F.O training simulator")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--num-steps", type=int, default=200)
    parser.add_argument("--out", type=str, default="results/training/training_single_run.csv")
    parser.add_argument("--sweep-param", type=str, default=None)
    parser.add_argument("--sweep-values", type=str, default=None)
    args = parser.parse_args()

    cfg = AFOTrainingConfig()
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            override = json.load(f)
        cfg = AFOTrainingConfig(**{**asdict(cfg), **override})

    validate(cfg)

    if args.sweep_param and args.sweep_values:
        vals = [float(x.strip()) for x in args.sweep_values.split(",") if x.strip()]
        rows = sweep(cfg, args.sweep_param, vals, args.num_steps)
    else:
        result = run_training_simulation(cfg, num_steps=args.num_steps)
        row = asdict(cfg)
        row.update(result)
        rows = [row]

    write_csv(Path(args.out), rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
