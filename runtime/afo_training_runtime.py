#!/usr/bin/env python3
"""
A.F.O training runtime mock.
Implements training-specific SW mechanisms:
- weight prefetch window planning
- activation checkpoint/offload control
- gradient accumulation and optimizer staging
- adaptive policy tuning based on tail/stall telemetry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Dict, List

if __package__ is None or __package__ == "":
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from runtime.afo_runtime import AFORuntime, TensorDesc
else:
    from runtime.afo_runtime import AFORuntime, TensorDesc


@dataclass
class TrainingPolicy:
    micro_batch_size: int = 4
    grad_accum_steps: int = 16
    checkpoint_ratio: float = 0.6
    activation_offload_ratio: float = 0.3
    prefetch_depth: int = 2
    top_k: int = 4


@dataclass
class StepTelemetry:
    step_id: int
    prefetch_issued: int
    activation_offloaded_bytes: int
    sram_pressure: float
    predicted_tail_penalty: float
    predicted_stall_ratio: float


@dataclass
class TrainingState:
    weights: Dict[str, TensorDesc] = field(default_factory=dict)
    trainable: Dict[str, TensorDesc] = field(default_factory=dict)
    optimizer_state: Dict[str, TensorDesc] = field(default_factory=dict)
    activation_live: Dict[str, TensorDesc] = field(default_factory=dict)
    activation_offloaded: Dict[str, TensorDesc] = field(default_factory=dict)
    grad_buffers: Dict[str, TensorDesc] = field(default_factory=dict)
    step_history: List[StepTelemetry] = field(default_factory=list)


class AFOTrainingRuntime:
    def __init__(
        self,
        hbm_cap_bytes: int,
        hbf_cap_bytes: int,
        sram_cap_bytes: int,
        policy: TrainingPolicy | None = None,
    ):
        self.mem = AFORuntime(hbm_cap_bytes=hbm_cap_bytes, hbf_cap_bytes=hbf_cap_bytes, sram_cap_bytes=sram_cap_bytes)
        self.policy = policy or TrainingPolicy()
        self.state = TrainingState()

    def register_weight(self, tensor_id: str, size_bytes: int, layer_id: int) -> bool:
        t = TensorDesc(tensor_id=tensor_id, size_bytes=size_bytes, kind="weight", layer_id=layer_id)
        ok = self.mem.allocate_hbf(t)
        if ok:
            self.state.weights[tensor_id] = t
        return ok

    def register_trainable_param(self, tensor_id: str, size_bytes: int, layer_id: int, peft: bool = False) -> bool:
        kind = "adapter" if peft else "trainable_weight"
        t = TensorDesc(tensor_id=tensor_id, size_bytes=size_bytes, kind=kind, layer_id=layer_id)

        # Trainable params and grads should stay HBM-hot when possible.
        ok = self.mem.allocate_hbm(t)
        if ok:
            self.state.trainable[tensor_id] = t

            g = TensorDesc(tensor_id=f"grad::{tensor_id}", size_bytes=size_bytes, kind="grad", layer_id=layer_id)
            g_ok = self.mem.allocate_hbm(g)
            if g_ok:
                self.state.grad_buffers[g.tensor_id] = g

            # Optimizer state defaults to HBF for capacity, SRAM/HBM prefetch on demand.
            opt = TensorDesc(
                tensor_id=f"opt::{tensor_id}",
                size_bytes=size_bytes * 2,
                kind="optimizer_state",
                layer_id=layer_id,
            )
            opt_ok = self.mem.allocate_hbf(opt)
            if opt_ok:
                self.state.optimizer_state[opt.tensor_id] = opt
        return ok

    def plan_prefetch_layers(self, current_layer: int, total_layers: int) -> List[int]:
        depth = max(1, self.policy.prefetch_depth)
        layers = []
        for d in range(1, depth + 1):
            nxt = current_layer + d
            if nxt < total_layers:
                layers.append(nxt)
        return layers

    def prefetch_weight_window(self, current_layer: int, total_layers: int) -> int:
        targets = self.plan_prefetch_layers(current_layer, total_layers)
        issued = 0
        for lyr in targets:
            for tid, t in self.state.weights.items():
                if t.layer_id == lyr:
                    if self.mem.prefetch_to_sram(tensor_id=tid, layer_id=lyr):
                        issued += 1
        return issued

    def stage_activation(self, step_id: int, micro_id: int, size_bytes: int, layer_id: int) -> str:
        tid = f"act::s{step_id}::m{micro_id}::l{layer_id}"
        t = TensorDesc(tensor_id=tid, size_bytes=size_bytes, kind="activation", layer_id=layer_id)
        if self.mem.allocate_hbm(t):
            self.state.activation_live[tid] = t
        return tid

    def offload_activation(self, tid: str) -> bool:
        t = self.state.activation_live.get(tid)
        if t is None:
            return False
        off = TensorDesc(tensor_id=f"hbf::{tid}", size_bytes=t.size_bytes, kind="activation_offloaded", layer_id=t.layer_id)
        ok = self.mem.allocate_hbf(off)
        if ok:
            self.state.activation_offloaded[off.tensor_id] = off
            self.state.activation_live.pop(tid, None)
        return ok

    def run_micro_step(self, step_id: int, micro_id: int, layer_id: int, total_layers: int, act_size_bytes: int) -> StepTelemetry:
        prefetch_issued = self.prefetch_weight_window(current_layer=layer_id, total_layers=total_layers)
        act_tid = self.stage_activation(step_id=step_id, micro_id=micro_id, size_bytes=act_size_bytes, layer_id=layer_id)

        offloaded = 0
        if self.policy.activation_offload_ratio > 0.0 and (micro_id % 2 == 1):
            if self.offload_activation(act_tid):
                offloaded = act_size_bytes

        sram_used = sum(t.size_bytes for t in self.mem.state.sram_resident.values())
        sram_pressure = sram_used / max(self.mem.sram_cap, 1)

        predicted_tail_penalty = min(1.0, 0.25 * max(0.0, sram_pressure - 0.7) + 0.05 * max(0, 2 - self.policy.prefetch_depth))
        predicted_stall_ratio = min(1.0, 0.35 * max(0.0, sram_pressure - 0.6) + 0.25 * self.policy.activation_offload_ratio)

        tel = StepTelemetry(
            step_id=step_id,
            prefetch_issued=prefetch_issued,
            activation_offloaded_bytes=offloaded,
            sram_pressure=sram_pressure,
            predicted_tail_penalty=predicted_tail_penalty,
            predicted_stall_ratio=predicted_stall_ratio,
        )
        self.state.step_history.append(tel)
        return tel

    def optimizer_step(self, step_id: int) -> dict:
        # Prefetch optimizer states of trainable tensors into SRAM before update.
        prefetched = 0
        for opt_id, opt_desc in self.state.optimizer_state.items():
            if self.mem.prefetch_to_sram(opt_id, layer_id=opt_desc.layer_id):
                prefetched += 1

        # Mock gradient update accounting.
        grad_bytes = sum(t.size_bytes for t in self.state.grad_buffers.values())
        update_cost_units = grad_bytes / max(1024**2, 1)

        return {
            "step_id": step_id,
            "prefetched_optimizer_tensors": prefetched,
            "updated_grad_mb": update_cost_units,
        }

    def adapt_policy(self) -> dict:
        # Closed-loop policy tweak using last N telemetry entries.
        hist = self.state.step_history[-16:]
        if not hist:
            return {"action": "none"}

        avg_tail = sum(t.predicted_tail_penalty for t in hist) / len(hist)
        avg_stall = sum(t.predicted_stall_ratio for t in hist) / len(hist)
        avg_pressure = sum(t.sram_pressure for t in hist) / len(hist)

        action = "hold"
        if avg_tail > 0.20:
            self.policy.prefetch_depth = min(3, self.policy.prefetch_depth + 1)
            action = "increase_prefetch_depth"
        if avg_stall > 0.30 and avg_pressure > 0.85:
            self.policy.checkpoint_ratio = min(0.9, self.policy.checkpoint_ratio + 0.1)
            self.policy.activation_offload_ratio = min(0.7, self.policy.activation_offload_ratio + 0.1)
            action = "increase_checkpoint_offload"
        elif avg_stall < 0.15 and avg_pressure < 0.6:
            self.policy.activation_offload_ratio = max(0.1, self.policy.activation_offload_ratio - 0.05)
            action = "reduce_offload"

        return {
            "action": action,
            "prefetch_depth": self.policy.prefetch_depth,
            "checkpoint_ratio": self.policy.checkpoint_ratio,
            "activation_offload_ratio": self.policy.activation_offload_ratio,
        }


def demo() -> None:
    rt = AFOTrainingRuntime(
        hbm_cap_bytes=192 * 1024**3,
        hbf_cap_bytes=2048 * 1024**3,
        sram_cap_bytes=768 * 1024**2,
        policy=TrainingPolicy(micro_batch_size=4, grad_accum_steps=16),
    )

    # Register minimal layer tensors.
    for l in range(4):
        rt.register_weight(f"w::l{l}", size_bytes=128 * 1024**2, layer_id=l)
        rt.register_trainable_param(f"tw::l{l}", size_bytes=8 * 1024**2, layer_id=l, peft=False)

    for step in range(3):
        for micro in range(rt.policy.grad_accum_steps):
            layer = micro % 4
            rt.run_micro_step(step_id=step, micro_id=micro, layer_id=layer, total_layers=4, act_size_bytes=32 * 1024**2)
        print(rt.optimizer_step(step_id=step))
        print(rt.adapt_policy())


if __name__ == "__main__":
    demo()
