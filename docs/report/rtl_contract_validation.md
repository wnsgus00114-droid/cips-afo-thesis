# RTL Contract Validation (DMA + Prefetch + Address Decoder)

## Goal
실험 피드백에서 지적된 bridge contention / tail latency 해석을 RTL 관점의 contract-level TB로 연결 검증한다.

## Scope
검증 블록:
- `rtl/src/afo_addr_decoder.sv`
- `rtl/src/afo_prefetch_engine.sv`
- `rtl/src/afo_dma_engine.sv`
- `rtl/src/afo_top.sv`
- `rtl/tb/tb_afo_top.sv`

핵심 확장:
1. DMA dequeue backpressure 입력(`i_dma_ready`) 추가
2. DMA queue peak counter(`o_dbg_qmax`) 추가
3. TB 시나리오 확장
- Nominal path
- Invalid-address block
- Saturation proxy(bridge contention 근사)

## How to Run
```bash
make -C rtl contract_tb
```

생성 산출물:
- `results/rtl/tb_afo_top_run.log`
- `results/rtl/rtl_contract_tb_summary.md`
- `results/waves/tb_afo_top.vcd`

## Assertion Matrix
| Scenario | Assertion Intention |
|---|---|
| Nominal | valid base에서 descriptor 2개(weight->kv) 순서 보장, queue shallow (`o_dma_qmax<=2`) |
| Invalid Address | decode fault 시 prefetch enqueue 차단 |
| Saturation Proxy | `i_dma_ready=0` 구간에서 queue buildup, ready 복구 후 drain 완료 및 drain tail 확인 |

## Latest Results
`results/rtl/rtl_contract_tb_summary.md` 기준:
- lint warning: 0
- sim: PASS
- saturation peak qdepth: 12
- saturation drain cycles: 13

## Link to Experiment Analysis
- RTL saturation proxy는 `results/summary/tail_latency_root_cause.md`의 bridge contention 증가와 동일한 방향성(큐 체류 증가)을 보인다.
- `results/tables/key_sensitivity_panels.md`의 bridge BW vs p99 음의 상관과 정합적이다.

## Limitation
- 본 TB는 contract-level 검증이며, HBM/HBF 실제 DRAM/NAND cycle timing을 모델링하지 않는다.
- 즉, silicon signoff가 아니라 정책/인터페이스 정합성 검증 용도다.
