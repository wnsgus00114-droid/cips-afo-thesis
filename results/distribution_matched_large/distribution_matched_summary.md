# Distribution-Matched Synthetic Experiment Summary

Paper-anchored profiles are mapped into synthetic input knobs (context length, decode steps, arrival-driven burstiness).

| Profile | Baseline | Tok/s (wavg) | p99 mpath (ms, wavg) | Stall (wavg) | Bridge util (wavg) | Inter-tier util (wavg) | Bridge share % | Inter-tier share % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sharegpt_vllm_fig11 | AFO_Proposed | 532.29 | 249.524863 | 0.9788 | 0.2398 | 0.3003 | 45.77 | 27.51 |
| sharegpt_vllm_fig11 | HBM_GPU_Baseline | 497.31 | 268.830467 | 0.9763 | 0.2258 | 0.2827 | 46.56 | 27.99 |
| sharegpt_vllm_fig11 | H3_Hybrid_Memory_Baseline | 510.09 | 260.780841 | 0.9752 | 0.2313 | 0.2897 | 44.64 | 26.83 |
| sharegpt_distserve_fig7 | AFO_Proposed | 529.50 | 251.061060 | 0.9794 | 0.2387 | 0.2989 | 45.87 | 27.48 |
| sharegpt_distserve_fig7 | HBM_GPU_Baseline | 493.83 | 271.640952 | 0.9757 | 0.2246 | 0.2812 | 46.61 | 27.93 |
| sharegpt_distserve_fig7 | H3_Hybrid_Memory_Baseline | 507.46 | 262.317055 | 0.9765 | 0.2305 | 0.2886 | 44.76 | 26.82 |
