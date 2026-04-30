# A.F.O Thesis Documentation

## 문서 개요
이 문서는 A.F.O(All For One) 3D AI 칩셋의 아키텍처, 수학적 모델, 구현 로드맵, 3D 시각화, 실험 설계를 논문 수준으로 통합한 패키지다.

레이어 규약:
- Layer 1 (Top): Compute
- Layer 2 (Bottom): Inner HBM rectangular ring + Outer HBF rectangular ring

핵심 산출물:
1. 논문형 본문: [A.F.O Thesis Manuscript](./thesis_manuscript.md)
2. 연구 원고 초안: [`../../paper/afo_paper_draft.md`](../../paper/afo_paper_draft.md)
3. 3D 모델(깃허브 회전 가능): [3D Models README](./assets/models/README.md)
4. 피겨 설명: [Figure Atlas](./figure_atlas.md)

## 빠른 시작
1. 3D 모델 확인
- [afo_chip_package_3d.obj](./assets/models/afo_chip_package_3d.obj)
- [afo_hardware_system_3d.obj](./assets/models/afo_hardware_system_3d.obj)

2. 논문 본문 읽기
- [thesis_manuscript.md](./thesis_manuscript.md)

3. 수식/성능 모델
- [performance_model.md](./performance_model.md)
4. 시각화 가이드
- [visualization_guide.md](./visualization_guide.md)
5. 참고문헌 맵
- [references.md](./references.md)

4. 재생성 스크립트
- `thesis/scripts/generate_3d_models.py`
- `thesis/scripts/generate_figures.py`

## 생성된 피겨
- `fig_chip_3d_annotated.{png,svg}`
- `fig_system_3d_annotated.{png,svg}`
- `fig_dataflow_pipeline.{png,svg}`

각 피겨는 칩 내부 블록/메모리 계층/시스템 부품의 의미를 레이어 단위로 설명하도록 구성되어 있다.
