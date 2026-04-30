# Thermal/Process Impact Analysis

## Thermal Coupling Evidence
- nominal thermal_peak: `110.78 C`
- thermal_hot thermal_peak: `125.00 C`
- worst_case_tail thermal_peak: `125.00 C`
- nominal throttling_ratio: `1.000`
- thermal_hot throttling_ratio: `1.000`
- worst_case_tail throttling_ratio: `1.000`

## Performance Impact
- nominal throughput: `4.11 tok/s`
- thermal_hot throughput: `2.29 tok/s`
- worst_case_tail throughput: `0.73 tok/s`
- nominal p99: `248.389 ms`
- thermal_hot p99: `460.923 ms`
- worst_case_tail p99: `1579.098 ms`

## Interpretation
Thermal rise increases throttling ratio, which lengthens compute time and amplifies queue residency under burst traffic.
Therefore thermal/process variability is not cosmetic; it shifts the bottleneck boundary in 3D-stacked operation.

## Limitation Note
This is a policy-level thermal RC model, not a package-accurate CFD/finite-element model.