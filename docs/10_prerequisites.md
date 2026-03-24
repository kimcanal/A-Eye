# Prerequisites

## 공통 개발 환경
- Python 3.11+
- Git / GitHub
- VS Code 또는 Cursor
- Jupyter Notebook 또는 Google Colab

## Python 패키지
- numpy
- pandas
- scikit-learn
- matplotlib
- seaborn
- pyyaml
- jupyter

설치 예시:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Module 1: Unity / Digital Twin
현재 제공된 에셋은 Unity 기반 `.unitypackage` 형식이다. 따라서 Module 1은 다음 전제를 가진다.

- Unity Hub 설치
- 권장: Unity 2022 LTS 계열
- 새 3D Core 프로젝트 생성
- 에셋 import 후 최소 도시 씬 구성

## 확인한 에셋 구성
- map: `street_main.unitypackage`
- object: `car_taxi.unitypackage`, `obs_car_1.unitypackage`, `obs_car_2.unitypackage`, `robot_spot.unitypackage` 등
- animation: `carwheel_move.unitypackage`, `kickboard_fall.unitypackage` 등
- effect: `MapSetting_1.unitypackage` 등
- guide: `Guide_unity.pdf`, `Guide_asset.pdf`, `Guide_build.pdf`

## Module 2~4 개발 전제
- 데이터는 공개 택시 데이터셋 또는 샘플 데이터 사용
- 지역 단위는 우선 `zone_id` 또는 단순 grid로 시작
- 모델은 baseline부터 구현
- 배차 로직은 rule-based로 먼저 구현
