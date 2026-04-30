#!/usr/bin/env python3
"""
A.F.O runtime mock for memory placement + token scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class TensorDesc:
    tensor_id: str
    size_bytes: int
    kind: str
    layer_id: int = -1


@dataclass
class RuntimeState:
    hbm_alloc: Dict[str, TensorDesc] = field(default_factory=dict)
    hbf_alloc: Dict[str, TensorDesc] = field(default_factory=dict)
    sram_resident: Dict[str, TensorDesc] = field(default_factory=dict)
    kv_chunks_hot: Dict[str, int] = field(default_factory=dict)


class AFORuntime:
    def __init__(self, hbm_cap_bytes: int, hbf_cap_bytes: int, sram_cap_bytes: int):
        self.state = RuntimeState()
        self.hbm_cap = hbm_cap_bytes
        self.hbf_cap = hbf_cap_bytes
        self.sram_cap = sram_cap_bytes

    def _used(self, pool: Dict[str, TensorDesc]) -> int:
        return sum(t.size_bytes for t in pool.values())

    def allocate_hbm(self, tensor: TensorDesc) -> bool:
        if self._used(self.state.hbm_alloc) + tensor.size_bytes > self.hbm_cap:
            return False
        self.state.hbm_alloc[tensor.tensor_id] = tensor
        return True

    def allocate_hbf(self, tensor: TensorDesc) -> bool:
        if self._used(self.state.hbf_alloc) + tensor.size_bytes > self.hbf_cap:
            return False
        self.state.hbf_alloc[tensor.tensor_id] = tensor
        return True

    def prefetch_to_sram(self, tensor_id: str, layer_id: int) -> bool:
        t = self.state.hbm_alloc.get(tensor_id) or self.state.hbf_alloc.get(tensor_id)
        if t is None:
            return False
        staged = TensorDesc(tensor_id=t.tensor_id, size_bytes=t.size_bytes, kind=t.kind, layer_id=layer_id)
        if self._used(self.state.sram_resident) + staged.size_bytes > self.sram_cap:
            return False
        self.state.sram_resident[tensor_id] = staged
        return True

    def route_kv_chunks(self, query_embedding, top_k: int) -> List[str]:
        # Placeholder for ANN/MoE router integration.
        del query_embedding
        return [f"kv_chunk_{i}" for i in range(top_k)]

    def execute_shared_kv_attention(self, batch_queries, kv_chunks: List[str]) -> Dict[str, float]:
        del batch_queries
        for cid in kv_chunks:
            self.state.kv_chunks_hot[cid] = self.state.kv_chunks_hot.get(cid, 0) + 1
        return {"mode": "shared_gemm", "chunks": float(len(kv_chunks))}

    def execute_unique_attention(self, query, runtime_kv) -> Dict[str, float]:
        del query, runtime_kv
        return {"mode": "unique_gemv", "cost_units": 1.0}

    def evict_kv_chunk(self, chunk_id: str) -> bool:
        if chunk_id in self.state.sram_resident:
            del self.state.sram_resident[chunk_id]
            return True
        return False

    def token_step(self, request_ids: List[str], layer_id: int, top_k: int = 4) -> Dict[str, object]:
        routed: Dict[str, List[str]] = {}
        for rid in request_ids:
            routed[rid] = self.route_kv_chunks(query_embedding=rid, top_k=top_k)

        unique_stats = []
        shared_chunks = sorted({c for chunks in routed.values() for c in chunks})
        shared_stats = self.execute_shared_kv_attention(request_ids, shared_chunks)

        for rid in request_ids:
            unique_stats.append(self.execute_unique_attention(query=rid, runtime_kv=f"runtime_kv_{rid}"))

        return {
            "layer_id": layer_id,
            "num_requests": len(request_ids),
            "shared_chunks": shared_chunks,
            "shared_stats": shared_stats,
            "unique_stats": unique_stats,
        }


def demo() -> None:
    rt = AFORuntime(hbm_cap_bytes=192 * 1024**3, hbf_cap_bytes=2048 * 1024**3, sram_cap_bytes=768 * 1024**2)
    rt.allocate_hbf(TensorDesc("dense_w_l0", 256 * 1024**2, "weight", layer_id=0))
    rt.allocate_hbm(TensorDesc("runtime_kv_req0", 16 * 1024**2, "runtime_kv", layer_id=0))
    rt.prefetch_to_sram("dense_w_l0", layer_id=0)
    print(rt.token_step(["req0", "req1", "req2"], layer_id=0, top_k=4))


if __name__ == "__main__":
    demo()
