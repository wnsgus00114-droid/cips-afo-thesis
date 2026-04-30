# A.F.O Thesis Package

이 폴더는 A.F.O 칩셋의 논문 제출/오픈소스 공개를 동시에 위한 완성형 패키지다.

아키텍처 레이어 규약:
- Layer 1 (Top): Compute die
- Layer 2 (Bottom): Inner HBM rectangular ring + Outer HBF rectangular ring

## 구성
- `docs/` : 읽기 쉬운 문서형(설명/도해/3D 링크)
- `scripts/` : 3D 모델/피겨 생성 스크립트
- `../paper/afo_paper_draft.md` : 현재 공개 저장소용 연구 원고 초안

## 핵심 문서
1. [Thesis Manuscript](./docs/thesis_manuscript.md)
2. [Figure Atlas](./docs/figure_atlas.md)
3. [Performance Model](./docs/performance_model.md)
4. [3D Models](./docs/assets/models/README.md)
5. [RTL Contract Validation](../docs/report/rtl_contract_validation.md)

## 3D 모델 (GitHub 회전 보기)
GitHub에서 아래 파일을 클릭하면 3D 뷰어에서 마우스로 회전 가능:
- `docs/assets/models/afo_chip_package_3d.obj`
- `docs/assets/models/afo_hardware_system_3d.obj`
- (대안) `.stl` 파일도 포함

## 로컬 인터랙티브 뷰어
```bash
cd thesis/docs/viewer
python3 -m http.server 18080
# http://localhost:18080 접속
```

## 논문 원고
- 공개 원고(Markdown): `../paper/afo_paper_draft.md`
- 상세 본문(문서형): `docs/thesis_manuscript.md`

## 피겨/모델 재생성
```bash
python3 thesis/scripts/generate_3d_models.py
.venv/bin/python thesis/scripts/generate_figures.py
```
