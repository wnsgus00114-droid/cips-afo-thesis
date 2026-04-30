# Baseline Comparison (Synthetic, Multi-Seed)

Topology: `Layer1=compute_top`, `Layer2=memory_bottom`, `HBM inner ring=1.0`, `HBF outer ring=1.0`.

## Core Metrics
| Baseline | tokens/sec | latency_ms/token | p99_ms | tail_ratio(p99/p50) | mem_bottleneck_% | tpw |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 14.68 | 68.103 | 69.235 | 1.017 | 92.08 | 0.1318 |
| HBM_only_GPU | 10.62 | 94.120 | 95.958 | 1.019 | 91.33 | 0.0930 |
| MoSKA_only | 11.81 | 84.662 | 86.315 | 1.019 | 93.15 | 0.0920 |
| H3_only | 9.77 | 102.398 | 104.398 | 1.019 | 92.38 | 0.1128 |
| Apple_like_UMA | 10.00 | 99.970 | 101.922 | 1.019 | 93.27 | 0.1031 |
| vLLM_like | 12.35 | 80.954 | 82.535 | 1.019 | 92.92 | 0.0932 |
| FlashAttn_like | 11.49 | 87.042 | 88.741 | 1.019 | 93.76 | 0.0915 |
| TensorRTLLM_like | 12.92 | 77.418 | 78.929 | 1.019 | 92.83 | 0.0965 |

## Bottleneck Attribution
| Baseline | compute% | hbm% | hbf% | bridge% | router% | bridge_util | sram_hit | overlap_eff |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.00 | 0.00 | 26.69 | 73.31 | 0.00 | 0.734 | 0.613 | 0.080 |
| HBM_only_GPU | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.717 | 0.410 | 0.087 |
| MoSKA_only | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.735 | 0.543 | 0.069 |
| H3_only | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.720 | 0.482 | 0.078 |
| Apple_like_UMA | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.701 | 0.382 | 0.069 |
| vLLM_like | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.737 | 0.552 | 0.072 |
| FlashAttn_like | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.732 | 0.522 | 0.063 |
| TensorRTLLM_like | 0.00 | 0.00 | 0.00 | 100.00 | 0.00 | 0.739 | 0.572 | 0.072 |

## Shared-KV Reuse / Prefetch Evidence
| Baseline | shared_kv_reuse_ratio | batch_gain | prefetch_coverage | lhb_hit | thermal_peak_C | model_error_% |
|---|---:|---:|---:|---:|---:|---:|
| AFO_full | 0.642 | 2.792 | 0.970 | 0.714 | 112.42 | 14.45 |
| HBM_only_GPU | 0.177 | 1.215 | 0.721 | 0.000 | 107.96 | 29.06 |
| MoSKA_only | 0.586 | 2.413 | 0.833 | 0.714 | 110.78 | 26.47 |
| H3_only | 0.266 | 1.362 | 0.777 | 0.631 | 109.37 | 27.99 |
| Apple_like_UMA | 0.141 | 1.165 | 0.684 | 0.000 | 107.03 | 29.91 |
| vLLM_like | 0.397 | 1.658 | 0.910 | 0.714 | 111.01 | 26.34 |
| FlashAttn_like | 0.106 | 1.119 | 0.814 | 0.000 | 110.31 | 26.79 |
| TensorRTLLM_like | 0.339 | 1.514 | 0.930 | 0.714 | 111.48 | 24.72 |

Assumption note: `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like` are policy-level synthetic baselines in this simulator, not measured vendor kernels.
Seed count per baseline: 5