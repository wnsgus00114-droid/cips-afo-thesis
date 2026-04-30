# Reviewer Feedback Closure Matrix

## Scope
This matrix maps the latest reviewer comments to concrete code/data/document artifacts.

## A. Experiment Feedback Closure
| Feedback | Action | Artifact |
|---|---|---|
| Simulator trust 부족 | sanity anchor + trend + model-error checks 자동화 | `experiments/scripts/sanity_validate.py`, `results/tables/simulator_sanity_checks.md` |
| Baseline 공정성 부족 | fairness-locked fields 강제 + 공개 표 생성 | `experiments/scripts/gen_baselines.py`, `results/tables/baseline_fairness.md` |
| 원인-결과 연결 약함 | causal chain 분석 자동 생성 | `experiments/scripts/analyze_results.py`, `results/summary/causal_chain_analysis.md` |
| tail latency 해석 부족 | worst-case root-cause 리포트 생성 | `results/summary/tail_latency_root_cause.md` |
| 핵심 sensitivity 부족 | 3개 핵심 panel 지표화 | `results/tables/key_sensitivity_panels.md` + plot links |
| thermal 설명 약함 | thermal-impact 리포트 분리 | `results/summary/thermal_impact_analysis.md` |
| parameter disclosure 부족 | 재현 파라미터 공개 | `results/tables/reproducibility_params.md` |
| 하드웨어 실현 가능성 증빙 부족 | DMA+Prefetch+Decoder assertion TB 확장 및 Verilator 파형 검증 | `rtl/tb/tb_afo_top.sv`, `results/rtl/rtl_contract_tb_summary.md`, `docs/report/rtl_contract_validation.md` |

## B. Paper/Story Feedback Closure
| Feedback | Action | Artifact |
|---|---|---|
| contribution 불명확 | one-line thesis를 중심 문장으로 반복 배치 | `paper/afo_paper_draft.md`, `thesis/docs/thesis_manuscript.md` |
| novelty 애매 | “not composition, but enforced mechanism” 구조 명시 | same as above |
| related work gap 약함 | 기존 시스템의 실패 모드(멀티테넌트 burst, tier enforcement 부재) 명시 | same as above |
| 수식-결과 연결 약함 | equation-to-metric binding + result link 추가 | same as above + `results/summary/causal_chain_analysis.md` |
| limitation 방어 약함 | not silicon-ready / not production-grade / policy-level validation 명시 | same as above |

## C. Current Reproduction Commands
```bash
python3 experiments/scripts/run_sweeps.py --config experiments/configs/base.json --num-tokens 256 --seeds 11,23,37
python3 experiments/scripts/gen_baselines.py
python3 experiments/scripts/plot_results.py
python3 experiments/scripts/sanity_validate.py
python3 experiments/scripts/analyze_results.py
python3 experiments/scripts/make_summary.py
make -C rtl contract_tb
```

## D. Status
- Experimental closure: complete in repository artifacts.
- Paper revision closure: reflected in draft/manuscript.
- Remaining gap (explicitly acknowledged): silicon-level physical validation.
