# 로컬 데이터셋 및 1차 산출물

## 로컬 데이터셋

1차 구현은 `data/local_taxi_calls.csv`를 기준으로 동작한다.

이 데이터셋은 다음 목적을 가진 synthetic local dataset이다.

- 전체 파이프라인이 로컬에서 바로 실행되도록 하기 위함
- 지역별 수요 편차를 일부러 만들기 위함
- 출퇴근/저녁 피크 시간대가 보이도록 하기 위함
- 배차 우선순위 계산이 눈에 띄게 나오도록 하기 위함

현재 구성:
- 기간: 2026-03-17 ~ 2026-03-23
- 단위: 1시간
- 지역: A, B, C, D

## 1차 산출물

파이프라인 실행 후 아래 결과가 생성된다.

- `outputs/processed_taxi_calls.csv`
- `outputs/model_metrics.json`
- `outputs/predictions.csv`
- `outputs/dispatch_recommendations.csv`
- `outputs/hourly_demand.png`
- `outputs/zone_hour_heatmap.png`
- `outputs/zone_demand_summary.csv`
- `outputs/hourly_demand_summary.csv`

## 해석 포인트

- 어떤 지역이 가장 수요가 높은가
- 어떤 시간대에 전체 수요가 집중되는가
- 최신 시점 기준 어느 지역에 우선 배차해야 하는가
- baseline 예측이 구조적으로 동작하는가

## 다음 단계

- local dataset을 공개 데이터셋으로 교체
- 시간 단위를 5분 또는 10분으로 세분화
- 외부 변수 추가
- Unity 연동을 위한 지역/오브젝트 매핑 설계
