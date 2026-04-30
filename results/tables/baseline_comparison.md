# Baseline Comparison (Synthetic, Multi-Seed)

Topology: `Layer1=compute_top`, `Layer2=memory_bottom`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## Fairness Contract
- Same workload: `batch_size=128`, `context_len=4096`, `kv_chunk_size_kb=128`
- Same memory/interface constraints: `HBM BW=6400.0`, `HBF BW=4800.0`, `Bridge BW=4800.0`, `HBF latency=6.0us`
- Same package-neck constraints: `TSV BW=4200.0 GB/s`, `Base-die BW=5600.0 GB/s`, `TSV util cap=0.88`
- Same capacity constraints: `HBM=192.0GB`, `HBF=2048.0GB`, `SRAM=768.0MB`
- Only policy/algorithm knobs are varied per baseline (`shared_kv_ratio`, `weight_hbf_fraction`, `prefetch_accuracy`, `routing`, `LHB`, `matrix_efficiency`).

## Core Metrics
| Baseline | tokens/sec | latency_ms/token | p99_ms | tail_ratio(p99/p50) | mem_bottleneck_% | tpw |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 5.73 | 174.646 | 178.058 | 1.019 | 96.91 | 0.0810 |
| HBM_only_GPU | 5.63 | 177.651 | 181.122 | 1.019 | 96.06 | 0.0755 |
| MoSKA_only | 5.70 | 175.582 | 179.013 | 1.019 | 96.70 | 0.0698 |
| H3_only | 5.63 | 177.557 | 181.027 | 1.019 | 95.60 | 0.0893 |
| Apple_like_UMA | 5.56 | 179.917 | 183.432 | 1.019 | 96.26 | 0.0844 |
| vLLM_like | 5.70 | 175.515 | 178.945 | 1.019 | 96.73 | 0.0693 |
| FlashAttn_like | 5.68 | 176.096 | 179.537 | 1.019 | 96.92 | 0.0706 |
| TensorRTLLM_like | 5.70 | 175.291 | 178.716 | 1.019 | 96.83 | 0.0696 |

## Bottleneck Attribution
| Baseline | compute% | hbm% | hbf% | bridge% | tsv% | router% | bridge_util | tsv_util | sram_hit | overlap_eff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.334 | 0.477 | 0.613 | 0.030 |
| HBM_only_GPU | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.329 | 0.470 | 0.421 | 0.037 |
| MoSKA_only | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.332 | 0.475 | 0.543 | 0.032 |
| H3_only | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.329 | 0.470 | 0.482 | 0.042 |
| Apple_like_UMA | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.325 | 0.464 | 0.382 | 0.036 |
| vLLM_like | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.333 | 0.475 | 0.552 | 0.031 |
| FlashAttn_like | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.332 | 0.474 | 0.522 | 0.030 |
| TensorRTLLM_like | 0.00 | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.333 | 0.476 | 0.572 | 0.031 |

## Shared-KV Reuse / Prefetch Evidence
| Baseline | shared_kv_reuse_ratio | batch_gain | prefetch_coverage | lhb_hit | thermal_peak_C | model_error_% |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.642 | 2.792 | 0.970 | 0.714 | 112.42 | 23.72 |
| HBM_only_GPU | 0.000 | 1.000 | 0.721 | 0.000 | 107.96 | 24.89 |
| MoSKA_only | 0.586 | 2.413 | 0.833 | 0.714 | 110.78 | 24.10 |
| H3_only | 0.266 | 1.362 | 0.777 | 0.631 | 109.37 | 24.91 |
| Apple_like_UMA | 0.141 | 1.165 | 0.684 | 0.000 | 107.03 | 25.88 |
| vLLM_like | 0.397 | 1.658 | 0.910 | 0.714 | 111.01 | 24.04 |
| FlashAttn_like | 0.106 | 1.119 | 0.814 | 0.000 | 110.31 | 24.25 |
| TensorRTLLM_like | 0.339 | 1.514 | 0.930 | 0.714 | 111.48 | 23.93 |

Assumption note: `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines in this simulator, not measured vendor kernels.
Seed count per baseline: 5