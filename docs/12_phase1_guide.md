# 1차 구현 설명서

## 목적

이 문서는 현재 저장소의 1차 구현이 무엇을 하는지, 왜 이렇게 구성했는지, 다음에 무엇을 바꾸면 되는지를 설명하기 위한 문서다.

1차 구현의 목표는 실시간 서비스가 아니라, 고정된 데이터를 바탕으로 수요 예측과 배차 로직을 오프라인으로 검증하는 것이다.

## 현재 1차 구현 범위

- 고정된 CSV 데이터를 입력으로 사용한다.
- 시간 피처와 시계열 피처를 생성한다.
- baseline 모델로 수요 예측 구조를 검증한다.
- 수요/공급 비율 기반의 rule-based 배차 로직을 계산한다.
- 시간대별 수요 그래프를 출력한다.

즉, 현재 단계는 “실시간 시스템”이 아니라 “알고리즘 검증용 오프라인 프로토타입”이다.

## 실행 흐름

전체 실행 순서는 `scripts/run_pipeline.sh`에 들어 있다.

### 1. 전처리

파일:
- `src/preprocessing/build_features.py`

입력:
- `data/sample_taxi_calls.csv`

처리:
- `pickup_datetime`에서 `hour`, `day_of_week`를 만든다.
- 지역별 이전 호출 수 `lag_1`을 만든다.
- 최근 3개 시점 평균인 `rolling_mean_3`을 만든다.

출력:
- `outputs/processed_taxi_calls.csv`

### 2. baseline 예측

파일:
- `src/prediction/train_baseline.py`

처리:
- 전처리된 데이터를 읽는다.
- `call_count`를 타깃으로 잡는다.
- 나머지 피처를 입력으로 사용한다.
- `RandomForestRegressor`로 baseline 모델을 학습한다.
- `RMSE`, `MAE`를 출력한다.

의미:
- 지금은 “예측이 아주 잘 되느냐”보다 “예측 파이프라인이 돌아가느냐”를 검증하는 단계다.

### 3. 배차 로직

파일:
- `src/dispatch/rule_based_dispatch.py`

핵심 수식:

`imbalance_score = demand / max(supply, 1)`

의미:
- 수요가 크고 공급이 적을수록 점수가 커진다.
- 점수가 높은 지역을 우선 배차 대상으로 본다.

추가 로직:
- 점수 구간에 따라 `incentive_multiplier`를 계산한다.

### 4. 시각화

파일:
- `src/visualization/plot_demand.py`

처리:
- `hour` 기준으로 전체 수요를 합산한다.
- 시간대별 총 호출 수를 막대그래프로 저장한다.

출력:
- `outputs/hourly_demand.png`

## 현재 그래프의 의미

`hourly_demand.png`는 시간대별 총 호출 수를 보여주는 그래프다.

현재 샘플 데이터 기준:
- 18시 총 수요: 70
- 19시 총 수요: 118

즉, 19시대 수요가 더 높기 때문에 배차를 더 집중하는 방향이 자연스럽다는 것을 보여준다.

## 이 구조를 만든 이유

처음부터 실시간 데이터를 붙이거나 Unity와 바로 연동하면 복잡도가 너무 커진다.
그래서 먼저 아래 4가지를 분리해서 검증하도록 설계했다.

- 데이터 전처리
- 예측 모델
- 배차 로직
- 시각화

이렇게 하면 각 단계가 실패하더라도 어디가 문제인지 빨리 알 수 있다.

## 앞으로 네가 보면 좋은 파일

- `configs/base.yaml`
- `src/preprocessing/build_features.py`
- `src/prediction/train_baseline.py`
- `src/dispatch/rule_based_dispatch.py`
- `src/visualization/plot_demand.py`

이 5개만 이해하면 현재 1차 구현 흐름은 거의 다 이해한 것이다.

## 다음에 해볼 수정

### 쉬운 수정

- 샘플 CSV 값 바꾸기
- 지역 수 늘리기
- 배차 점수 임계값 바꾸기
- 그래프를 지역별로 나눠 그리기

### 다음 단계

- 공개 택시 데이터셋으로 입력 교체
- 시간 단위를 5분 또는 10분으로 고정
- baseline 외 다른 모델 추가
- 외부 변수(날씨, 이벤트) 추가
- Unity 결과와 연결

## 2차 확장 방향

2차에서는 다음을 목표로 할 수 있다.

- 실시간 또는 준실시간 데이터 반영
- 교통상황, 날씨, 이벤트 등 외부 데이터 반영
- 현재 빈 차량 수와 차량 위치 반영
- 더 동적인 재배치 의사결정

즉,
- 1차는 오프라인 검증
- 2차는 동적 확장

이라는 구조로 이해하면 된다.
