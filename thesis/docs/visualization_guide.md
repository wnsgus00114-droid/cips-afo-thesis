# Visualization Guide (Detailed)

## 목표
타인이 처음 봐도 A.F.O의 구조를 즉시 이해할 수 있도록,
1. 칩 내부 블록 관계
2. 메모리 계층 데이터 흐름
3. 시스템 레벨 전력/열/인터커넥트 맥락
을 모두 시각적으로 제공한다.

## 산출물 종류
1. 설명형 피겨 (PNG/SVG)
- `fig_chip_3d_annotated`
- `fig_system_3d_annotated`
- `fig_dataflow_pipeline`

2. 회전형 3D 모델 (OBJ/STL)
- chip package model
- full system model

3. 웹 인터랙티브 뷰어 (Three.js)
- `docs/viewer/index.html`

## 칩 3D 피겨 읽는 순서
1. Substrate와 compute die 레이어 위치 확인
2. Layer-2 inner HBM ring / outer HBF ring의 사각형 감싸기 배치 확인
3. bridge slab과 data path 화살표 확인
4. CPU/GPU/NPU/SRAM zone 색상으로 기능 파악
5. LHB 주석으로 prefetch miss 완화 메커니즘 이해

## 시스템 3D 피겨 읽는 순서
1. 중앙 chip package
2. 상단 cooling (heatsink/fan)
3. 측면 VRM phase
4. 외곽 CXL/PCIe 슬롯
5. host memory/PSU 영역

## 커뮤니케이션 원칙
- 색상은 기능군 단위로 고정
- 모든 핵심 블록에 텍스트 callout 제공
- 데이터 경로는 화살표 방향으로만 표현
- 축약어는 첫 등장 시 풀네임 병기

## 재생성
```bash
python3 thesis/scripts/generate_3d_models.py
.venv/bin/python thesis/scripts/generate_figures.py
```
