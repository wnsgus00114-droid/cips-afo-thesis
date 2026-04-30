# A.F.O (All For One)

유한 대역폭 환경에서 장문맥 LLM 추론의 병목을 분석하기 위한 아키텍처/패키징 중심 연구 저장소입니다.

## 핵심 요약
- A.F.O는 단순 3D 적층 가정이 아니라, `Active Base Die + 중앙 3D TSV + 외곽 2.5D 메모리 링` 토폴로지를 명시적으로 모델링합니다.
- 실험은 다중 시드, 스트레스 시나리오, 공정성(Fairness) 계약, sanity 검증까지 포함합니다.
- 최신 재실험(본 저장소 현재 결과)에서 TSV neck 대역폭이 tail latency를 강하게 지배함을 확인했습니다.

## 1) 물리 구현 가능성(Feasibility) 정의

본 리포지토리는 아래 패키징 계약을 고정 가정으로 사용합니다.

- `Top / Layer1`: 중앙 compute chiplet (3D hybrid bonding)
- `Bottom / Layer2`: Active Base Die (logic interposer)
- Layer2 periphery: inner HBM ring + outer HBF ring (2.5D micro-bump 실장)
- 핵심 경로: `ring ingress -> base-die lateral route -> central TSV neck -> SRAM staging`

이 구조는 최신 3D/3.5D 통합 패키징 흐름(예: SoIC/Foveros 계열)에서 논의되는 병목 특성과 정합되며, 본 연구의 소프트웨어 스케줄링 필요성을 하드웨어 병목 관점에서 정당화합니다.

## 2) 최신 실험 헤드라인 (재실행 결과)

- Baseline 최고 처리량: `AFO_full = 5.73 tok/s`
- Baseline 최소 p99: `AFO_full = 178.058 ms`
- HBM-only 대비: `AFO_full`가 처리량/꼬리 지연 모두 우세
  - `5.73 vs 5.63 tok/s`, `178.058 vs 181.122 ms`
- 최악 스트레스 tail: `worst_case_tail p99 = 893.099 ms`
- 최악 bridge contention: `133816.345 ms`
- TSV neck 압박 시나리오: `nominal p99 179.476 ms -> tsv_neck_pressure p99 618.234 ms`
- Simulator sanity: `9 PASS / 0 FAIL`

주요 민감도(Reviewer critical):
- `corr(bridge_bw_gbs, latency_p99_ms) = -0.979`
- `corr(tsv_uplink_bw_gbs, latency_p99_ms) = -0.975`
- `corr(prefetch_accuracy, overlap_efficiency) = 1.000`

## 3) 빠른 재현

### 환경 준비
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 전체 실험 파이프라인 (권장)
```bash
bash scripts/run_all.sh
```

### 수동 단계 실행
```bash
python3 experiments/scripts/run_sweeps.py --config experiments/configs/base.json --num-tokens 256 --seeds 11,23,37
python3 experiments/scripts/gen_baselines.py
python3 experiments/scripts/plot_results.py
python3 experiments/scripts/sanity_validate.py
python3 experiments/scripts/analyze_results.py
python3 experiments/scripts/make_summary.py
```

### 스모크/CI 체크
```bash
bash scripts/check_all.sh
```

## 4) 핵심 결과 아티팩트

- 종합 요약: [results/summary/simulation_summary.md](results/summary/simulation_summary.md)
- Baseline 비교: [results/tables/baseline_comparison.md](results/tables/baseline_comparison.md)
- Baseline 공정성: [results/tables/baseline_fairness.md](results/tables/baseline_fairness.md)
- Sweep 요약: [results/tables/sweep_summary.md](results/tables/sweep_summary.md)
- Sanity 검증: [results/tables/simulator_sanity_checks.md](results/tables/simulator_sanity_checks.md)
- 인과 분석: [results/summary/causal_chain_analysis.md](results/summary/causal_chain_analysis.md)
- Tail 원인 분석: [results/summary/tail_latency_root_cause.md](results/summary/tail_latency_root_cause.md)
- Thermal 영향 분석: [results/summary/thermal_impact_analysis.md](results/summary/thermal_impact_analysis.md)
- 민감도 패널: [results/tables/key_sensitivity_panels.md](results/tables/key_sensitivity_panels.md)

## 5) Baseline Fairness 정책

모든 baseline은 아래를 동일하게 고정합니다.

- workload: batch/context/chunk
- capacity: HBM/HBF/SRAM
- link: HBM BW, HBF BW, Bridge BW, HBF latency
- package-neck: TSV BW, Base-die BW, TSV util cap

변동 허용 항목(정책/알고리즘 knob):
- shared KV ratio
- HBF weight fraction
- prefetch accuracy
- routing diversity
- LHB/prefetch depth
- matrix efficiency

## 6) 저장소 맵

- 아키텍처 문서: [docs/architecture/afo_system_overview.md](docs/architecture/afo_system_overview.md)
- 구현 문서: [docs/implementation/dataflow.md](docs/implementation/dataflow.md), [docs/implementation/runtime_software_design.md](docs/implementation/runtime_software_design.md)
- 실험 스크립트: [experiments/scripts](experiments/scripts)
- 시뮬레이터: [sim/afo_simulator.py](sim/afo_simulator.py)
- 결과 폴더: [results](results)

## 7) 보안/공개 정책

- `result_paper/`는 로컬 전용 산출물이며, Git에 포함하면 안 됩니다.
- 본 저장소의 `.gitignore`에 `result_paper/`가 포함되어 있어야 하며, 현재도 해당 정책을 유지합니다.

## 8) 한계와 해석 범위

- `vLLM_like`, `FlashAttn_like`, `TensorRTLLM_like`는 정책 수준의 synthetic baseline입니다.
- 본 결과는 아키텍처 경향성 및 병목 인과 분석 목적이며, 실측 실리콘 수치와 동일시하면 안 됩니다.
- 하드웨어 publication 수준 claim에는 추가 RTL/FPGA/실측 검증이 필요합니다.
