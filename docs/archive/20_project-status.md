# Project Status

## 한 줄 요약
현재 프로젝트는 **로컬 더미데이터와 서울 공공데이터 기준으로 `예측 -> 배차 -> 비교 평가 -> Unity 시각화`까지 한 번 이어지는 1차 프로토타입** 상태입니다.

## 지금 실제로 되는 것

### 1. 로컬 더미데이터 파이프라인
- 가짜 택시 수요 데이터를 생성합니다.
- 전처리와 시계열 피처 생성을 수행합니다.
- baseline 예측을 실행합니다.
- 예측 결과 기반으로 배차 순위를 계산합니다.
- 배차 전/후 비교 그래프와 평가 JSON을 생성합니다.

실행:
```bash
cd <repo-root>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_pipeline.sh
```

대표 산출물:
- `outputs/model_metrics.json`
- `outputs/predictions.csv`
- `outputs/dispatch_recommendations.csv`
- `outputs/dispatch_before_after.png`

### 2. 서울 공공데이터 파이프라인
- 서울 Open API에서 행정동별 대중교통 승차 데이터를 가져옵니다.
- long format 수요 데이터로 변환합니다.
- baseline 예측과 배차 로직을 실행합니다.
- public dataset 기준 결과물을 저장합니다.

실행:
```bash
cd <repo-root>
source .venv/bin/activate
bash scripts/run_public_pipeline.sh
```

대표 산출물:
- `outputs/seoul_public/model_metrics.json`
- `outputs/seoul_public/predictions.csv`
- `outputs/seoul_public/dispatch_recommendations.csv`
- `outputs/seoul_public/dispatch_before_after.png`

### 3. Module 1 Unity 브리지
- Python 배차 결과를 `unity_scenario.json`으로 내보냅니다.
- Unity Editor 스크립트가 이 JSON을 읽어 택시와 장애물을 씬에 배치합니다.
- Unity 캡처와 오버레이, 발표용 보드 이미지를 자동 생성합니다.

실행:
```bash
cd <repo-root>
bash scripts/run_unity_module1_capture.sh
```

대표 산출물:
- `outputs/module1/unity_module1_view.png`
- `outputs/module1/unity_module1_annotated.png`
- `outputs/module1/unity_module1_presentation.png`
- `outputs/module1/unity_scenario.json`

## 모듈별 현재 상태

| 모듈 | 상태 | 설명 |
| --- | --- | --- |
| Module 1 | 부분 완료 | Unity 씬 생성과 캡처는 되지만, 정확한 GIS/차선 정합은 아직 아님 |
| Module 2 | 완료에 가까움 | 전처리, 시간 피처, lag, rolling mean, 공공데이터 변환까지 있음 |
| Module 3 | 1차 완료 | RandomForest baseline과 평가 지표 생성 가능 |
| Module 4 | 1차 완료 | 예측값 기반 배차 추천과 배차 전/후 비교 가능 |

## 아직 남아 있는 것

### 반드시 남아 있는 것
- 외부 feature 추가
  - 날씨
  - 공휴일
  - 교통속도
- 모델 고도화
  - LSTM
  - CNN-LSTM 또는 ConvLSTM 검토
- Module 1 정교화
  - 택시를 실제 차선에 더 자연스럽게 배치
  - before/after 장면을 더 명확히 분리

### 아직 안 한 것
- SUMO 연동
- 실시간 스트리밍 구조
- 실제 택시 공급 데이터 기반 운영 검증

## 팀원에게 설명할 때 쓰는 문장
- 우리는 현재 오프라인 기준으로 수요 예측, 배차 추천, 배차 전후 비교, Unity 시각화까지 연결되는 1차 프로토타입을 만든 상태다.
- 지금 단계에서는 구조와 연결을 검증한 것이고, 다음 단계는 외부 feature 추가와 모델 고도화다.
- Unity는 실제 결과를 보여주는 Module 1 브리지까지 확인되었고, SUMO는 아직 구현하지 않았다.

## 다음 우선순위
1. 모델 입력에 외부 feature를 붙인다.
2. baseline과 LSTM 계열 모델을 비교한다.
3. Unity 화면을 before/after 중심으로 더 정리한다.
