# Performance Model (A.F.O)

## 1. Layer-level Latency Decomposition
\[
T^{(l)} = \max\left(T^{(l)}_{compute}, T^{(l)}_{hbm}, T^{(l)}_{hbf}+\Delta^{(l)}_{miss}, T^{(l)}_{bridge}\right) + T^{(l)}_{router}
\]

where
\[
T^{(l)}_{hbm}=\frac{B^{(l)}_{hbm}}{BW_{hbm}},\;
T^{(l)}_{hbf}=\frac{B^{(l)}_{hbf}}{BW_{hbf}},\;
T^{(l)}_{bridge}=\frac{B^{(l)}_{bridge}}{BW_{bridge}}
\]

\[
\Delta^{(l)}_{miss}=(1-p^{(l)}_{pref})\left(L_{hbf}+\alpha\cdot T^{(l)}_{hbf}\right)
\]

Layer-2 ring topology conformance:
\[
R_{topo}=0.5\cdot(C_{hbm\_ring}+C_{hbf\_outer\_ring})
\]
\[
T^{(l)}_{bridge,eff}=T^{(l)}_{bridge}\cdot(1-\gamma\cdot\max(0,R_{topo}-0.8))
\]

## 2. Shared-KV Batching Gain
shared path의 유효 연산 집약도 증가를 다음으로 근사한다.
\[
G_{batch}=\frac{\sum_r n_r}{\left|\bigcup_r \mathcal{C}_r\right|}
\]

- \(n_r\): 요청 \(r\)의 selected chunk 수
- \(\mathcal{C}_r\): 요청 \(r\)의 chunk set

\(G_{batch}\)가 클수록 동일 fetched bytes 대비 FLOP 재사용이 증가한다.

## 3. KV Chunk Size Tradeoff
chunk size \(S_c\)에 대해:
\[
\mathrm{Overfetch}(S_c) \propto S_c - S_{useful}
\]
\[
\mathrm{MetaOverhead}(S_c) \propto \frac{1}{S_c}
\]

따라서 최적 \(S_c\)는 아래 목적함수 최소점 근방에서 선택한다.
\[
J(S_c)=\lambda_1\mathrm{Overfetch}(S_c)+\lambda_2\mathrm{MetaOverhead}(S_c)+\lambda_3\mathrm{SRAMPressure}(S_c)
\]

## 4. Power Model
\[
P_{total}=P_{compute}^{peak}U_c + P_{hbm}^{peak}U_h + P_{hbf}^{peak}U_f + P_{bridge}^{peak}U_b + (P_{sram}^{idle}+\beta BW_{sram})
\]

\[
TPW=\frac{TPS}{P_{total}}
\]

## 5. Memory Bottleneck Ratio
\[
MB\% = 100\times\frac{\sum_l (T_l-T_{compute,l})_+}{\sum_l T_l}
\]
