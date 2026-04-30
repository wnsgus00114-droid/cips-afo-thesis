# Baseline Comparison (Synthetic, Multi-Seed)

Topology: `Layer1=compute_top`, `Layer2=memory_bottom`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## Fairness Contract
- Same workload: `batch_size=128`, `context_len=4096`, `kv_chunk_size_kb=128`
- Same memory/interface constraints: `HBM BW=6400.0`, `HBF BW=4800.0`, `Bridge BW=4800.0`, `HBF latency=6.0us`
- Same package-neck constraints: `TSV BW=4600.0 GB/s`, `Base-die BW=6000.0 GB/s`, `TSV util cap=0.9`
- Same capacity constraints: `HBM=192.0GB`, `HBF=2048.0GB`, `SRAM=768.0MB`
- Only policy/algorithm knobs are varied per baseline (`shared_kv_ratio`, `weight_hbf_fraction`, `prefetch_accuracy`, `routing`, `LHB`, `matrix_efficiency`).

## Core Metrics
| Baseline | tokens/sec | latency_ms/token | p99_ms | tail_ratio(p99/p50) | mem_bottleneck_% | tpw |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 4.16 | 240.122 | 244.814 | 1.019 | 97.75 | 0.0705 |
| HBM_only_GPU | 4.02 | 248.980 | 253.845 | 1.019 | 97.19 | 0.0688 |
| MoSKA_only | 4.11 | 243.184 | 247.936 | 1.019 | 97.62 | 0.0626 |
| H3_only | 4.05 | 247.014 | 251.841 | 1.019 | 96.84 | 0.0789 |
| Apple_like_UMA | 3.96 | 252.396 | 257.329 | 1.019 | 97.33 | 0.0769 |
| vLLM_like | 4.12 | 242.860 | 247.606 | 1.019 | 97.64 | 0.0621 |
| FlashAttn_like | 4.09 | 244.390 | 249.166 | 1.019 | 97.78 | 0.0634 |
| TensorRTLLM_like | 4.13 | 242.054 | 246.784 | 1.019 | 97.71 | 0.0621 |

## Bottleneck Attribution
| Baseline | compute% | hbm% | hbf% | bridge% | tsv% | router% | bridge_util | tsv_util | sram_hit | overlap_eff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.243 | 0.304 | 0.613 | 0.023 |
| HBM_only_GPU | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.235 | 0.294 | 0.421 | 0.028 |
| MoSKA_only | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.240 | 0.300 | 0.543 | 0.024 |
| H3_only | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.236 | 0.296 | 0.482 | 0.032 |
| Apple_like_UMA | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.231 | 0.290 | 0.382 | 0.027 |
| vLLM_like | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.240 | 0.301 | 0.552 | 0.024 |
| FlashAttn_like | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.239 | 0.299 | 0.522 | 0.022 |
| TensorRTLLM_like | 0.00 | 0.00 | 0.00 | 32.60 | 67.40 | 0.00 | 0.241 | 0.302 | 0.572 | 0.023 |

## Shared-KV Reuse / Prefetch Evidence
| Baseline | shared_kv_reuse_ratio | batch_gain | prefetch_coverage | lhb_hit | thermal_peak_C | model_error_% |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.642 | 2.792 | 0.970 | 0.714 | 112.42 | 25.93 |
| HBM_only_GPU | 0.000 | 1.000 | 0.721 | 0.000 | 107.96 | 28.46 |
| MoSKA_only | 0.586 | 2.413 | 0.833 | 0.714 | 110.78 | 26.84 |
| H3_only | 0.266 | 1.362 | 0.777 | 0.631 | 109.37 | 27.94 |
| Apple_like_UMA | 0.141 | 1.165 | 0.684 | 0.000 | 107.03 | 29.46 |
| vLLM_like | 0.397 | 1.658 | 0.910 | 0.714 | 111.01 | 26.71 |
| FlashAttn_like | 0.106 | 1.119 | 0.814 | 0.000 | 110.31 | 27.14 |
| TensorRTLLM_like | 0.339 | 1.514 | 0.930 | 0.714 | 111.48 | 26.46 |

Assumption note: `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines in this simulator, not measured vendor kernels.
Seed count per baseline: 5