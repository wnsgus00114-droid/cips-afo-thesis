# Baseline Comparison (Synthetic, Multi-Seed)

Topology: `Layer1=compute_top`, `Layer2=memory_bottom`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## Fairness Contract
- Same workload: `batch_size=128`, `context_len=4096`, `kv_chunk_size_kb=128`
- Same memory/interface constraints: `HBM BW=6400.0`, `HBF BW=4800.0`, `Bridge BW=4800.0`, `HBF latency=6.0us`
- Same capacity constraints: `HBM=192.0GB`, `HBF=2048.0GB`, `SRAM=768.0MB`
- Only policy/algorithm knobs are varied per baseline (`shared_kv_ratio`, `weight_hbf_fraction`, `prefetch_accuracy`, `routing`, `LHB`, `matrix_efficiency`).

## Core Metrics
| Baseline | tokens/sec | latency_ms/token | p99_ms | tail_ratio(p99/p50) | mem_bottleneck_% | tpw |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 12.74 | 78.477 | 80.004 | 1.019 | 93.12 | 0.1216 |
| HBM_only_GPU | 12.30 | 81.330 | 82.918 | 1.019 | 91.40 | 0.0987 |
| MoSKA_only | 12.60 | 79.379 | 80.929 | 1.019 | 92.70 | 0.0946 |
| H3_only | 12.30 | 81.313 | 82.895 | 1.019 | 90.40 | 0.1288 |
| Apple_like_UMA | 11.96 | 83.643 | 85.277 | 1.019 | 91.96 | 0.1118 |
| vLLM_like | 12.62 | 79.271 | 80.818 | 1.019 | 92.77 | 0.0941 |
| FlashAttn_like | 12.53 | 79.804 | 81.362 | 1.019 | 93.19 | 0.0950 |
| TensorRTLLM_like | 12.65 | 79.027 | 80.570 | 1.019 | 92.98 | 0.0957 |

## Bottleneck Attribution
| Baseline | compute% | hbm% | hbf% | bridge% | router% | bridge_util | sram_hit | overlap_eff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.00 | 0.00 | 0.51 | 99.49 | 0.00 | 0.743 | 0.613 | 0.070 |
| HBM_only_GPU | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.718 | 0.421 | 0.087 |
| MoSKA_only | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.735 | 0.543 | 0.074 |
| H3_only | 0.00 | 0.00 | 0.55 | 99.45 | 0.00 | 0.718 | 0.482 | 0.098 |
| Apple_like_UMA | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.698 | 0.382 | 0.083 |
| vLLM_like | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.737 | 0.552 | 0.073 |
| FlashAttn_like | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.732 | 0.522 | 0.069 |
| TensorRTLLM_like | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.739 | 0.572 | 0.071 |

## Shared-KV Reuse / Prefetch Evidence
| Baseline | shared_kv_reuse_ratio | batch_gain | prefetch_coverage | lhb_hit | thermal_peak_C | model_error_% |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.642 | 2.792 | 0.970 | 0.714 | 112.42 | 25.64 |
| HBM_only_GPU | 0.000 | 1.000 | 0.721 | 0.000 | 107.96 | 28.14 |
| MoSKA_only | 0.586 | 2.413 | 0.833 | 0.714 | 110.78 | 26.47 |
| H3_only | 0.266 | 1.362 | 0.777 | 0.631 | 109.37 | 28.18 |
| Apple_like_UMA | 0.141 | 1.165 | 0.684 | 0.000 | 107.03 | 30.17 |
| vLLM_like | 0.397 | 1.658 | 0.910 | 0.714 | 111.01 | 26.34 |
| FlashAttn_like | 0.106 | 1.119 | 0.814 | 0.000 | 110.31 | 26.79 |
| TensorRTLLM_like | 0.339 | 1.514 | 0.930 | 0.714 | 111.48 | 26.10 |

Assumption note: `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines in this simulator, not measured vendor kernels.
Seed count per baseline: 5