# Tail Latency Root-Cause Analysis

## Worst-case Scenario
- scenario: `worst_case_tail`
- p99 latency: `1579.098 ms`
- p99/p50 tail ratio: `1.148`
- bridge util: `0.064`
- tsv util: `0.053`
- burst event ratio: `0.249`
- hbf_miss_penalty_ms_total: `1864.500`
- bridge_contention_ms_total: `133816.345`
- tsv_contention_ms_total: `45623.219`

## Dominant Tail Causes
- central TSV neck (50.49%)
- bridge saturation (49.51%)
- HBF miss penalty exposure (0.00%)

## Nominal vs Worst-case Delta
- p99 delta: `+1330.709 ms`
- bridge contention delta: `+130174.152 ms`
- tsv contention delta: `+42837.532 ms`
- hbf miss penalty delta: `+1736.895 ms`
- overlap efficiency delta: `-0.0208`
- lhb hit delta: `-0.2265`

## Interpretation
Tail explosion is mainly associated with bridge queue growth and miss-penalty amplification under burst pressure.
This supports the review claim that multi-tenant burst contention, not mean latency, is the key risk surface.